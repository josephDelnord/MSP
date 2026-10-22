"""
Application FastAPI principale - Mikrotik Provisioning Manager (MSP)
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import engine, Base, get_db
from app.models.models import (
    Router, Client, Site, Template, Audit, Alert, FirmwareUpdate, User,
    RouterStatus, ComplianceStatus, AlertSeverity, AlertStatus,
    AuditStatus, RemediationMode, UserRole,
)
from app.schemas.schemas import (
    RouterCreate, RouterUpdate, RouterResponse, RouterDiscoveryRequest,
    ClientCreate, ClientUpdate, ClientResponse,
    SiteCreate, SiteUpdate, SiteResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    AuditCreate, AuditResponse, AuditCheckResult,
    AlertCreate, AlertResponse,
    FirmwareUpdateResponse,
    DashboardStats,
    Token, UserCreate, UserResponse, UserLogin,
)
from app.services.mikrotik import MikrotikService
from app.services.compliance import ComplianceEngine
from app.services.discovery import DiscoveryService, ProvisioningService
from app.services.alerts import AlertService, NotificationService

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Sécurité
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: créer les tables
    logger.info("Démarrage de MSP - Création des tables...")
    Base.metadata.create_all(bind=engine)
    # Créer un utilisateur admin par défaut
    db = next(get_db())
    _create_default_admin(db)
    _seed_sample_data(db)
    db.close()
    logger.info("MSP démarré avec succès")
    yield
    # Shutdown
    logger.info("Arrêt de MSP")


def _create_default_admin(db: Session):
    """Crée l'utilisateur admin par défaut si inexistant."""
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@msp.com",
            hashed_password=pwd_context.hash("admin"),
            full_name="Administrateur MSP",
            role=UserRole.ADMIN,
            is_superuser=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Utilisateur admin créé (admin/admin)")


