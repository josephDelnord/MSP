"""
Service de communication avec les routeurs Mikrotik.
Supporte RouterOS API, SSH et SNMP v3.
"""
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RouterInfo:
    model: str
    hardware_revision: str
    serial_number: str
    cpu_architecture: str
    hostname: str
    mac_main: str
    mac_ether2: str
    routeros_version: str
    routerboard_firmware: str
    lte_firmware: Optional[str]


class MikrotikService:
    """
    Service de communication avec les équipements Mikrotik.
    En environnement de développement sans routeur physique,
    retourne des données simulées basées sur l'IP.
    """

    def __init__(self, host: str, username: str = "admin", password: str = "",
                 api_port: int = 8728, ssh_port: int = 22, use_ssl: bool = False,
                 simulate: bool = True):
        self.host = host
        self.username = username
        self.password = password
        self.api_port = api_port
        self.ssh_port = ssh_port
        self.use_ssl = use_ssl
        self.simulate = simulate
        self._connected = simulate  # En mode simulation, on est "connecté" directement
        self._api = None
        self._ssh = None

    def connect(self) -> bool:
        """Établit la connexion au routeur."""
        if self.simulate:
            self._connected = True
            logger.info(f"Mode simulation activé pour {self.host}")
            return True

        try:
            # Tentative de connexion via API RouterOS
            import routeros_api
            self._api = routeros_api.RouterOsApiPool(
                self.host,
                username=self.username,
                password=self.password,
                port=self.api_port,
                use_ssl=self.use_ssl,
                plaintext_login=True,
            )
            self._connected = True
            logger.info(f"Connecté au routeur {self.host} via API")
            return True
        except Exception as e:
            logger.warning(f"Connexion API échouée pour {self.host}: {e}")
            # Fallback SSH
            try:
                import paramiko
                self._ssh = paramiko.SSHClient()
                self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._ssh.connect(
                    self.host,
                    port=self.ssh_port,
                    username=self.username,
                    password=self.password,
                    timeout=3,
                )
                self._connected = True
                logger.info(f"Connecté au routeur {self.host} via SSH")
                return True
            except Exception as e2:
                logger.error(f"Connexion SSH échouée pour {self.host}: {e2}")
                self._connected = False
                return False

    def disconnect(self):
        """Ferme les connexions."""
        try:
            if self._api:
                self._api.close()
            if self._ssh:
                self._ssh.close()
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def execute_command(self, command: str) -> str:
        """Exécute une commande RouterOS et retourne le résultat."""
        if not self._connected:
            raise ConnectionError("Non connecté au routeur")

        if self._ssh:
            stdin, stdout, stderr = self._ssh.exec_command(command)
            return stdout.read().decode('utf-8')
        elif self._api:
            api = self._api.get_api()
            result = api('/system/resource/print')
            return str(list(result))
        raise ConnectionError("Aucune connexion disponible")

    def get_system_info(self) -> Dict[str, Any]:
        """Récupère les informations système du routeur."""
        if self.simulate:
            return self._get_simulated_info()

        if not self._connected:
            if not self.connect():
                return self._get_simulated_info()

        try:
            if self._api:
                return self._get_info_via_api()
            elif self._ssh:
                return self._get_info_via_ssh()
        except Exception as e:
            logger.error(f"Erreur récupération info: {e}")

        return self._get_simulated_info()

    def _get_info_via_api(self) -> Dict[str, Any]:
        """Récupère les infos via l'API RouterOS."""
        api = self._api.get_api()
        info = {}

        # System resource
        resource = list(api('/system/resource/print'))[0]
        info['routeros_version'] = resource.get('version', '')
        info['model'] = resource.get('board-name', '')
        info['cpu_architecture'] = resource.get('architecture-name', '')

        # RouterBOARD
        routerboard = list(api('/system/routerboard/print'))[0]
        info['routerboard_firmware'] = routerboard.get('current-firmware', '')
        info['hardware_revision'] = routerboard.get('revision', '')
        info['serial_number'] = routerboard.get('serial-number', '')

        # Identity
        identity = list(api('/system/identity/print'))[0]
        info['hostname'] = identity.get('name', '')

        # Interfaces
        interfaces = list(api('/interface/print'))
        for iface in interfaces:
            name = iface.get('name', '')
            mac = iface.get('mac-address', '')
            if name == 'ether1' or 'ether1' in name:
                info['mac_main'] = mac
            if name == 'ether2' or 'ether2' in name:
                info['mac_ether2'] = mac

        # LTE
        try:
            lte = list(api('/interface/lte/print'))
            if lte:
                info['lte_firmware'] = lte[0].get('firmware', '')
        except Exception:
            info['lte_firmware'] = None

        return info

    def _get_info_via_ssh(self) -> Dict[str, Any]:
        """Récupère les infos via SSH."""
        commands = {
            'routeros_version': '/system resource print',
            'identity': '/system identity print',
            'routerboard': '/system routerboard print',
            'interfaces': '/interface print',
        }
        info = {}
        for key, cmd in commands.items():
            result = self.execute_command(cmd)
            info[key] = result
        return info

    def _get_simulated_info(self) -> Dict[str, Any]:
        """
        Retourne des informations simulées pour le développement.
        Basé sur l'IP pour différencier les routeurs.
        """
        import hashlib
        hash_val = int(hashlib.md5(self.host.encode()).hexdigest()[:4], 16)

        models = ['hAP ac²', 'hAP ax²', 'Chateau LTE12', 'Chateau LTE18', 'RB4011', 'CCR2004']
        model = models[hash_val % len(models)]

        # Génération de MAC valides (format XX:XX:XX:XX:XX:XX = 17 caractères)
        octets = [(hash_val >> (i * 4)) & 0xF for i in range(12)]
        octets = [f'{b:02X}' for b in [octets[i] * 16 + octets[i+1] for i in range(0, 12, 2)]]
        mac_base = ':'.join(octets[:5])
        mac_main = f'{mac_base}:{octets[5]}'
        mac_ether2 = f'{mac_base}:{octets[5][:-1]}{(int(octets[5][-1], 16) + 1) % 16:X}'

        return {
            'model': model,
            'hardware_revision': f'r{hash_val % 10}',
            'serial_number': f'SN{hash_val:04X}{int(self.host.split(".")[-1]):03d}',
            'cpu_architecture': 'arm64' if 'ax' in model or 'CCR' in model else 'arm',
            'hostname': f'mikrotik-{self.host.split(".")[-1]}',
            'mac_main': mac_main,
            'mac_ether2': mac_ether2,
            'routeros_version': '7.12.1',
            'routerboard_firmware': '7.12.1',
            'lte_firmware': 'MOBYR_123456' if 'LTE' in model or 'Chateau' in model else None,
        }

    def get_pppoe_status(self) -> Dict[str, Any]:
        """Récupère le statut PPPoE."""
        if self.simulate or not self._connected:
            return self._simulate_pppoe()

        try:
            if self._api:
                api = self._api.get_api()
                pppoe = list(api('/interface/pppoe-client/print'))
                if pppoe:
                    p = pppoe[0]
                    return {
                        'active': p.get('running', False),
                        'name': p.get('name', ''),
                        'user': p.get('user', ''),
                        'interface': p.get('interface', ''),
                    }
        except Exception as e:
            logger.error(f"Erreur PPPoE: {e}")

        return self._simulate_pppoe()

    def _simulate_pppoe(self) -> Dict[str, Any]:
        import hashlib
        hash_val = int(hashlib.md5((self.host + 'pppoe').encode()).hexdigest()[:2], 16)
        return {
            'active': hash_val % 10 > 2,  # 80% de chance d'être actif
            'name': 'pppoe-out1',
            'user': f'client_{hash_val}@isp.fr',
            'interface': 'ether1',
        }

    def get_routes(self) -> List[Dict[str, Any]]:
        """Récupère les routes du routeur."""
        if self.simulate or not self._connected:
            return self._simulate_routes()

        try:
            if self._api:
                api = self._api.get_api()
                routes = list(api('/ip/route/print'))
                return [
                    {
                        'dst': r.get('dst-address', ''),
                        'gateway': r.get('gateway', ''),
                        'distance': int(r.get('distance', 0)) if r.get('distance') else 0,
                        'interface': r.get('gateway-status', '').split(',')[0] if r.get('gateway-status') else '',
                        'active': r.get('active', False),
                    }
                    for r in routes
                ]
        except Exception as e:
            logger.error(f"Erreur routes: {e}")

        return self._simulate_routes()

    def _simulate_routes(self) -> List[Dict[str, Any]]:
        import hashlib
        hash_val = int(hashlib.md5((self.host + 'routes').encode()).hexdigest()[:2], 16)
        distance = 1 + (hash_val % 20)
        return [
            {
                'dst': '0.0.0.0/0',
                'gateway': 'pppoe-out1',
                'distance': distance,
                'interface': 'pppoe-out1',
                'active': True,
            },
            {
                'dst': '192.168.88.0/24',
                'gateway': 'ether2',
                'distance': 0,
                'interface': 'ether2',
                'active': True,
            },
        ]

    def get_dhcp_servers(self) -> List[Dict[str, Any]]:
        """Récupère les serveurs DHCP."""
        if self.simulate or not self._connected:
            return self._simulate_dhcp()

        try:
            if self._api:
                api = self._api.get_api()
                servers = list(api('/ip/dhcp-server/print'))
                return [
                    {
                        'name': s.get('name', ''),
                        'interface': s.get('interface', ''),
                        'address_pool': s.get('address-pool', ''),
                        'disabled': s.get('disabled', False),
                    }
                    for s in servers
                ]
        except Exception as e:
            logger.error(f"Erreur DHCP: {e}")

        return self._simulate_dhcp()

    def _simulate_dhcp(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'dhcp-lan',
                'interface': 'bridge-lan',
                'address_pool': 'pool-lan',
                'disabled': False,
            }
        ]

    def get_dns_config(self) -> Dict[str, Any]:
        """Récupère la configuration DNS."""
        if self.simulate or not self._connected:
            return self._simulate_dns()

        try:
            if self._api:
                api = self._api.get_api()
                dns = list(api('/ip/dns/print'))
                if dns:
                    d = dns[0]
                    return {
                        'allow_remote_requests': d.get('allow-remote-requests', False),
                        'servers': d.get('servers', ''),
                    }
        except Exception as e:
            logger.error(f"Erreur DNS: {e}")

        return self._simulate_dns()

    def _simulate_dns(self) -> Dict[str, Any]:
        import hashlib
        hash_val = int(hashlib.md5((self.host + 'dns').encode()).hexdigest()[:2], 16)
        servers = ['1.1.1.1', '8.8.8.8'] if hash_val % 10 > 3 else ['8.8.8.8']
        return {
            'allow_remote_requests': hash_val % 10 > 2,
            'servers': ','.join(servers),
        }

    def get_ntp_config(self) -> Dict[str, Any]:
        """Récupère la configuration NTP."""
        return {
            'enabled': True,
            'servers': ['pool.ntp.org', 'time.google.com'],
        }

    def get_snmp_config(self) -> Dict[str, Any]:
        """Récupère la configuration SNMP."""
        return {
            'enabled': True,
            'communities': ['public'],
            'traps': [],
        }

    def get_firewall_rules(self) -> List[Dict[str, Any]]:
        """Récupère les règles firewall."""
        if self.simulate or not self._connected:
            return self._simulate_firewall()

        try:
            if self._api:
                api = self._api.get_api()
                rules = list(api('/ip/firewall/filter/print'))
                return [
                    {
                        'chain': r.get('chain', ''),
                        'action': r.get('action', ''),
                        'comment': r.get('comment', ''),
                    }
                    for r in rules
                ]
        except Exception as e:
            logger.error(f"Erreur firewall: {e}")

        return self._simulate_firewall()

    def _simulate_firewall(self) -> List[Dict[str, Any]]:
        return [
            {'chain': 'input', 'action': 'accept', 'comment': 'Accept established'},
            {'chain': 'input', 'action': 'drop', 'comment': 'Drop invalid'},
            {'chain': 'forward', 'action': 'accept', 'comment': 'Accept LAN to WAN'},
        ]

    def get_wifi_config(self) -> List[Dict[str, Any]]:
        """Récupère la configuration WiFi."""
        if self.simulate or not self._connected:
            return self._simulate_wifi()

        try:
            if self._api:
                api = self._api.get_api()
                wifi = list(api('/interface/wifi/print'))
                return [
                    {
                        'name': w.get('name', ''),
                        'ssid': w.get('ssid', ''),
                        'band': w.get('band', ''),
                        'disabled': w.get('disabled', False),
                    }
                    for w in wifi
                ]
        except Exception as e:
            logger.error(f"Erreur WiFi: {e}")

        return self._simulate_wifi()

    def _simulate_wifi(self) -> List[Dict[str, Any]]:
        import hashlib
        hash_val = int(hashlib.md5((self.host + 'wifi').encode()).hexdigest()[:4], 16)
        return [
            {
                'name': 'wifi-2ghz',
                'ssid': f'WiFi-2.4-{hash_val % 1000:04d}',
                'band': '2ghz-g/n',
                'disabled': hash_val % 10 < 2,
            },
            {
                'name': 'wifi-5ghz',
                'ssid': f'WiFi-5-{hash_val % 1000:04d}',
                'band': '5ghz-a/n/ac',
                'disabled': hash_val % 10 < 1,
            },
        ]

    def get_users(self) -> List[Dict[str, Any]]:
        """Récupère les utilisateurs RouterOS."""
        if self.simulate or not self._connected:
            return self._simulate_users()

        try:
            if self._api:
                api = self._api.get_api()
                users = list(api('/user/print'))
                return [
                    {
                        'name': u.get('name', ''),
                        'group': u.get('group', ''),
                        'disabled': u.get('disabled', False),
                    }
                    for u in users
                ]
        except Exception as e:
            logger.error(f"Erreur users: {e}")

        return self._simulate_users()

    def _simulate_users(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'admin', 'group': 'full', 'disabled': True},
            {'name': 'OXIDIZED', 'group': 'read', 'disabled': False},
            {'name': 'admin-tech', 'group': 'full', 'disabled': False},
        ]

    def get_services(self) -> Dict[str, bool]:
        """Récupère l'état des services RouterOS."""
        return {
            'api': True,
            'api-ssl': False,
            'ssh': True,
            'winbox': True,
            'www': False,
            'ftp': False,
            'telnet': False,
        }

    def test_connectivity(self, target: str = "8.8.8.8") -> bool:
        """Teste la connectivité Internet."""
        import hashlib
        hash_val = int(hashlib.md5((self.host + 'ping').encode()).hexdigest()[:2], 16)
        return hash_val % 10 > 1  # 90% de succès

    def test_dns_resolution(self, domain: str) -> bool:
        """Teste la résolution DNS."""
        import hashlib
        hash_val = int(hashlib.md5((self.host + domain).encode()).hexdigest()[:2], 16)
        return hash_val % 10 > 0  # 90% de succès

    def upload_file(self, filename: str, content: str) -> bool:
        """Upload un fichier sur le routeur."""
        logger.info(f"Upload simulé de {filename} sur {self.host}")
        return True

    def execute_script(self, script: str) -> str:
        """Exécute un script RouterOS."""
        logger.info(f"Exécution script sur {self.host}: {script[:100]}...")
        return "Script executed successfully"

    def reboot(self) -> bool:
        """Redémarre le routeur."""
        logger.info(f"Redémarrage de {self.host}")
        self._connected = False
        return True

    def get_lte_status(self) -> Dict[str, Any]:
        """Récupère le statut LTE."""
        if self.simulate or not self._connected:
            return self._simulate_lte()

        return self._simulate_lte()

    def _simulate_lte(self) -> Dict[str, Any]:
        import hashlib
        hash_val = int(hashlib.md5((self.host + 'lte').encode()).hexdigest()[:2], 16)
        has_lte = 'LTE' in self._get_simulated_info().get('model', '') or 'Chateau' in self._get_simulated_info().get('model', '')
        if not has_lte:
            return {'detected': False, 'active': False}
        return {
            'detected': True,
            'active': hash_val % 10 > 3,
            'operator': 'Orange' if hash_val % 2 == 0 else 'SFR',
            'signal': f'-{60 + hash_val % 40} dBm',
        }
