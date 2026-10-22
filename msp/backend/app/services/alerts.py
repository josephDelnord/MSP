"""
Service de gestion des alertes et notifications.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.models import Alert, AlertSeverity, AlertStatus, Router, RouterStatus, ComplianceStatus

logger = logging.getLogger(__name__)


class AlertService:
    """Service de gestion des alertes."""

    # Définition des types d'alertes
    ALERT_TYPES = {
        'router_offline': {
            'title': 'Routeur inaccessible',
            'severity': AlertSeverity.CRITICAL,
            'category': 'connectivity',
        },
        'wan_down': {
            'title': 'WAN indisponible',
            'severity': AlertSeverity.CRITICAL,
            'category': 'network',
        },
        'lte_down': {
            'title': 'LTE indisponible',
            'severity': AlertSeverity.WARNING,
            'category': 'network',
        },
        'internet_loss': {
            'title': 'Perte de connectivité Internet',
            'severity': AlertSeverity.CRITICAL,
            'category': 'network',
        },
        'update_failed_routeros': {
            'title': 'Échec de mise à jour RouterOS',
            'severity': AlertSeverity.CRITICAL,
            'category': 'update',
        },
        'update_failed_firmware': {
            'title': 'Échec de mise à jour Firmware',
            'severity': AlertSeverity.HIGH if hasattr(AlertSeverity, 'HIGH') else AlertSeverity.CRITICAL,
            'category': 'update',
        },
        'update_failed_lte': {
            'title': 'Échec de mise à jour LTE',
            'severity': AlertSeverity.WARNING,
            'category': 'update',
        },
        'non_compliant': {
            'title': 'Configuration non conforme',
            'severity': AlertSeverity.WARNING,
            'category': 'compliance',
        },
        'remediation_failed': {
            'title': 'Échec d\'auto-remédiation',
            'severity': AlertSeverity.CRITICAL,
            'category': 'remediation',
        },
        'serial_changed': {
            'title': 'Changement de numéro de série détecté',
            'severity': AlertSeverity.CRITICAL,
            'category': 'security',
        },
        'mac_changed': {
            'title': 'Changement de MAC Ether2 détecté',
            'severity': AlertSeverity.CRITICAL,
            'category': 'security',
        },
        'template_missing': {
            'title': 'Template absent pour le modèle',
            'severity': AlertSeverity.CRITICAL,
            'category': 'provisioning',
        },
        'config_drift': {
            'title': 'Dérive de configuration détectée',
            'severity': AlertSeverity.WARNING,
            'category': 'compliance',
        },
    }

    def __init__(self, db_session):
        self.db = db_session

    def create_alert(self, alert_type: str, router: Optional[Router] = None,
                     description: Optional[str] = None,
                     custom_data: Optional[Dict[str, Any]] = None) -> Alert:
        """Crée une nouvelle alerte."""
        alert_def = self.ALERT_TYPES.get(alert_type, {
            'title': alert_type,
            'severity': AlertSeverity.INFO,
            'category': 'general',
        })

        # Vérifier si une alerte similaire existe déjà (non résolue)
        existing = self.db.query(Alert).filter(
            Alert.router_id == (router.id if router else None),
            Alert.category == alert_def['category'],
            Alert.status == AlertStatus.ACTIVE,
            Alert.title == alert_def['title'],
        ).first()

        if existing:
            logger.info(f"Alerte déjà active: {alert_def['title']}")
            return existing

        alert = Alert(
            router_id=router.id if router else None,
            severity=alert_def['severity'],
            title=alert_def['title'],
            description=description or self._build_description(alert_type, router, custom_data),
            category=alert_def['category'],
            status=AlertStatus.ACTIVE,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.warning(f"Nouvelle alerte créée: [{alert.severity.value}] {alert.title}")
        return alert

    def _build_description(self, alert_type: str, router: Optional[Router],
                           custom_data: Optional[Dict[str, Any]]) -> str:
        """Construit la description de l'alerte."""
        parts = []
        if router:
            parts.append(f"Routeur: {router.hostname}")
            parts.append(f"Modèle: {router.model or 'N/A'}")
            parts.append(f"Numéro de série: {router.serial_number or 'N/A'}")
            parts.append(f"MAC Ether2: {router.mac_ether2 or 'N/A'}")
            parts.append(f"Adresse IP: {router.ip_address}")
            if router.site:
                parts.append(f"Site: {router.site.name}")
        if custom_data:
            for key, value in custom_data.items():
                parts.append(f"{key}: {value}")
        return "\n".join(parts)

    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Marque une alerte comme résolue."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Alerte résolue: {alert.title}")
        return alert

    def acknowledge_alert(self, alert_id: str) -> Optional[Alert]:
        """Marque une alerte comme acquittée."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.status = AlertStatus.ACKNOWLEDGED
            self.db.commit()
        return alert

    def get_active_alerts(self, router_id: Optional[str] = None,
                          severity: Optional[str] = None) -> List[Alert]:
        """Récupère les alertes actives."""
        query = self.db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE)
        if router_id:
            query = query.filter(Alert.router_id == router_id)
        if severity:
            query = query.filter(Alert.severity == severity)
        return query.order_by(Alert.created_at.desc()).all()

    def check_router_health(self, router: Router) -> List[Alert]:
        """Vérifie la santé d'un routeur et génère les alertes nécessaires."""
        alerts = []

        # Routeur hors ligne
        if router.status == RouterStatus.OFFLINE:
            alerts.append(self.create_alert('router_offline', router))

        # Non conforme
        if router.compliance_status == ComplianceStatus.NON_COMPLIANT:
            alerts.append(self.create_alert('non_compliant', router))

        # Version obsolète
        if router.routeros_version and router.routeros_target_version:
            if router.routeros_version != router.routeros_target_version:
                alerts.append(self.create_alert(
                    'non_compliant', router,
                    description=f"Version RouterOS obsolète: {router.routeros_version} (cible: {router.routeros_target_version})",
                    custom_data={'type': 'outdated_version'}
                ))

        return alerts