def _seed_sample_data(db: Session):
    """Insère des données de démonstration."""
    # Template de démo
    if db.query(Template).count() == 0:
        templates = [
            Template(
                name="template-hap-ac2",
                model="hAP ac²",
                description="Template pour Mikrotik hAP ac²",
                rsc_content=open("/app/templates/template-hap-ac2.rsc").read() if __import__('os').path.exists("/app/templates/template-hap-ac2.rsc") else DEFAULT_RSC_TEMPLATE,
                yaml_content=open("/app/templates/template-hap-ac2.yaml").read() if __import__('os').path.exists("/app/templates/template-hap-ac2.yaml") else DEFAULT_YAML_TEMPLATE,
                target_routeros_version="7.15.3",
                target_routerboard_firmware="7.15.3",
            ),
            Template(
                name="template-hap-ax2",
                model="hAP ax²",
                description="Template pour Mikrotik hAP ax²",
                rsc_content=DEFAULT_RSC_TEMPLATE,
                yaml_content=DEFAULT_YAML_TEMPLATE,
                target_routeros_version="7.15.3",
                target_routerboard_firmware="7.15.3",
            ),
            Template(
                name="template-chateau-lte12",
                model="Chateau LTE12",
                description="Template pour Mikrotik Chateau LTE12",
                rsc_content=DEFAULT_RSC_TEMPLATE,
                yaml_content=DEFAULT_YAML_TEMPLATE,
                target_routeros_version="7.15.3",
                target_routerboard_firmware="7.15.3",
                target_lte_firmware="latest",
            ),
        ]
        for t in templates:
            db.add(t)

        # Client de démo
        client = Client(
            name="Client Demo",
            reference_crm="CRM-001",
            contact_email="demo@client.fr",
        )
        db.add(client)
        db.flush()

        # Site de démo
        site = Site(
            client_id=client.id,
            name="Site Principal",
            address="123 Rue de la Tech",
            city="Paris",
            postal_code="75001",
            vlan=10,
            ip_lan="192.168.10.1",
        )
        db.add(site)
        db.flush()

        # Routeurs de démo
        routers = [
            Router(
                hostname="mikrotik-paris-01",
                ip_address="192.168.88.1",
                model="hAP ac²",
                serial_number="SN001DEMO",
                mac_ether2="AA:BB:CC:DD:EE:01",
                mac_main="AA:BB:CC:DD:EE:00",
                routeros_version="7.12.1",
                routerboard_firmware="7.12.1",
                routeros_target_version="7.15.3",
                status=RouterStatus.ONLINE,
                compliance_status=ComplianceStatus.COMPLIANT_WITH_WARNINGS,
                compliance_score=87.5,
                is_discovered=True,
                is_provisioned=True,
                client_id=client.id,
                site_id=site.id,
                template_id=templates[0].id,
                pppoe_login="client001@isp.fr",
                ssid_2ghz="WiFi-Paris-2.4",
                ssid_5ghz="WiFi-Paris-5",
            ),
            Router(
                hostname="mikrotik-lyon-01",
                ip_address="192.168.88.2",
                model="hAP ax²",
                serial_number="SN002DEMO",
                mac_ether2="AA:BB:CC:DD:EE:11",
                mac_main="AA:BB:CC:DD:EE:10",
                routeros_version="7.10.0",
                routerboard_firmware="7.10.0",
                routeros_target_version="7.15.3",
                status=RouterStatus.ONLINE,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                compliance_score=62.0,
                is_discovered=True,
                is_provisioned=False,
                client_id=client.id,
                site_id=site.id,
                template_id=templates[1].id,
            ),
            Router(
                hostname="mikrotik-lte-01",
                ip_address="192.168.88.3",
                model="Chateau LTE12",
                serial_number="SN003DEMO",
                mac_ether2="AA:BB:CC:DD:EE:21",
                mac_main="AA:BB:CC:DD:EE:20",
                routeros_version="7.15.3",
                routerboard_firmware="7.15.3",
                lte_firmware="MOBYR_123456",
                status=RouterStatus.OFFLINE,
                compliance_status=ComplianceStatus.UNKNOWN,
                compliance_score=0.0,
                is_discovered=True,
                is_provisioned=True,
            ),
        ]
        for r in routers:
            db.add(r)

        db.commit()
        logger.info("Données de démonstration insérées")


DEFAULT_RSC_TEMPLATE = """# Template RouterOS - Configuration automatique MSP
# Généré automatiquement par Mikrotik Provisioning Manager

/system identity set name="{{hostname}}"

# Configuration utilisateurs
/user add name=OXIDIZED group=read password="{{wifi_key}}" comment="Monitoring"
/user add name=admin-tech group=full password="{{wifi_key}}" comment="Technicien"
/user disable admin

# Configuration WiFi
/interface wifi set wifi1 ssid="{{ssid_2ghz}}" disabled=no
/interface wifi set wifi2 ssid="{{ssid_5ghz}}" disabled=no

# Configuration PPPoE
/interface pppoe-client add name=pppoe-out1 interface=ether1 user="{{pppoe_login}}" password="{{pppoe_password}}" add-default-route=yes default-route-distance=1

# Configuration DNS
/ip dns set allow-remote-requests=yes servers=1.1.1.1,8.8.8.8

# Configuration NTP
/system ntp client set enabled=yes mode=unicast
/system ntp client servers add address=pool.ntp.org
/system ntp client servers add address=time.google.com

# Configuration SNMP
/snmp set enabled=yes contact="msp@operator.fr" location="{{site}}"
/snmp community add name=msp-monitoring addresses=0.0.0.0/0 authentication-protocol=SHA1

# Configuration Logging
/system logging action add name=loki target=loki
/system logging add topics=info,!ntp action=loki

# Configuration Firewall - Base
/ip firewall filter add chain=input action=accept connection-state=established,related comment="Accept established"
/ip firewall filter add chain=input action=drop connection-state=invalid comment="Drop invalid"
/ip firewall filter add chain=input action=drop protocol=tcp dst-port=22,23,8291 in-interface=pppoe-out1 comment="Block WAN access"

# NAT
/ip firewall nat add chain=srcnat action=masquerade out-interface=pppoe-out1 comment="Masquerade WAN"
"""

