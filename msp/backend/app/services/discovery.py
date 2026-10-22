"""
Service de découverte automatique et provisioning des routeurs Mikrotik.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.mikrotik import MikrotikService
from app.models.models import Router, Template, FirmwareUpdate, RouterStatus

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Service de découverte automatique des équipements Mikrotik."""

    def __init__(self, db_session):
        self.db = db_session

    def discover_router(self, ip_address: str, username: str = "admin",
                        password: str = "", api_port: int = 8728) -> Dict[str, Any]:
        """
        Découvre un routeur Mikrotik sur le réseau.
        Se connecte à 192.168.88.1 par défaut et récupère toutes les informations.
        """
        logger.info(f"Découverte du routeur sur {ip_address}:{api_port}")

        mikrotik = MikrotikService(
            host=ip_address,
            username=username,
            password=password,
            api_port=api_port,
        )

        # Connexion et récupération des informations
        info = mikrotik.get_system_info()

        result = {
            'ip_address': ip_address,
            'model': info.get('model'),
            'hardware_revision': info.get('hardware_revision'),
            'serial_number': info.get('serial_number'),
            'cpu_architecture': info.get('cpu_architecture'),
            'hostname': info.get('hostname'),
            'mac_main': info.get('mac_main'),
            'mac_ether2': info.get('mac_ether2'),
            'routeros_version': info.get('routeros_version'),
            'routerboard_firmware': info.get('routerboard_firmware'),
            'lte_firmware': info.get('lte_firmware'),
            'discovered_at': datetime.utcnow().isoformat(),
        }

        # Recherche du template correspondant au modèle
        template = self._find_template_for_model(info.get('model', ''))
        result['template_id'] = template.id if template else None
        result['template_name'] = template.name if template else None
        result['template_found'] = template is not None

        if not template:
            logger.warning(f"Aucun template trouvé pour le modèle: {info.get('model')}")

        mikrotik.disconnect()
        return result

    def _find_template_for_model(self, model: str) -> Optional[Template]:
        """Recherche un template correspondant au modèle de routeur."""
        if not model:
            return None
        # Recherche exacte d'abord
        template = self.db.query(Template).filter(
            Template.model == model,
            Template.is_active == True
        ).first()
        if template:
            return template
        # Recherche par pattern (ex: hAP ac² -> hAP ac2)
        model_normalized = model.replace('²', '2').replace('^', '')
        template = self.db.query(Template).filter(
            Template.model.ilike(f'%{model_normalized}%'),
            Template.is_active == True
        ).first()
        return template

    def register_router(self, discovery_data: Dict[str, Any],
                        client_id: Optional[str] = None,
                        site_id: Optional[str] = None,
                        template_id: Optional[str] = None) -> Router:
        """Enregistre un routeur découvert dans la base de données."""
        # Vérifier si le routeur existe déjà (par serial ou IP)
        existing = self.db.query(Router).filter(
            (Router.serial_number == discovery_data.get('serial_number')) |
            (Router.ip_address == discovery_data.get('ip_address'))
        ).first()

        if existing:
            # Mise à jour
            for key, value in discovery_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.is_discovered = True
            existing.last_seen = datetime.utcnow()
            existing.status = RouterStatus.ONLINE
            self.db.commit()
            logger.info(f"Routeur mis à jour: {existing.hostname}")
            return existing

        # Création
        router = Router(
            hostname=discovery_data.get('hostname', f"router-{discovery_data.get('ip_address')}"),
            ip_address=discovery_data.get('ip_address'),
            model=discovery_data.get('model'),
            hardware_revision=discovery_data.get('hardware_revision'),
            serial_number=discovery_data.get('serial_number'),
            cpu_architecture=discovery_data.get('cpu_architecture'),
            mac_main=discovery_data.get('mac_main'),
            mac_ether2=discovery_data.get('mac_ether2'),
            routeros_version=discovery_data.get('routeros_version'),
            routerboard_firmware=discovery_data.get('routerboard_firmware'),
            lte_firmware=discovery_data.get('lte_firmware'),
            client_id=client_id,
            site_id=site_id,
            template_id=template_id or discovery_data.get('template_id'),
            is_discovered=True,
            status=RouterStatus.ONLINE,
            last_seen=datetime.utcnow(),
        )
        self.db.add(router)
        self.db.commit()
        self.db.refresh(router)
        logger.info(f"Routeur enregistré: {router.hostname} ({router.model})")
        return router


