import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


# Enums
class RouterStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    PROVISIONING = "provisioning"
    ERROR = "error"
    UNKNOWN = "unknown"


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "compliant"
    COMPLIANT_WITH_WARNINGS = "compliant_with_warnings"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AuditStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RemediationMode(str, enum.Enum):
    AUDIT_ONLY = "audit_only"
    AUDIT_AND_PROPOSE = "audit_and_purpose"
    AUDIT_AND_FIX = "audit_and_fix"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    reference_crm = Column(String(100), unique=True, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sites = relationship("Site", back_populates="client")
    routers = relationship("Router", back_populates="client")


class Site(Base):
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    client_id = Column(UUID(as_uuid=False), ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="France")
    vlan = Column(Integer, nullable=True)
    ip_lan = Column(String(50), nullable=True)
    ip_wan = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="sites")
    routers = relationship("Router", back_populates="site")


class Router(Base):
    __tablename__ = "routers"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    client_id = Column(UUID(as_uuid=False), ForeignKey("clients.id"), nullable=True)
    site_id = Column(UUID(as_uuid=False), ForeignKey("sites.id"), nullable=True)
    template_id = Column(UUID(as_uuid=False), ForeignKey("templates.id"), nullable=True)

    # Identification
    hostname = Column(String(255), nullable=False, unique=True)
    model = Column(String(100), nullable=True)
    hardware_revision = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True, unique=True)
    cpu_architecture = Column(String(50), nullable=True)
    mac_ether2 = Column(String(17), nullable=True)
    mac_main = Column(String(17), nullable=True)

    # Network
    ip_address = Column(String(50), nullable=False)
    api_port = Column(Integer, default=8728)
    ssh_port = Column(Integer, default=22)
    api_ssl_port = Column(Integer, default=8729)

    # Credentials (stored encrypted in production)
    username = Column(String(100), default="admin")
    password = Column(String(255), nullable=True)

    # Versions
    routeros_version = Column(String(50), nullable=True)
    routerboard_firmware = Column(String(50), nullable=True)
    lte_firmware = Column(String(50), nullable=True)
    routeros_target_version = Column(String(50), nullable=True)

    # PPPoE
    pppoe_login = Column(String(255), nullable=True)
    pppoe_password = Column(String(255), nullable=True)

    # WiFi
    ssid_2ghz = Column(String(100), nullable=True)
    ssid_5ghz = Column(String(100), nullable=True)
    wifi_key = Column(String(255), nullable=True)

    # Status
    status = Column(SQLEnum(RouterStatus), default=RouterStatus.UNKNOWN)
    compliance_status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.UNKNOWN)
    compliance_score = Column(Float, default=0.0)

    # Discovery & Provisioning
    is_discovered = Column(Boolean, default=False)
    is_provisioned = Column(Boolean, default=False)
    last_seen = Column(DateTime, nullable=True)
    last_audit_at = Column(DateTime, nullable=True)
    last_provisioning_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="routers")
    site = relationship("Site", back_populates="routers")
    template = relationship("Template", back_populates="routers")
    audits = relationship("Audit", back_populates="router", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="router", cascade="all, delete-orphan")
    updates = relationship("FirmwareUpdate", back_populates="router", cascade="all, delete-orphan")


class Template(Base):
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    model = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Template files
    rsc_content = Column(Text, nullable=True)
    yaml_content = Column(Text, nullable=True)

    # Variables schema (JSON)
    variables_schema = Column(JSON, nullable=True)

    # Target versions
    target_routeros_version = Column(String(50), nullable=True)
    target_routerboard_firmware = Column(String(50), nullable=True)
    target_lte_firmware = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    routers = relationship("Router", back_populates="template")


class Audit(Base):
    __tablename__ = "audits"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    router_id = Column(UUID(as_uuid=False), ForeignKey("routers.id"), nullable=False)

    status = Column(SQLEnum(AuditStatus), default=AuditStatus.PENDING)
    compliance_status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.UNKNOWN)
    compliance_score = Column(Float, default=0.0)

    # Results (JSON)
    checks = Column(JSON, nullable=True)
    anomalies = Column(JSON, nullable=True)

    # Remediation
    remediation_mode = Column(SQLEnum(RemediationMode), default=RemediationMode.AUDIT_ONLY)
    remediation_commands = Column(JSON, nullable=True)
    remediation_applied = Column(Boolean, default=False)
    remediation_result = Column(JSON, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    router = relationship("Router", back_populates="audits")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    router_id = Column(UUID(as_uuid=False), ForeignKey("routers.id"), nullable=True)

    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)

    # Notification tracking
    is_notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)
    notification_channels = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    router = relationship("Router", back_populates="alerts")


class FirmwareUpdate(Base):
    __tablename__ = "firmware_updates"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    router_id = Column(UUID(as_uuid=False), ForeignKey("routers.id"), nullable=False)

    update_type = Column(String(50), nullable=False)  # routeros, routerboard, lte
    old_version = Column(String(50), nullable=True)
    new_version = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False)  # pending, downloading, installing, completed, failed
    result = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    router = relationship("Router", back_populates="updates")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Entra ID
    entra_id_object_id = Column(String(100), nullable=True, unique=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