DEFAULT_YAML_TEMPLATE = """name: default
model: generic
description: Template de conformité par défaut

checks:
  versions:
    routeros_min_version: "7.10"
    firmware_required: true

  interfaces:
    required:
      - bridge-lan
      - ether2
    wan_interface: ether1

  pppoe:
    required: true
    max_active: 1
    route_distance_min: 1
    route_distance_max: 20
    check_internet: true
    check_default_route: true
    check_wan_list: true

  lte:
    route_distance: 21
    check_if_present: true

  dhcp:
    required_servers: 1
    check_pools: true
    check_networks: true
    check_gateways: true

  dns:
    allow_remote_requests: true
    required_servers:
      - "1.1.1.1"
      - "8.8.8.8"
    test_domains:
      - google.com
      - microsoft.com
      - webex.com

  ntp:
    enabled: true
    required_servers: 2

  snmp:
    enabled: true
    required_communities: 1

  firewall:
    required_rules: 5
    check_order: true
    anti_scan: true
    ddos_protection: true
    wan_restrictions: true

  nat:
    masquerade_required: true

  wifi:
    check_ssid: true
    check_2ghz: true
    check_5ghz: true
    check_security: true
    wpa2_required: true

  users:
    required_users:
      - OXIDIZED
      - admin-tech
    admin_disabled: true

  services:
    enabled:
      - ssh
      - winbox
      - api
    disabled:
      - telnet
      - ftp
      - www
      - api-ssl

  logging:
    actions_required: 1
    loki_enabled: true

  scripts:
    required_scripts: []

  scheduler:
    required_jobs: []
"""


# Création de l'application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plateforme SaaS de gestion centralisée du cycle de vie des routeurs Mikrotik",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency pour l'authentification (simplifiée pour le local)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user


# ==================== AUTHENTIFICATION ====================