class NotificationService:
    """Service de notification multi-canaux."""

    SUPPORTED_CHANNELS = ['webex', 'teams', 'email', 'webhook', 'servicenow', 'glpi', 'jira']

    def __init__(self, db_session):
        self.db = db_session

    def send_notification(self, alert: Alert, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Envoie une notification pour une alerte sur les canaux spécifiés.
        En environnement local, les notifications sont loguées.
        """
        channels = channels or ['email']
        results = {}

        message = self._build_message(alert)

        for channel in channels:
            if channel not in self.SUPPORTED_CHANNELS:
                results[channel] = {'status': 'skipped', 'reason': 'channel not supported'}
                continue

            try:
                if channel == 'email':
                    results[channel] = self._send_email(alert, message)
                elif channel == 'webex':
                    results[channel] = self._send_webex(alert, message)
                elif channel == 'teams':
                    results[channel] = self._send_teams(alert, message)
                elif channel == 'webhook':
                    results[channel] = self._send_webhook(alert, message)
                else:
                    # Simulation pour les autres canaux
                    results[channel] = self._simulate_notification(channel, alert, message)

                logger.info(f"Notification envoyée via {channel} pour alerte {alert.id}")

            except Exception as e:
                results[channel] = {'status': 'failed', 'error': str(e)}
                logger.error(f"Échec notification {channel}: {e}")

        # Mise à jour de l'alerte
        alert.is_notified = any(r.get('status') == 'sent' for r in results.values())
        alert.notified_at = datetime.utcnow()
        alert.notification_channels = [c for c, r in results.items() if r.get('status') == 'sent']
        self.db.commit()

        return results

    def _build_message(self, alert: Alert) -> Dict[str, Any]:
        """Construit le message de notification."""
        router = alert.router
        return {
            'subject': f"[{alert.severity.value.upper()}] {alert.title}",
            'body': alert.description or '',
            'hostname': router.hostname if router else 'N/A',
            'model': router.model if router else 'N/A',
            'serial_number': router.serial_number if router else 'N/A',
            'mac_ether2': router.mac_ether2 if router else 'N/A',
            'ip_address': router.ip_address if router else 'N/A',
            'site': router.site.name if router and router.site else 'N/A',
            'severity': alert.severity.value,
            'category': alert.category,
            'description': alert.description,
            'platform_url': f"http://localhost:3000/routers/{router.id}" if router else "http://localhost:3000",
        }

    def _send_email(self, alert: Alert, message: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une notification par email (simulé en local)."""
        logger.info(f"[EMAIL] To: admin@localhost | Subject: {message['subject']}")
        logger.info(f"[EMAIL] Body: {message['body'][:200]}...")
        return {'status': 'sent', 'channel': 'email'}

    def _send_webex(self, alert: Alert, message: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une notification Cisco Webex (simulé en local)."""
        logger.info(f"[WEBEX] {message['subject']}")
        return {'status': 'sent', 'channel': 'webex'}

    def _send_teams(self, alert: Alert, message: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une notification Microsoft Teams (simulé en local)."""
        logger.info(f"[TEAMS] {message['subject']}")
        return {'status': 'sent', 'channel': 'teams'}

    def _send_webhook(self, alert: Alert, message: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une notification webhook (simulé en local)."""
        logger.info(f"[WEBHOOK] POST {message['subject']}")
        return {'status': 'sent', 'channel': 'webhook'}

    def _simulate_notification(self, channel: str, alert: Alert, message: Dict[str, Any]) -> Dict[str, Any]:
        """Simule l'envoi pour les canaux ITSM."""
        logger.info(f"[{channel.upper()}] {message['subject']} - {message.get('hostname', 'N/A')}")
        return {'status': 'sent', 'channel': channel}