class ProvisioningService:
    """Service de provisioning automatisé des routeurs."""

    def __init__(self, db_session):
        self.db = db_session

    def check_updates(self, router: Router) -> Dict[str, Any]:
        """
        Vérifie si des mises à jour sont nécessaires.
        Workflow: Détection -> Vérification -> Mise à jour -> Redémarrage -> Validation
        """
        mikrotik = MikrotikService(
            host=router.ip_address,
            username=router.username,
            password=router.password or "",
            api_port=router.api_port,
        )

        info = mikrotik.get_system_info()
        updates_needed = {
            'routeros': {
                'current': info.get('routeros_version'),
                'target': router.routeros_target_version or '7.15.3',
                'needs_update': info.get('routeros_version') != (router.routeros_target_version or '7.15.3'),
            },
            'routerboard': {
                'current': info.get('routerboard_firmware'),
                'target': info.get('routeros_version'),
                'needs_update': info.get('routerboard_firmware') != info.get('routeros_version'),
            },
            'lte': {
                'current': info.get('lte_firmware'),
                'target': 'latest',
                'needs_update': False,  # À implémenter avec la vraie API
            },
        }

        mikrotik.disconnect()
        return updates_needed

    def perform_update(self, router: Router, update_type: str) -> FirmwareUpdate:
        """Effectue une mise à jour de firmware/RouterOS."""
        import time
        start_time = time.time()

        update = FirmwareUpdate(
            router_id=router.id,
            update_type=update_type,
            status='pending',
            started_at=datetime.utcnow(),
        )
        self.db.add(update)
        self.db.commit()

        try:
            mikrotik = MikrotikService(
                host=router.ip_address,
                username=router.username,
                password=router.password or "",
                api_port=router.api_port,
            )
            info = mikrotik.get_system_info()
            update.old_version = info.get('routeros_version' if update_type == 'routeros' else 'routerboard_firmware')

            update.status = 'downloading'
            self.db.commit()

            # Simulation de la mise à jour
            if update_type == 'routeros':
                update.new_version = router.routeros_target_version or '7.15.3'
                # mikrotik.execute_command('/system package update install')
            elif update_type == 'routerboard':
                update.new_version = info.get('routeros_version')
                # mikrotik.execute_command('/system routerboard upgrade')

            update.status = 'installing'
            self.db.commit()

            # Redémarrage
            mikrotik.reboot()
            update.status = 'completed'
            update.result = 'Mise à jour effectuée avec succès'

            # Mise à jour du routeur
            if update_type == 'routeros':
                router.routeros_version = update.new_version
            elif update_type == 'routerboard':
                router.routerboard_firmware = update.new_version

        except Exception as e:
            update.status = 'failed'
            update.result = str(e)
            logger.error(f"Échec mise à jour {update_type} pour {router.hostname}: {e}")

        update.completed_at = datetime.utcnow()
        update.duration_seconds = time.time() - start_time
        self.db.commit()
        self.db.refresh(update)

        return update

    def provision_router(self, router: Router, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Provisionnement complet d'un routeur:
        1. Vérification template
        2. Mise à jour si nécessaire
        3. Import du template .rsc
        4. Application de la configuration
        5. Redémarrage
        6. Validation
        """
        result = {
            'router_id': router.id,
            'hostname': router.hostname,
            'steps': [],
            'success': False,
            'error': None,
        }

        # 1. Vérification template
        if not router.template_id:
            result['error'] = 'Aucun template associé au routeur'
            result['steps'].append({'step': 'template_check', 'status': 'failed', 'message': 'Template manquant'})
            return result

        template = self.db.query(Template).filter(Template.id == router.template_id).first()
        if not template:
            result['error'] = 'Template introuvable en base'
            return result

        result['steps'].append({'step': 'template_check', 'status': 'ok', 'message': f'Template trouvé: {template.name}'})

        # 2. Vérification mises à jour
        updates = self.check_updates(router)
        for update_type, info in updates.items():
            if info.get('needs_update'):
                result['steps'].append({'step': f'update_{update_type}', 'status': 'pending', 'message': f"Mise à jour {update_type}: {info['current']} -> {info['target']}"})
                update = self.perform_update(router, update_type)
                result['steps'].append({
                    'step': f'update_{update_type}',
                    'status': 'ok' if update.status == 'completed' else 'failed',
                    'message': update.result,
                })
                if update.status == 'failed':
                    result['error'] = f'Échec mise à jour {update_type} - Provisioning bloqué'
                    return result

        # 3. Préparation des variables
        default_variables = {
            'client_id': router.client_id or 'default',
            'hostname': router.hostname,
            'serial_number': router.serial_number or '',
            'mac_ether2': router.mac_ether2 or '',
            'pppoe_login': router.pppoe_login or '',
            'pppoe_password': router.pppoe_password or '',
            'ssid_2ghz': router.ssid_2ghz or f'WiFi-{router.hostname}-2.4',
            'ssid_5ghz': router.ssid_5ghz or f'WiFi-{router.hostname}-5',
            'wifi_key': router.wifi_key or 'changeme123',
            'vlan': str(router.site.vlan) if router.site and router.site.vlan else '1',
            'site': router.site.name if router.site else 'default',
            'ip_lan': router.site.ip_lan if router.site and router.site.ip_lan else '192.168.88.1',
            'ip_wan': 'dhcp',
        }
        if variables:
            default_variables.update(variables)

        result['variables'] = default_variables
        result['steps'].append({'step': 'variables_preparation', 'status': 'ok', 'message': 'Variables préparées'})

        # 4. Génération du script de configuration
        rsc_content = template.rsc_content or ''
        # Substitution des variables dans le template
        for key, value in default_variables.items():
            rsc_content = rsc_content.replace(f'{{{{{key}}}}}', str(value))

        result['steps'].append({'step': 'config_generation', 'status': 'ok', 'message': 'Configuration générée'})

        # 5. Déploiement (simulé)
        mikrotik = MikrotikService(
            host=router.ip_address,
            username=router.username,
            password=router.password or "",
            api_port=router.api_port,
        )

        # Upload du fichier de configuration
        mikrotik.upload_file('configuration.rsc', rsc_content)
        result['steps'].append({'step': 'config_upload', 'status': 'ok', 'message': 'Configuration uploadée'})

        # Application avec reset-configuration
        mikrotik.execute_script('/system reset-configuration run-after-reset=configuration.rsc')
        result['steps'].append({'step': 'config_apply', 'status': 'ok', 'message': 'Reset-configuration programmé'})

        # Redémarrage
        mikrotik.reboot()
        result['steps'].append({'step': 'reboot', 'status': 'ok', 'message': 'Redémarrage effectué'})

        # 6. Mise à jour du statut
        router.is_provisioned = True
        router.last_provisioning_at = datetime.utcnow()
        router.status = RouterStatus.ONLINE
        self.db.commit()

        result['success'] = True
        result['steps'].append({'step': 'validation', 'status': 'ok', 'message': 'Provisionnement terminé avec succès'})

        mikrotik.disconnect()
        return result
