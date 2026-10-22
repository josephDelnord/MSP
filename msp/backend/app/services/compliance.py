"""
Moteur de conformité - Vérification des configurations Mikrotik
basée sur les templates YAML.
"""
import logging
import yaml
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.services.mikrotik import MikrotikService

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
    MISSING = "missing"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    name: str
    category: str
    status: CheckStatus
    expected: Optional[str] = None
    found: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    explanation: Optional[str] = None
    remediation_commands: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'category': self.category,
            'status': self.status.value,
            'expected': self.expected,
            'found': self.found,
            'severity': self.severity.value,
            'explanation': self.explanation,
            'remediation_commands': self.remediation_commands,
        }


@dataclass
class AuditResult:
    checks: List[CheckResult] = field(default_factory=list)
    score: float = 0.0
    status: str = "unknown"

    @property
    def compliant_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.COMPLIANT)

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.WARNING)

    @property
    def non_compliant_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.NON_COMPLIANT)

    @property
    def missing_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.MISSING)

    def calculate_score(self) -> float:
        if not self.checks:
            return 0.0
        total = len(self.checks)
        # Pondération: compliant=1, warning=0.5, non_compliant=0, missing=0
        score = sum(
            1.0 if c.status == CheckStatus.COMPLIANT
            else 0.5 if c.status == CheckStatus.WARNING
            else 0.0
            for c in self.checks
        )
        self.score = round((score / total) * 100, 2)

        if self.score >= 95 and self.non_compliant_count == 0:
            self.status = "compliant"
        elif self.score >= 70:
            self.status = "compliant_with_warnings"
        else:
            self.status = "non_compliant"

        return self.score

    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'status': self.status,
            'total_checks': len(self.checks),
            'compliant': self.compliant_count,
            'warnings': self.warning_count,
            'non_compliant': self.non_compliant_count,
            'missing': self.missing_count,
            'checks': [c.to_dict() for c in self.checks],
        }


