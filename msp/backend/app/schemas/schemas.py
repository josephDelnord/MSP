from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# Client Schemas
class ClientBase(BaseModel):
    name: str
    reference_crm: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    reference_crm: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Site Schemas
class SiteBase(BaseModel):
    client_id: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "France"
    vlan: Optional[int] = None
    ip_lan: Optional[str] = None
    ip_wan: Optional[str] = None
    is_active: bool = True


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    vlan: Optional[int] = None
    ip_lan: Optional[str] = None
    ip_wan: Optional[str] = None
    is_active: Optional[bool] = None


class SiteResponse(SiteBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Template Schemas
class TemplateBase(BaseModel):
    name: str
    model: str
    description: Optional[str] = None
    rsc_content: Optional[str] = None
    yaml_content: Optional[str] = None
    variables_schema: Optional[Dict[str, Any]] = None
    target_routeros_version: Optional[str] = None
    target_routerboard_firmware: Optional[str] = None
    target_lte_firmware: Optional[str] = None
    is_active: bool = True


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    description: Optional[str] = None
    rsc_content: Optional[str] = None
    yaml_content: Optional[str] = None
    variables_schema: Optional[Dict[str, Any]] = None
    target_routeros_version: Optional[str] = None
    target_routerboard_firmware: Optional[str] = None
    target_lte_firmware: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Router Schemas
class RouterBase(BaseModel):
    hostname: str
    ip_address: str
    client_id: Optional[str] = None
    site_id: Optional[str] = None
    template_id: Optional[str] = None
    api_port: int = 8728
    ssh_port: int = 22
    api_ssl_port: int = 8729
    username: str = "admin"
    password: Optional[str] = None
    pppoe_login: Optional[str] = None
    pppoe_password: Optional[str] = None
    ssid_2ghz: Optional[str] = None
    ssid_5ghz: Optional[str] = None
    wifi_key: Optional[str] = None


class RouterCreate(RouterBase):
    pass


class RouterUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    client_id: Optional[str] = None
    site_id: Optional[str] = None
    template_id: Optional[str] = None
    api_port: Optional[int] = None
    ssh_port: Optional[int] = None
    api_ssl_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    pppoe_login: Optional[str] = None
    pppoe_password: Optional[str] = None
    ssid_2ghz: Optional[str] = None
    ssid_5ghz: Optional[str] = None
    wifi_key: Optional[str] = None


class RouterDiscoveryRequest(BaseModel):
    ip_address: str = "192.168.88.1"
    username: str = "admin"
    password: str = ""
    api_port: int = 8728


class RouterResponse(RouterBase):
    id: str
    model: Optional[str] = None
    hardware_revision: Optional[str] = None
    serial_number: Optional[str] = None
    cpu_architecture: Optional[str] = None
    mac_ether2: Optional[str] = None
    mac_main: Optional[str] = None
    routeros_version: Optional[str] = None
    routerboard_firmware: Optional[str] = None
    lte_firmware: Optional[str] = None
    routeros_target_version: Optional[str] = None
    status: str
    compliance_status: str
    compliance_score: float
    is_discovered: bool
    is_provisioned: bool
    last_seen: Optional[datetime] = None
    last_audit_at: Optional[datetime] = None
    last_provisioning_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Audit Schemas
class AuditCheckResult(BaseModel):
    name: str
    category: str
    status: str  # compliant, warning, non_compliant
    expected: Optional[str] = None
    found: Optional[str] = None
    severity: str
    explanation: Optional[str] = None


class AuditCreate(BaseModel):
    router_id: str
    remediation_mode: str = "audit_only"


class AuditResponse(BaseModel):
    id: str
    router_id: str
    status: str
    compliance_status: str
    compliance_score: float
    checks: Optional[List[Dict[str, Any]]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    remediation_mode: str
    remediation_commands: Optional[List[Dict[str, Any]]] = None
    remediation_applied: bool
    remediation_result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Alert Schemas
class AlertCreate(BaseModel):
    router_id: Optional[str] = None
    severity: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    router_id: Optional[str] = None
    severity: str
    status: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_notified: bool
    notified_at: Optional[datetime] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Firmware Update Schemas
class FirmwareUpdateResponse(BaseModel):
    id: str
    router_id: str
    update_type: str
    old_version: Optional[str] = None
    new_version: Optional[str] = None
    status: str
    result: Optional[str] = None
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_routers: int
    online_routers: int
    offline_routers: int
    non_compliant_routers: int
    error_routers: int
    outdated_routers: int
    active_alerts: int
    critical_alerts: int


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "viewer"
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str
