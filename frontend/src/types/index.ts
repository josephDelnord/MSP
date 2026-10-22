// Types pour l'application MSP

export interface Router {
  id: string;
  hostname: string;
  ip_address: string;
  model?: string;
  hardware_revision?: string;
  serial_number?: string;
  cpu_architecture?: string;
  mac_main?: string;
  mac_ether2?: string;
  routeros_version?: string;
  routerboard_firmware?: string;
  lte_firmware?: string;
  routeros_target_version?: string;
  status: 'online' | 'offline' | 'provisioning' | 'error' | 'unknown';
  compliance_status: 'compliant' | 'compliant_with_warnings' | 'non_compliant' | 'unknown';
  compliance_score: number;
  is_discovered: boolean;
  is_provisioned: boolean;
  last_seen?: string;
  last_audit_at?: string;
  last_provisioning_at?: string;
  client_id?: string;
  site_id?: string;
  template_id?: string;
  pppoe_login?: string;
  ssid_2ghz?: string;
  ssid_5ghz?: string;
  created_at: string;
  updated_at: string;
}

export interface Client {
  id: string;
  name: string;
  reference_crm?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Site {
  id: string;
  client_id: string;
  name: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country: string;
  vlan?: number;
  ip_lan?: string;
  ip_wan?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Template {
  id: string;
  name: string;
  model: string;
  description?: string;
  rsc_content?: string;
  yaml_content?: string;
  target_routeros_version?: string;
  target_routerboard_firmware?: string;
  target_lte_firmware?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditCheck {
  name: string;
  category: string;
  status: 'compliant' | 'warning' | 'non_compliant' | 'missing';
  expected?: string;
  found?: string;
  severity: string;
  explanation?: string;
  remediation_commands?: string[];
}

export interface Audit {
  id: string;
  router_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  compliance_status: string;
  compliance_score: number;
  checks?: AuditCheck[];
  anomalies?: AuditCheck[];
  remediation_mode: string;
  remediation_commands?: any[];
  remediation_applied: boolean;
  remediation_result?: any;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  created_at: string;
}

export interface Alert {
  id: string;
  router_id?: string;
  severity: 'info' | 'warning' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved';
  title: string;
  description?: string;
  category?: string;
  is_notified: boolean;
  notified_at?: string;
  created_at: string;
  resolved_at?: string;
}

export interface FirmwareUpdate {
  id: string;
  router_id: string;
  update_type: string;
  old_version?: string;
  new_version?: string;
  status: string;
  result?: string;
  duration_seconds?: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface DashboardStats {
  total_routers: number;
  online_routers: number;
  offline_routers: number;
  non_compliant_routers: number;
  error_routers: number;
  outdated_routers: number;
  active_alerts: number;
  critical_alerts: number;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  last_login?: string;
}

export interface DiscoveryResult {
  ip_address: string;
  model?: string;
  hardware_revision?: string;
  serial_number?: string;
  cpu_architecture?: string;
  hostname?: string;
  mac_main?: string;
  mac_ether2?: string;
  routeros_version?: string;
  routerboard_firmware?: string;
  lte_firmware?: string;
  template_id?: string;
  template_name?: string;
  template_found: boolean;
  router_id?: string;
  discovered_at: string;
}

export interface ProvisioningResult {
  router_id: string;
  hostname: string;
  steps: Array<{ step: string; status: string; message: string }>;
  success: boolean;
  error?: string;
  variables?: Record<string, string>;
}
