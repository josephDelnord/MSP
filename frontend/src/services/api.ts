import axios from 'axios';
import type {
  Router, Client, Site, Template, Audit, Alert,
  DashboardStats, User, DiscoveryResult, ProvisioningResult,
  FirmwareUpdate,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('msp_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur pour gérer les erreurs 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('msp_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const { data } = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },
  me: async (): Promise<User> => {
    const { data } = await api.get('/auth/me');
    return data;
  },
};

// Dashboard API
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const { data } = await api.get('/dashboard/stats');
    return data;
  },
  getRoutersStatus: async () => {
    const { data } = await api.get('/dashboard/routers-status');
    return data;
  },
};

// Routers API
export const routersApi = {
  list: async (params?: { status?: string; client_id?: string }): Promise<Router[]> => {
    const { data } = await api.get('/routers', { params });
    return data;
  },
  get: async (id: string): Promise<Router> => {
    const { data } = await api.get(`/routers/${id}`);
    return data;
  },
  create: async (router: Partial<Router>): Promise<Router> => {
    const { data } = await api.post('/routers', router);
    return data;
  },
  update: async (id: string, router: Partial<Router>): Promise<Router> => {
    const { data } = await api.put(`/routers/${id}`, router);
    return data;
  },
  delete: async (id: string) => {
    await api.delete(`/routers/${id}`);
  },
  discover: async (discovery: { ip_address: string; username: string; password: string; api_port?: number }): Promise<DiscoveryResult> => {
    const { data } = await api.post('/routers/discover', discovery);
    return data;
  },
  provision: async (id: string, variables?: Record<string, string>): Promise<ProvisioningResult> => {
    const { data } = await api.post(`/routers/${id}/provision`, variables);
    return data;
  },
  updateFirmware: async (id: string, updateType: string): Promise<FirmwareUpdate> => {
    const { data } = await api.post(`/routers/${id}/update?update_type=${updateType}`);
    return data;
  },
  getUpdates: async (id: string): Promise<FirmwareUpdate[]> => {
    const { data } = await api.get(`/routers/${id}/updates`);
    return data;
  },
};

// Audits API
export const auditsApi = {
  list: async (routerId?: string): Promise<Audit[]> => {
    const { data } = await api.get('/audits', { params: { router_id: routerId } });
    return data;
  },
  get: async (id: string): Promise<Audit> => {
    const { data } = await api.get(`/audits/${id}`);
    return data;
  },
  run: async (routerId: string, remediationMode: string = 'audit_only'): Promise<Audit> => {
    const { data } = await api.post('/audits', {
      router_id: routerId,
      remediation_mode: remediationMode,
    });
    return data;
  },
  getRouterAudits: async (routerId: string): Promise<Audit[]> => {
    const { data } = await api.get(`/routers/${routerId}/audits`);
    return data;
  },
};

// Alerts API
export const alertsApi = {
  list: async (params?: { status?: string; severity?: string; router_id?: string }): Promise<Alert[]> => {
    const { data } = await api.get('/alerts', { params });
    return data;
  },
  create: async (alert: { severity: string; title: string; description?: string; router_id?: string }): Promise<Alert> => {
    const { data } = await api.post('/alerts', alert);
    return data;
  },
  resolve: async (id: string): Promise<Alert> => {
    const { data } = await api.post(`/alerts/${id}/resolve`);
    return data;
  },
  acknowledge: async (id: string): Promise<Alert> => {
    const { data } = await api.post(`/alerts/${id}/acknowledge`);
    return data;
  },
  notify: async (id: string, channels?: string[]) => {
    const { data } = await api.post(`/alerts/${id}/notify`, channels);
    return data;
  },
};

// Clients API
export const clientsApi = {
  list: async (): Promise<Client[]> => {
    const { data } = await api.get('/clients');
    return data;
  },
  create: async (client: Partial<Client>): Promise<Client> => {
    const { data } = await api.post('/clients', client);
    return data;
  },
  get: async (id: string): Promise<Client> => {
    const { data } = await api.get(`/clients/${id}`);
    return data;
  },
  update: async (id: string, client: Partial<Client>): Promise<Client> => {
    const { data } = await api.put(`/clients/${id}`, client);
    return data;
  },
};

// Sites API
export const sitesApi = {
  list: async (clientId?: string): Promise<Site[]> => {
    const { data } = await api.get('/sites', { params: { client_id: clientId } });
    return data;
  },
  create: async (site: Partial<Site>): Promise<Site> => {
    const { data } = await api.post('/sites', site);
    return data;
  },
  get: async (id: string): Promise<Site> => {
    const { data } = await api.get(`/sites/${id}`);
    return data;
  },
};

// Templates API
export const templatesApi = {
  list: async (): Promise<Template[]> => {
    const { data } = await api.get('/templates');
    return data;
  },
  create: async (template: Partial<Template>): Promise<Template> => {
    const { data } = await api.post('/templates', template);
    return data;
  },
  get: async (id: string): Promise<Template> => {
    const { data } = await api.get(`/templates/${id}`);
    return data;
  },
  update: async (id: string, template: Partial<Template>): Promise<Template> => {
    const { data } = await api.put(`/templates/${id}`, template);
    return data;
  },
  delete: async (id: string) => {
    await api.delete(`/templates/${id}`);
  },
};

// System API
export const systemApi = {
  health: async () => {
    const { data } = await api.get('/health');
    return data;
  },
  info: async () => {
    const { data } = await api.get('/system/info');
    return data;
  },
};

export default api;