@app.post("/api/auth/token", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = jwt.encode(
        {"sub": user.username, "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    user.last_login = datetime.utcnow()
    db.commit()
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.post("/api/auth/register", response_model=UserResponse, tags=["Auth"])
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=pwd_context.hash(user_data.password),
        full_name=user_data.full_name,
        role=UserRole(user_data.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ==================== DASHBOARD ====================

@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(Router).count()
    online = db.query(Router).filter(Router.status == RouterStatus.ONLINE).count()
    offline = db.query(Router).filter(Router.status == RouterStatus.OFFLINE).count()
    non_compliant = db.query(Router).filter(
        Router.compliance_status == ComplianceStatus.NON_COMPLIANT
    ).count()
    error = db.query(Router).filter(Router.status == RouterStatus.ERROR).count()
    outdated = db.query(Router).filter(
        Router.routeros_version != Router.routeros_target_version,
        Router.routeros_target_version.isnot(None),
    ).count()
    active_alerts = db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE).count()
    critical_alerts = db.query(Alert).filter(
        Alert.status == AlertStatus.ACTIVE,
        Alert.severity == AlertSeverity.CRITICAL,
    ).count()

    return DashboardStats(
        total_routers=total,
        online_routers=online,
        offline_routers=offline,
        non_compliant_routers=non_compliant,
        error_routers=error,
        outdated_routers=outdated,
        active_alerts=active_alerts,
        critical_alerts=critical_alerts,
    )


@app.get("/api/dashboard/routers-status", tags=["Dashboard"])
async def get_routers_status_summary(db: Session = Depends(get_db)):
    """Résumé de l'état des routeurs pour le dashboard."""
    routers = db.query(Router).all()
    return [
        {
            'id': r.id,
            'hostname': r.hostname,
            'model': r.model,
            'ip_address': r.ip_address,
            'status': r.status.value,
            'compliance_status': r.compliance_status.value,
            'compliance_score': r.compliance_score,
            'routeros_version': r.routeros_version,
            'last_seen': r.last_seen.isoformat() if r.last_seen else None,
        }
        for r in routers
    ]


# ==================== ROUTEURS ====================

@app.get("/api/routers", response_model=List[RouterResponse], tags=["Routers"])
async def list_routers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Router)
    if status:
        query = query.filter(Router.status == status)
    if client_id:
        query = query.filter(Router.client_id == client_id)
    return query.offset(skip).limit(limit).all()


@app.get("/api/routers/{router_id}", response_model=RouterResponse, tags=["Routers"])
async def get_router(router_id: str, db: Session = Depends(get_db)):
    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        raise HTTPException(status_code=404, detail="Routeur non trouvé")
    return router


@app.post("/api/routers", response_model=RouterResponse, tags=["Routers"])
async def create_router(router_data: RouterCreate, db: Session = Depends(get_db)):
    # Vérifier si l'IP existe déjà
    existing = db.query(Router).filter(Router.ip_address == router_data.ip_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un routeur avec cette IP existe déjà")

    router = Router(**router_data.model_dump())
    db.add(router)
    db.commit()
    db.refresh(router)
    return router


@app.put("/api/routers/{router_id}", response_model=RouterResponse, tags=["Routers"])
async def update_router(router_id: str, router_data: RouterUpdate, db: Session = Depends(get_db)):
    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        raise HTTPException(status_code=404, detail="Routeur non trouvé")

    for key, value in router_data.model_dump(exclude_unset=True).items():
        setattr(router, key, value)

    db.commit()
    db.refresh(router)
    return router


@app.delete("/api/routers/{router_id}", tags=["Routers"])
async def delete_router(router_id: str, db: Session = Depends(get_db)):
    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        raise HTTPException(status_code=404, detail="Routeur non trouvé")
    db.delete(router)
    db.commit()
    return {"message": "Routeur supprimé"}


@app.post("/api/routers/discover", tags=["Routers"])
async def discover_router(
    discovery: RouterDiscoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Découverte automatique d'un routeur Mikrotik."""
    discovery_service = DiscoveryService(db)
    result = discovery_service.discover_router(
        ip_address=discovery.ip_address,
        username=discovery.username,
        password=discovery.password,
        api_port=discovery.api_port,
    )

    # Si template trouvé, créer/mettre à jour le routeur
    if result.get('serial_number'):
        router = discovery_service.register_router(result)
        result['router_id'] = router.id

        # Générer alerte si pas de template
        if not result.get('template_found'):
            alert_service = AlertService(db)
            alert_service.create_alert(
                'template_missing',
                router,
                description=f"Aucun template trouvé pour le modèle: {result.get('model')}",
            )

    return result


@app.post("/api/routers/{router_id}/provision", tags=["Routers"])
async def provision_router(
    router_id: str,
    variables: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """Provisionnement automatisé d'un routeur."""
    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        raise HTTPException(status_code=404, detail="Routeur non trouvé")

    provisioning_service = ProvisioningService(db)
    result = provisioning_service.provision_router(router, variables)
    return result


@app.post("/api/routers/{router_id}/update", tags=["Routers"])
async def update_router_firmware(
    router_id: str,
    update_type: str = "routeros",
    db: Session = Depends(get_db),
):
    """Met à jour le firmware/RouterOS d'un routeur."""
    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        raise HTTPException(status_code=404, detail="Routeur non trouvé")

    if update_type not in ["routeros", "routerboard", "lte"]:
        raise HTTPException(status_code=400, detail="Type de mise à jour invalide")

    provisioning_service = ProvisioningService(db)
    update = provisioning_service.perform_update(router, update_type)
    return update


@app.get("/api/routers/{router_id}/updates", response_model=List[FirmwareUpdateResponse], tags=["Routers"])
async def get_router_updates(router_id: str, db: Session = Depends(get_db)):
    """Historique des mises à jour d'un routeur."""
    updates = db.query(FirmwareUpdate).filter(
        FirmwareUpdate.router_id == router_id
    ).order_by(FirmwareUpdate.created_at.desc()).all()
    return updates


# ==================== AUDITS ====================

@app.post("/api/audits", response_model=AuditResponse, tags=["Audits"])
async def run_audit(audit_data: AuditCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Lance un audit de conformité sur un routeur."""
    router = db.query(Router).filter(Router.id == audit_data.router_id).first()
    if not router:
        raise HTTPException(status_code=404, detail="Routeur non trouvé")

    # Créer l'audit
    audit = Audit(
        router_id=router.id,
        status=AuditStatus.RUNNING,
        remediation_mode=RemediationMode(audit_data.remediation_mode),
        started_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    # Exécuter l'audit (synchrone pour la simplicité)
    import time
    start = time.time()

    mikrotik = MikrotikService(
        host=router.ip_address,
        username=router.username,
        password=router.password or "",
        api_port=router.api_port,
    )

    # Récupérer le template
    template_yaml = None
    if router.template_id:
        template = db.query(Template).filter(Template.id == router.template_id).first()
        if template:
            template_yaml = template.yaml_content

    engine = ComplianceEngine(mikrotik, template_yaml)
    result = engine.run_audit()

    audit.status = AuditStatus.COMPLETED
    audit.compliance_status = ComplianceStatus(result.status)
    audit.compliance_score = result.score
    audit.checks = [c.to_dict() for c in result.checks]
    audit.anomalies = [c.to_dict() for c in result.checks if c.status.value != 'compliant']
    audit.completed_at = datetime.utcnow()
    audit.duration_seconds = time.time() - start

    # Génération des commandes de remédiation si mode > 1
    if audit.remediation_mode in (RemediationMode.AUDIT_AND_PROPOSE, RemediationMode.AUDIT_AND_FIX):
        remediations = engine.generate_remediation(result)
        audit.remediation_commands = remediations

        if audit.remediation_mode == RemediationMode.AUDIT_AND_FIX:
            # Auto-remédiation
            audit.remediation_applied = True
            remediation_result = {'applied': len(remediations), 'commands': remediations}
            audit.remediation_result = remediation_result

            # Revalidation
            result2 = engine.run_audit()
            audit.compliance_score = result2.score
            audit.compliance_status = ComplianceStatus(result2.status)
            audit.checks = [c.to_dict() for c in result2.checks]

    # Mise à jour du routeur
    router.compliance_status = audit.compliance_status
    router.compliance_score = audit.compliance_score
    router.last_audit_at = datetime.utcnow()

    # Génération d'alertes si non conforme
    if audit.compliance_status == ComplianceStatus.NON_COMPLIANT:
        alert_service = AlertService(db)
        alert_service.create_alert('non_compliant', router, custom_data={
            'audit_id': audit.id,
            'score': audit.compliance_score,
        })

    db.commit()
    db.refresh(audit)

    return audit


@app.get("/api/audits", response_model=List[AuditResponse], tags=["Audits"])
async def list_audits(
    router_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Audit)
    if router_id:
        query = query.filter(Audit.router_id == router_id)
    return query.order_by(Audit.created_at.desc()).offset(skip).limit(limit).all()


@app.get("/api/audits/{audit_id}", response_model=AuditResponse, tags=["Audits"])
async def get_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit


@app.get("/api/routers/{router_id}/audits", response_model=List[AuditResponse], tags=["Audits"])
async def get_router_audits(router_id: str, db: Session = Depends(get_db)):
    return db.query(Audit).filter(
        Audit.router_id == router_id
    ).order_by(Audit.created_at.desc()).all()


# ==================== ALERTES ====================

@app.get("/api/alerts", response_model=List[AlertResponse], tags=["Alerts"])
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    router_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if router_id:
        query = query.filter(Alert.router_id == router_id)
    return query.order_by(Alert.created_at.desc()).all()


@app.post("/api/alerts", response_model=AlertResponse, tags=["Alerts"])
async def create_alert(alert_data: AlertCreate, db: Session = Depends(get_db)):
    alert_service = AlertService(db)
    router = None
    if alert_data.router_id:
        router = db.query(Router).filter(Router.id == alert_data.router_id).first()
    return alert_service.create_alert(
        alert_type=alert_data.title.lower().replace(' ', '_'),
        router=router,
        description=alert_data.description,
        custom_data={'category': alert_data.category},
    )


@app.post("/api/alerts/{alert_id}/resolve", response_model=AlertResponse, tags=["Alerts"])
async def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    alert_service = AlertService(db)
    alert = alert_service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    return alert


@app.post("/api/alerts/{alert_id}/acknowledge", response_model=AlertResponse, tags=["Alerts"])
async def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    alert_service = AlertService(db)
    alert = alert_service.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    return alert


@app.post("/api/alerts/{alert_id}/notify", tags=["Alerts"])
async def notify_alert(alert_id: str, channels: Optional[List[str]] = None, db: Session = Depends(get_db)):
    """Envoie une notification pour une alerte."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    notification_service = NotificationService(db)
    return notification_service.send_notification(alert, channels)


# ==================== CLIENTS ====================

@app.get("/api/clients", response_model=List[ClientResponse], tags=["Clients"])
async def list_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()


@app.post("/api/clients", response_model=ClientResponse, tags=["Clients"])
async def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**client_data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.get("/api/clients/{client_id}", response_model=ClientResponse, tags=["Clients"])
async def get_client(client_id: str, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client


@app.put("/api/clients/{client_id}", response_model=ClientResponse, tags=["Clients"])
async def update_client(client_id: str, client_data: ClientUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    for key, value in client_data.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


# ==================== SITES ====================

@app.get("/api/sites", response_model=List[SiteResponse], tags=["Sites"])
async def list_sites(client_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Site)
    if client_id:
        query = query.filter(Site.client_id == client_id)
    return query.all()


@app.post("/api/sites", response_model=SiteResponse, tags=["Sites"])
async def create_site(site_data: SiteCreate, db: Session = Depends(get_db)):
    site = Site(**site_data.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@app.get("/api/sites/{site_id}", response_model=SiteResponse, tags=["Sites"])
async def get_site(site_id: str, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return site


# ==================== TEMPLATES ====================

@app.get("/api/templates", response_model=List[TemplateResponse], tags=["Templates"])
async def list_templates(db: Session = Depends(get_db)):
    return db.query(Template).all()


@app.post("/api/templates", response_model=TemplateResponse, tags=["Templates"])
async def create_template(template_data: TemplateCreate, db: Session = Depends(get_db)):
    if db.query(Template).filter(Template.model == template_data.model).first():
        raise HTTPException(status_code=400, detail="Un template pour ce modèle existe déjà")
    template = Template(**template_data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@app.get("/api/templates/{template_id}", response_model=TemplateResponse, tags=["Templates"])
async def get_template(template_id: str, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@app.put("/api/templates/{template_id}", response_model=TemplateResponse, tags=["Templates"])
async def update_template(template_id: str, template_data: TemplateUpdate, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    for key, value in template_data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


@app.delete("/api/templates/{template_id}", tags=["Templates"])
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    db.delete(template)
    db.commit()
    return {"message": "Template supprimé"}


# ==================== SANTÉ ====================

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "msp-backend", "version": settings.APP_VERSION}


@app.get("/api/system/info", tags=["System"])
async def system_info():
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "templates_dir": settings.TEMPLATES_DIR,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