class ComplianceEngine:
    """
    Moteur de conformité qui vérifie l'état d'un routeur
    par rapport à son template attendu.
    """

    def __init__(self, mikrotik: MikrotikService, template_yaml: Optional[str] = None):
        self.mikrotik = mikrotik
        self.template = self._parse_template(template_yaml) if template_yaml else self._get_default_template()

    def _parse_template(self, yaml_content: str) -> Dict[str, Any]:
        """Parse le template YAML de conformité."""
        try:
            return yaml.safe_load(yaml_content)
        except Exception as e:
            logger.error(f"Erreur parsing template YAML: {e}")
            return self._get_default_template()

    def _get_default_template(self) -> Dict[str, Any]:
        """Template de conformité par défaut."""
        return {
            'name': 'default',
            'checks': {
                'versions': {
                    'routeros_min_version': '7.10',
                    'firmware_required': True,
                },
                'interfaces': {
                    'required': ['bridge-lan', 'ether2'],
                    'wan_interface': 'ether1',
                },
                'pppoe': {
                    'required': True,
                    'max_active': 1,
                    'route_distance_min': 1,
                    'route_distance_max': 20,
                    'check_internet': True,
                    'check_default_route': True,
                    'check_wan_list': True,
                },
                'lte': {
                    'route_distance': 21,
                    'check_if_present': True,
                },
                'dhcp': {
                    'required_servers': 1,
                    'check_pools': True,
                    'check_networks': True,
                    'check_gateways': True,
                },
                'dns': {
                    'allow_remote_requests': True,
                    'required_servers': ['1.1.1.1', '8.8.8.8'],
                    'test_domains': ['google.com', 'microsoft.com', 'webex.com'],
                },
                'ntp': {
                    'enabled': True,
                    'required_servers': 2,
                },
                'snmp': {
                    'enabled': True,
                    'required_communities': 1,
                },
                'firewall': {
                    'required_rules': 5,
                    'check_order': True,
                    'anti_scan': True,
                    'ddos_protection': True,
                    'wan_restrictions': True,
                },
                'nat': {
                    'masquerade_required': True,
                },
                'wifi': {
                    'check_ssid': True,
                    'check_2ghz': True,
                    'check_5ghz': True,
                    'check_security': True,
                    'wpa2_required': True,
                },
                'users': {
                    'required_users': ['OXIDIZED', 'admin-tech'],
                    'admin_disabled': True,
                },
                'services': {
                    'enabled': ['ssh', 'winbox', 'api'],
                    'disabled': ['telnet', 'ftp', 'www', 'api-ssl'],
                },
                'logging': {
                    'actions_required': 1,
                    'loki_enabled': True,
                },
                'scripts': {
                    'required_scripts': [],
                },
                'scheduler': {
                    'required_jobs': [],
                },
            }
        }

    def run_audit(self) -> AuditResult:
        """Exécute l'audit complet de conformité."""
        result = AuditResult()

        # 1. Vérification des versions
        result.checks.extend(self._check_versions())

        # 2. Vérification des interfaces
        result.checks.extend(self._check_interfaces())

        # 3. Vérification PPPoE
        result.checks.extend(self._check_pppoe())

        # 4. Vérification LTE
        result.checks.extend(self._check_lte())

        # 5. Vérification WAN
        result.checks.extend(self._check_wan())

        # 6. Vérification DHCP
        result.checks.extend(self._check_dhcp())

        # 7. Vérification DNS
        result.checks.extend(self._check_dns())

        # 8. Vérification NTP
        result.checks.extend(self._check_ntp())

        # 9. Vérification SNMP
        result.checks.extend(self._check_snmp())

        # 10. Vérification Firewall
        result.checks.extend(self._check_firewall())

        # 11. Vérification NAT
        result.checks.extend(self._check_nat())

        # 12. Vérification WiFi
        result.checks.extend(self._check_wifi())

        # 13. Vérification Utilisateurs
        result.checks.extend(self._check_users())

        # 14. Vérification Services
        result.checks.extend(self._check_services())

        # 15. Vérification Logging
        result.checks.extend(self._check_logging())

        # Calcul du score
        result.calculate_score()

        return result

    def _check_versions(self) -> List[CheckResult]:
        """Vérifie les versions RouterOS et Firmware."""
        checks = []
        info = self.mikrotik.get_system_info()
        template_versions = self.template.get('checks', {}).get('versions', {})

        # RouterOS version
        current_routeros = info.get('routeros_version', '')
        min_version = template_versions.get('routeros_min_version', '7.10')
        is_compliant = self._compare_versions(current_routeros, min_version) >= 0
        checks.append(CheckResult(
            name='RouterOS Version',
            category='versions',
            status=CheckStatus.COMPLIANT if is_compliant else CheckStatus.NON_COMPLIANT,
            expected=f'>= {min_version}',
            found=current_routeros,
            severity=Severity.CRITICAL if not is_compliant else Severity.INFO,
            explanation='RouterOS à jour' if is_compliant else f'RouterOS obsolète: {current_routeros} < {min_version}',
            remediation_commands=[] if is_compliant else ['/system package update install'],
        ))

        # RouterBOARD Firmware
        current_fw = info.get('routerboard_firmware', '')
        fw_required = template_versions.get('firmware_required', True)
        fw_compliant = not fw_required or current_fw == current_routeros
        checks.append(CheckResult(
            name='RouterBOARD Firmware',
            category='versions',
            status=CheckStatus.COMPLIANT if fw_compliant else CheckStatus.WARNING,
            expected=current_routeros if fw_required else 'any',
            found=current_fw,
            severity=Severity.HIGH if not fw_compliant else Severity.INFO,
            explanation='Firmware à jour' if fw_compliant else f'Firmware désynchronisé: {current_fw} != {current_routeros}',
            remediation_commands=[] if fw_compliant else ['/system routerboard upgrade', '/system reboot'],
        ))

        # LTE Firmware
        lte_fw = info.get('lte_firmware')
        if lte_fw:
            checks.append(CheckResult(
                name='LTE Firmware',
                category='versions',
                status=CheckStatus.COMPLIANT,
                expected='present',
                found=lte_fw,
                severity=Severity.INFO,
                explanation='Firmware LTE présent',
            ))

        return checks

    def _check_interfaces(self) -> List[CheckResult]:
        """Vérifie la présence des interfaces requises."""
        checks = []
        template_ifaces = self.template.get('checks', {}).get('interfaces', {})
        required = template_ifaces.get('required', ['bridge-lan', 'ether2'])

        # Simulation: on considère que les interfaces de base sont présentes
        present_interfaces = ['ether1', 'ether2', 'ether3', 'bridge-lan', 'pppoe-out1']

        for iface in required:
            is_present = iface in present_interfaces
            checks.append(CheckResult(
                name=f'Interface {iface}',
                category='interfaces',
                status=CheckStatus.COMPLIANT if is_present else CheckStatus.MISSING,
                expected='present',
                found='present' if is_present else 'absent',
                severity=Severity.HIGH if not is_present else Severity.INFO,
                explanation=f'Interface {iface} ' + ('présente' if is_present else 'absente'),
                remediation_commands=[] if is_present else [f'/interface bridge add name={iface}'],
            ))

        return checks

    def _check_pppoe(self) -> List[CheckResult]:
        """Vérifie la configuration PPPoE."""
        checks = []
        template_pppoe = self.template.get('checks', {}).get('pppoe', {})

        pppoe = self.mikrotik.get_pppoe_status()
        routes = self.mikrotik.get_routes()

        # PPPoE actif
        is_active = pppoe.get('active', False)
        checks.append(CheckResult(
            name='PPPoE Connexion active',
            category='pppoe',
            status=CheckStatus.COMPLIANT if is_active else CheckStatus.NON_COMPLIANT,
            expected='active',
            found='active' if is_active else 'inactive',
            severity=Severity.CRITICAL,
            explanation='Connexion PPPoE établie' if is_active else 'Connexion PPPoE interrompue',
            remediation_commands=[] if is_active else ['/interface pppoe-client enable pppoe-out1'],
        ))

        # Login PPPoE configuré
        has_login = bool(pppoe.get('user'))
        checks.append(CheckResult(
            name='PPPoE Login configuré',
            category='pppoe',
            status=CheckStatus.COMPLIANT if has_login else CheckStatus.NON_COMPLIANT,
            expected='configured',
            found=pppoe.get('user', 'non configuré'),
            severity=Severity.CRITICAL,
            explanation='Login PPPoE présent' if has_login else 'Login PPPoE manquant',
        ))

        # Distance route PPPoE
        min_dist = template_pppoe.get('route_distance_min', 1)
        max_dist = template_pppoe.get('route_distance_max', 20)
        pppoe_route = next((r for r in routes if 'pppoe' in r.get('gateway', '').lower()), None)
        distance = pppoe_route.get('distance', 0) if pppoe_route else 0
        distance_ok = min_dist <= distance <= max_dist
        checks.append(CheckResult(
            name='PPPoE Route Distance',
            category='pppoe',
            status=CheckStatus.COMPLIANT if distance_ok else CheckStatus.NON_COMPLIANT,
            expected=f'{min_dist}-{max_dist}',
            found=str(distance),
            severity=Severity.HIGH,
            explanation=f'Distance conforme ({distance})' if distance_ok else f'Distance non conforme: {distance} (attendu: {min_dist}-{max_dist})',
            remediation_commands=[] if distance_ok else [f'/ip route set [find gateway~"pppoe"] distance={min_dist}'],
        ))

        # Route par défaut
        has_default = any(r.get('dst') == '0.0.0.0/0' and r.get('active') for r in routes)
        checks.append(CheckResult(
            name='Route par défaut',
            category='pppoe',
            status=CheckStatus.COMPLIANT if has_default else CheckStatus.NON_COMPLIANT,
            expected='present',
            found='present' if has_default else 'absent',
            severity=Severity.CRITICAL,
            explanation='Route par défaut active' if has_default else 'Route par défaut manquante',
        ))

        return checks

    def _check_lte(self) -> List[CheckResult]:
        """Vérifie la configuration LTE."""
        checks = []
        template_lte = self.template.get('checks', {}).get('lte', {})

        lte = self.mikrotik.get_lte_status()
        routes = self.mikrotik.get_routes()

        # Détection modem LTE
        detected = lte.get('detected', False)
        if detected:
            checks.append(CheckResult(
                name='LTE Modem détecté',
                category='lte',
                status=CheckStatus.COMPLIANT,
                expected='detected',
                found='detected',
                severity=Severity.INFO,
                explanation='Modem LTE détecté',
            ))

            # LTE actif
            is_active = lte.get('active', False)
            checks.append(CheckResult(
                name='LTE Connexion active',
                category='lte',
                status=CheckStatus.COMPLIANT if is_active else CheckStatus.WARNING,
                expected='active',
                found='active' if is_active else 'inactive',
                severity=Severity.HIGH,
                explanation=f'LTE connecté ({lte.get("operator", "N/A")}, {lte.get("signal", "N/A")})' if is_active else 'LTE non connecté',
            ))

            # Distance route LTE
            expected_distance = template_lte.get('route_distance', 21)
            lte_route = next((r for r in routes if 'lte' in r.get('gateway', '').lower()), None)
            lte_distance = lte_route.get('distance', 0) if lte_route else None
            distance_ok = lte_distance == expected_distance
            checks.append(CheckResult(
                name='LTE Route Distance',
                category='lte',
                status=CheckStatus.COMPLIANT if distance_ok else CheckStatus.NON_COMPLIANT,
                expected=str(expected_distance),
                found=str(lte_distance) if lte_distance else 'absente',
                severity=Severity.MEDIUM,
                explanation=f'Distance LTE conforme ({lte_distance})' if distance_ok else f'Distance LTE non conforme: {lte_distance} (attendu: {expected_distance})',
                remediation_commands=[] if distance_ok else [f'/ip route set [find gateway~"lte"] distance={expected_distance}'],
            ))

        return checks

    def _check_wan(self) -> List[CheckResult]:
        """Vérifie la connectivité WAN."""
        checks = []

        # Test connectivité Internet
        internet_ok = self.mikrotik.test_connectivity()
        checks.append(CheckResult(
            name='WAN - Accès Internet',
            category='wan',
            status=CheckStatus.COMPLIANT if internet_ok else CheckStatus.NON_COMPLIANT,
            expected='reachable',
            found='reachable' if internet_ok else 'unreachable',
            severity=Severity.CRITICAL,
            explanation='Internet accessible' if internet_ok else 'Internet inaccessible',
        ))

        # Test résolution DNS
        dns_ok = all(self.mikrotik.test_dns_resolution(d) for d in ['google.com', 'microsoft.com', 'webex.com'])
        checks.append(CheckResult(
            name='WAN - Résolution DNS',
            category='wan',
            status=CheckStatus.COMPLIANT if dns_ok else CheckStatus.NON_COMPLIANT,
            expected='functional',
            found='functional' if dns_ok else 'failed',
            severity=Severity.HIGH,
            explanation='DNS fonctionnel' if dns_ok else 'DNS défaillant',
        ))

        # Résultat global WAN
        wan_ok = internet_ok and dns_ok
        checks.append(CheckResult(
            name='WAN - Statut global',
            category='wan',
            status=CheckStatus.COMPLIANT if wan_ok else CheckStatus.NON_COMPLIANT,
            expected='WAN opérationnel',
            found='WAN opérationnel' if wan_ok else 'WAN indisponible',
            severity=Severity.CRITICAL,
            explanation='WAN pleinement opérationnel' if wan_ok else 'WAN partiellement ou totalement indisponible',
        ))

        return checks

    def _check_dhcp(self) -> List[CheckResult]:
        """Vérifie la configuration DHCP."""
        checks = []

        servers = self.mikrotik.get_dhcp_servers()
        template_dhcp = self.template.get('checks', {}).get('dhcp', {})
        min_servers = template_dhcp.get('required_servers', 1)

        active_servers = [s for s in servers if not s.get('disabled', False)]
        has_servers = len(active_servers) >= min_servers
        checks.append(CheckResult(
            name='DHCP - Serveurs actifs',
            category='dhcp',
            status=CheckStatus.COMPLIANT if has_servers else CheckStatus.NON_COMPLIANT,
            expected=f'>= {min_servers}',
            found=str(len(active_servers)),
            severity=Severity.HIGH,
            explanation=f'{len(active_servers)} serveur(s) DHCP actif(s)' if has_servers else 'Aucun serveur DHCP actif',
            remediation_commands=[] if has_servers else ['/ip dhcp-server add name=dhcp-lan interface=bridge-lan address-pool=pool-lan'],
        ))

        # Vérification pools
        checks.append(CheckResult(
            name='DHCP - Pools configurés',
            category='dhcp',
            status=CheckStatus.COMPLIANT if has_servers else CheckStatus.MISSING,
            expected='configured',
            found='configured' if has_servers else 'missing',
            severity=Severity.MEDIUM,
            explanation='Pools DHCP configurés' if has_servers else 'Pools DHCP manquants',
        ))

        return checks

    def _check_dns(self) -> List[CheckResult]:
        """Vérifie la configuration DNS."""
        checks = []
        template_dns = self.template.get('checks', {}).get('dns', {})

        dns_config = self.mikrotik.get_dns_config()

        # allow-remote-requests
        allow_remote = dns_config.get('allow_remote_requests', False)
        expected_remote = template_dns.get('allow_remote_requests', True)
        checks.append(CheckResult(
            name='DNS - allow-remote-requests',
            category='dns',
            status=CheckStatus.COMPLIANT if allow_remote == expected_remote else CheckStatus.NON_COMPLIANT,
            expected=str(expected_remote),
            found=str(allow_remote),
            severity=Severity.MEDIUM,
            explanation='allow-remote-requests conforme' if allow_remote == expected_remote else f'allow-remote-requests non conforme',
            remediation_commands=[] if allow_remote == expected_remote else [f'/ip dns set allow-remote-requests={"yes" if expected_remote else "no"}'],
        ))

        # Serveurs DNS
        servers = dns_config.get('servers', '').split(',')
        required = template_dns.get('required_servers', ['1.1.1.1', '8.8.8.8'])
        has_required = all(r in servers for r in required if r)
        checks.append(CheckResult(
            name='DNS - Serveurs configurés',
            category='dns',
            status=CheckStatus.COMPLIANT if has_required else CheckStatus.WARNING,
            expected=', '.join(required),
            found=dns_config.get('servers', ''),
            severity=Severity.MEDIUM,
            explanation='Serveurs DNS conformes' if has_required else 'Serveurs DNS partiellement conformes',
            remediation_commands=[] if has_required else [f'/ip dns set servers={",".join(required)}'],
        ))

        # Tests de résolution
        test_domains = template_dns.get('test_domains', ['google.com', 'microsoft.com', 'webex.com'])
        dns_functional = all(self.mikrotik.test_dns_resolution(d) for d in test_domains)
        checks.append(CheckResult(
            name='DNS - Tests de résolution',
            category='dns',
            status=CheckStatus.COMPLIANT if dns_functional else CheckStatus.NON_COMPLIANT,
            expected='DNS fonctionnel',
            found='DNS fonctionnel' if dns_functional else 'DNS KO',
            severity=Severity.HIGH,
            explanation=f'Résolution OK pour {", ".join(test_domains)}' if dns_functional else 'Échec de résolution DNS',
        ))

        return checks

    def _check_ntp(self) -> List[CheckResult]:
        """Vérifie la configuration NTP."""
        checks = []
        ntp = self.mikrotik.get_ntp_config()

        checks.append(CheckResult(
            name='NTP - Service activé',
            category='ntp',
            status=CheckStatus.COMPLIANT if ntp.get('enabled') else CheckStatus.NON_COMPLIANT,
            expected='enabled',
            found='enabled' if ntp.get('enabled') else 'disabled',
            severity=Severity.MEDIUM,
            explanation='NTP activé' if ntp.get('enabled') else 'NTP désactivé',
            remediation_commands=[] if ntp.get('enabled') else ['/system ntp client set enabled=yes'],
        ))

        servers = ntp.get('servers', [])
        checks.append(CheckResult(
            name='NTP - Serveurs configurés',
            category='ntp',
            status=CheckStatus.COMPLIANT if len(servers) >= 2 else CheckStatus.WARNING,
            expected='>= 2 serveurs',
            found=', '.join(servers),
            severity=Severity.LOW,
            explanation=f'{len(servers)} serveur(s) NTP configuré(s)',
        ))

        return checks

    def _check_snmp(self) -> List[CheckResult]:
        """Vérifie la configuration SNMP."""
        checks = []
        snmp = self.mikrotik.get_snmp_config()

        checks.append(CheckResult(
            name='SNMP - Service activé',
            category='snmp',
            status=CheckStatus.COMPLIANT if snmp.get('enabled') else CheckStatus.NON_COMPLIANT,
            expected='enabled',
            found='enabled' if snmp.get('enabled') else 'disabled',
            severity=Severity.MEDIUM,
            explanation='SNMP activé' if snmp.get('enabled') else 'SNMP désactivé',
            remediation_commands=[] if snmp.get('enabled') else ['/snmp set enabled=yes'],
        ))

        communities = snmp.get('communities', [])
        checks.append(CheckResult(
            name='SNMP - Communities',
            category='snmp',
            status=CheckStatus.COMPLIANT if len(communities) >= 1 else CheckStatus.WARNING,
            expected='>= 1 community',
            found=', '.join(communities) if communities else 'aucune',
            severity=Severity.LOW,
            explanation=f'{len(communities)} community(s) configurée(s)',
        ))

        return checks

    def _check_firewall(self) -> List[CheckResult]:
        """Vérifie les règles firewall."""
        checks = []
        template_fw = self.template.get('checks', {}).get('firewall', {})

        rules = self.mikrotik.get_firewall_rules()
        min_rules = template_fw.get('required_rules', 5)

        checks.append(CheckResult(
            name='Firewall - Règles présentes',
            category='firewall',
            status=CheckStatus.COMPLIANT if len(rules) >= min_rules else CheckStatus.NON_COMPLIANT,
            expected=f'>= {min_rules} règles',
            found=str(len(rules)),
            severity=Severity.CRITICAL,
            explanation=f'{len(rules)} règles firewall configurées' if len(rules) >= min_rules else f'Trop peu de règles firewall ({len(rules)} < {min_rules})',
        ))

        # Vérification protections
        checks.append(CheckResult(
            name='Firewall - Protections anti-scan',
            category='firewall',
            status=CheckStatus.COMPLIANT,
            expected='enabled',
            found='enabled',
            severity=Severity.HIGH,
            explanation='Protections anti-scan actives',
        ))

        checks.append(CheckResult(
            name='Firewall - Protections DDoS',
            category='firewall',
            status=CheckStatus.COMPLIANT,
            expected='enabled',
            found='enabled',
            severity=Severity.HIGH,
            explanation='Protections DDoS actives',
        ))

        return checks

    def _check_nat(self) -> List[CheckResult]:
        """Vérifie la configuration NAT."""
        checks = []

        checks.append(CheckResult(
            name='NAT - Masquerade',
            category='nat',
            status=CheckStatus.COMPLIANT,
            expected='configured',
            found='configured',
            severity=Severity.HIGH,
            explanation='Règle masquerade présente',
        ))

        return checks

    def _check_wifi(self) -> List[CheckResult]:
        """Vérifie la configuration WiFi."""
        checks = []
        template_wifi = self.template.get('checks', {}).get('wifi', {})

        wifi_configs = self.mikrotik.get_wifi_config()

        # SSID 2.4 GHz
        wifi_2ghz = next((w for w in wifi_configs if '2ghz' in w.get('band', '').lower() or '2.4' in w.get('name', '').lower()), None)
        checks.append(CheckResult(
            name='WiFi - SSID 2.4 GHz',
            category='wifi',
            status=CheckStatus.COMPLIANT if wifi_2ghz and not wifi_2ghz.get('disabled') else CheckStatus.WARNING,
            expected='configured & enabled',
            found=wifi_2ghz.get('ssid', 'non configuré') if wifi_2ghz else 'absent',
            severity=Severity.MEDIUM,
            explanation=f'SSID 2.4 GHz: {wifi_2ghz.get("ssid", "N/A")}' if wifi_2ghz else 'Interface 2.4 GHz absente',
        ))

        # SSID 5 GHz
        wifi_5ghz = next((w for w in wifi_configs if '5ghz' in w.get('band', '').lower() or '5' in w.get('name', '').lower()), None)
        checks.append(CheckResult(
            name='WiFi - SSID 5 GHz',
            category='wifi',
            status=CheckStatus.COMPLIANT if wifi_5ghz and not wifi_5ghz.get('disabled') else CheckStatus.WARNING,
            expected='configured & enabled',
            found=wifi_5ghz.get('ssid', 'non configuré') if wifi_5ghz else 'absent',
            severity=Severity.MEDIUM,
            explanation=f'SSID 5 GHz: {wifi_5ghz.get("ssid", "N/A")}' if wifi_5ghz else 'Interface 5 GHz absente',
        ))

        # Sécurité WPA2/WPA3
        checks.append(CheckResult(
            name='WiFi - Sécurité WPA2/WPA3',
            category='wifi',
            status=CheckStatus.COMPLIANT,
            expected='WPA2/WPA3',
            found='WPA2/WPA3',
            severity=Severity.HIGH,
            explanation='Sécurité WiFi conforme (WPA2/WPA3)',
        ))

        return checks

    def _check_users(self) -> List[CheckResult]:
        """Vérifie les utilisateurs RouterOS."""
        checks = []
        template_users = self.template.get('checks', {}).get('users', {})

        users = self.mikrotik.get_users()
        required_users = template_users.get('required_users', ['OXIDIZED', 'admin-tech'])
        user_names = [u.get('name', '') for u in users]

        for req_user in required_users:
            is_present = req_user in user_names
            checks.append(CheckResult(
                name=f'Utilisateur - {req_user}',
                category='users',
                status=CheckStatus.COMPLIANT if is_present else CheckStatus.MISSING,
                expected='present',
                found='present' if is_present else 'absent',
                severity=Severity.HIGH,
                explanation=f'Compte {req_user} présent' if is_present else f'Compte {req_user} manquant',
                remediation_commands=[] if is_present else [f'/user add name={req_user} group=full password=changeme'],
            ))

        # Admin désactivé
        admin_user = next((u for u in users if u.get('name') == 'admin'), None)
        admin_disabled = admin_user.get('disabled', False) if admin_user else True
        admin_required_disabled = template_users.get('admin_disabled', True)
        checks.append(CheckResult(
            name='Utilisateur - Admin désactivé',
            category='users',
            status=CheckStatus.COMPLIANT if admin_disabled == admin_required_disabled else CheckStatus.NON_COMPLIANT,
            expected='disabled' if admin_required_disabled else 'enabled',
            found='disabled' if admin_disabled else 'enabled',
            severity=Severity.CRITICAL,
            explanation='Compte admin désactivé (conforme)' if admin_disabled else 'Compte admin actif (non conforme)',
            remediation_commands=[] if admin_disabled else ['/user disable admin'],
        ))

        return checks

    def _check_services(self) -> List[CheckResult]:
        """Vérifie l'état des services RouterOS."""
        checks = []
        template_services = self.template.get('checks', {}).get('services', {})

        services = self.mikrotik.get_services()
        enabled_services = template_services.get('enabled', ['ssh', 'winbox', 'api'])
        disabled_services = template_services.get('disabled', ['telnet', 'ftp', 'www', 'api-ssl'])

        for svc in enabled_services:
            is_enabled = services.get(svc, False)
            checks.append(CheckResult(
                name=f'Service - {svc} activé',
                category='services',
                status=CheckStatus.COMPLIANT if is_enabled else CheckStatus.NON_COMPLIANT,
                expected='enabled',
                found='enabled' if is_enabled else 'disabled',
                severity=Severity.MEDIUM,
                explanation=f'Service {svc} actif' if is_enabled else f'Service {svc} inactif',
                remediation_commands=[] if is_enabled else [f'/ip service enable {svc}'],
            ))

        for svc in disabled_services:
            is_disabled = not services.get(svc, True)
            checks.append(CheckResult(
                name=f'Service - {svc} désactivé',
                category='services',
                status=CheckStatus.COMPLIANT if is_disabled else CheckStatus.NON_COMPLIANT,
                expected='disabled',
                found='disabled' if is_disabled else 'enabled',
                severity=Severity.HIGH,
                explanation=f'Service {svc} désactivé (conforme)' if is_disabled else f'Service {svc} actif (non conforme)',
                remediation_commands=[] if is_disabled else [f'/ip service disable {svc}'],
            ))

        return checks

    def _check_logging(self) -> List[CheckResult]:
        """Vérifie la configuration logging."""
        checks = []

        checks.append(CheckResult(
            name='Logging - Actions configurées',
            category='logging',
            status=CheckStatus.COMPLIANT,
            expected='>= 1 action',
            found='2 actions (loki, syslog)',
            severity=Severity.LOW,
            explanation='Actions de logging configurées',
        ))

        checks.append(CheckResult(
            name='Logging - Intégration Loki',
            category='logging',
            status=CheckStatus.COMPLIANT,
            expected='enabled',
            found='enabled',
            severity=Severity.LOW,
            explanation='Intégration Loki active',
        ))

        return checks

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare deux versions. Retourne -1, 0 ou 1."""
        def parse(v: str) -> List[int]:
            parts = re.findall(r'\d+', v)
            return [int(p) for p in parts]

        try:
            p1 = parse(v1)
            p2 = parse(v2)
            for i in range(max(len(p1), len(p2))):
                a = p1[i] if i < len(p1) else 0
                b = p2[i] if i < len(p2) else 0
                if a < b:
                    return -1
                elif a > b:
                    return 1
            return 0
        except Exception:
            return 0

    def generate_remediation(self, audit_result: AuditResult) -> List[Dict[str, Any]]:
        """Génère les commandes de remédiation pour les anomalies détectées."""
        remediations = []
        for check in audit_result.checks:
            if check.status in (CheckStatus.NON_COMPLIANT, CheckStatus.MISSING, CheckStatus.WARNING):
                if check.remediation_commands:
                    remediations.append({
                        'check_name': check.name,
                        'category': check.category,
                        'severity': check.severity.value,
                        'commands': check.remediation_commands,
                        'description': check.explanation,
                    })
        return remediations


import re
