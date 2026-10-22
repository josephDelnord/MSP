import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Button, Card, CardContent, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, IconButton, Tooltip, LinearProgress,
  Tabs, Tab, Paper, Alert as MuiAlert, CircularProgress,
  Accordion, AccordionSummary, AccordionDetails,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  PlayArrow as ProvisionIcon,
  Assessment as AuditIcon,
  SystemUpdate as UpdateIcon,
  Search as DiscoverIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { routersApi, auditsApi, templatesApi } from '../services/api';
import type { Router, Audit, Template, DiscoveryResult, ProvisioningResult } from '../types';

const Routers: React.FC = () => {
  const [routers, setRouters] = useState<Router[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRouter, setSelectedRouter] = useState<Router | null>(null);
  const [audits, setAudits] = useState<Audit[]>([]);
  const [detailTab, setDetailTab] = useState(0);

  // Dialogs
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [discoverDialogOpen, setDiscoverDialogOpen] = useState(false);
  const [provisionDialogOpen, setProvisionDialogOpen] = useState(false);
  const [auditDialogOpen, setAuditDialogOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionResult, setActionResult] = useState<any>(null);

  // Forms
  const [newRouter, setNewRouter] = useState({ hostname: '', ip_address: '', username: 'admin', password: '' });
  const [discoveryForm, setDiscoveryForm] = useState({ ip_address: '192.168.88.1', username: 'admin', password: '', api_port: 8728 });
  const [provisionVariables, setProvisionVariables] = useState<Record<string, string>>({});

  const fetchRouters = async () => {
    setLoading(true);
    try {
      const data = await routersApi.list();
      setRouters(data);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const data = await templatesApi.list();
      setTemplates(data);
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const fetchAudits = async (routerId: string) => {
    try {
      const data = await auditsApi.getRouterAudits(routerId);
      setAudits(data);
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  useEffect(() => {
    fetchRouters();
    fetchTemplates();
  }, []);

  const handleSelectRouter = (router: Router) => {
    setSelectedRouter(router);
    setDetailTab(0);
    setActionResult(null);
    fetchAudits(router.id);
  };

  const handleAddRouter = async () => {
    try {
      await routersApi.create(newRouter);
      setAddDialogOpen(false);
      setNewRouter({ hostname: '', ip_address: '', username: 'admin', password: '' });
      fetchRouters();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const handleDiscover = async () => {
    setActionLoading(true);
    setActionResult(null);
    try {
      const result = await routersApi.discover(discoveryForm);
      setActionResult({ type: 'discovery', data: result });
      fetchRouters();
    } catch (error: any) {
      setActionResult({ type: 'error', message: error.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleProvision = async () => {
    if (!selectedRouter) return;
    setActionLoading(true);
    setActionResult(null);
    try {
      const result = await routersApi.provision(selectedRouter.id, provisionVariables);
      setActionResult({ type: 'provision', data: result });
      fetchRouters();
    } catch (error: any) {
      setActionResult({ type: 'error', message: error.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleAudit = async (mode: string = 'audit_only') => {
    if (!selectedRouter) return;
    setActionLoading(true);
    setActionResult(null);
    try {
      const result = await auditsApi.run(selectedRouter.id, mode);
      setActionResult({ type: 'audit', data: result });
      fetchRouters();
      fetchAudits(selectedRouter.id);
    } catch (error: any) {
      setActionResult({ type: 'error', message: error.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateFirmware = async (type: string) => {
    if (!selectedRouter) return;
    setActionLoading(true);
    try {
      const result = await routersApi.updateFirmware(selectedRouter.id, type);
      setActionResult({ type: 'update', data: result });
      fetchRouters();
    } catch (error: any) {
      setActionResult({ type: 'error', message: error.message });
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'success';
      case 'offline': return 'error';
      case 'provisioning': return 'info';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'success';
      case 'compliant_with_warnings': return 'warning';
      case 'non_compliant': return 'error';
      default: return 'default';
    }
  };

  const columns: GridColDef[] = [
    { field: 'hostname', headerName: 'Hostname', flex: 1, minWidth: 150 },
    { field: 'ip_address', headerName: 'Adresse IP', width: 130 },
    { field: 'model', headerName: 'Modèle', width: 120 },
    {
      field: 'status',
      headerName: 'Statut',
      width: 110,
      renderCell: (params) => (
        <Chip size="small" label={params.value} color={getStatusColor(params.value) as any} />
      ),
    },
    {
      field: 'compliance_status',
      headerName: 'Conformité',
      width: 140,
      renderCell: (params) => (
        <Chip size="small" label={params.value} color={getComplianceColor(params.value) as any} />
      ),
    },
    {
      field: 'compliance_score',
      headerName: 'Score',
      width: 100,
      renderCell: (params) => (
        <Box sx={{ width: '100%' }}>
          <LinearProgress
            variant="determinate"
            value={params.value}
            color={params.value >= 95 ? 'success' : params.value >= 70 ? 'warning' : 'error'}
          />
          <Typography variant="caption">{params.value}%</Typography>
        </Box>
      ),
    },
    { field: 'routeros_version', headerName: 'RouterOS', width: 100 },
    { field: 'serial_number', headerName: 'N° Série', width: 120 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Routeurs</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<DiscoverIcon />} onClick={() => setDiscoverDialogOpen(true)}>
            Découvrir
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setAddDialogOpen(true)}>
            Ajouter
          </Button>
          <IconButton onClick={fetchRouters}><RefreshIcon /></IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Liste des routeurs */}
        <Grid item xs={12} lg={selectedRouter ? 7 : 12}>
          <Paper sx={{ height: 600 }}>
            <DataGrid
              rows={routers}
              columns={columns}
              loading={loading}
              onRowClick={(params) => handleSelectRouter(params.row)}
              sx={{
                border: 'none',
                '& .MuiDataGrid-row': { cursor: 'pointer' },
                '& .MuiDataGrid-row.Mui-selected': { bgcolor: 'action.selected' },
              }}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              pageSizeOptions={[10, 25, 50]}
            />
          </Paper>
        </Grid>

        {/* Détail routeur */}
        {selectedRouter && (
          <Grid item xs={12} lg={5}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>{selectedRouter.hostname}</Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                  <Chip label={selectedRouter.status} color={getStatusColor(selectedRouter.status) as any} size="small" />
                  <Chip label={selectedRouter.compliance_status} color={getComplianceColor(selectedRouter.compliance_status) as any} size="small" />
                  {selectedRouter.model && <Chip label={selectedRouter.model} variant="outlined" size="small" />}
                </Box>

                <Grid container spacing={1} sx={{ mb: 2 }}>
                  <Grid item xs={6}><Typography variant="body2" color="text.secondary">IP</Typography><Typography>{selectedRouter.ip_address}</Typography></Grid>
                  <Grid item xs={6}><Typography variant="body2" color="text.secondary">Série</Typography><Typography>{selectedRouter.serial_number || '-'}</Typography></Grid>
                  <Grid item xs={6}><Typography variant="body2" color="text.secondary">MAC Ether2</Typography><Typography variant="body2">{selectedRouter.mac_ether2 || '-'}</Typography></Grid>
                  <Grid item xs={6}><Typography variant="body2" color="text.secondary">RouterOS</Typography><Typography>{selectedRouter.routeros_version || '-'}</Typography></Grid>
                  <Grid item xs={6}><Typography variant="body2" color="text.secondary">Firmware</Typography><Typography>{selectedRouter.routerboard_firmware || '-'}</Typography></Grid>
                  <Grid item xs={6}><Typography variant="body2" color="text.secondary">Score</Typography><Typography>{selectedRouter.compliance_score}%</Typography></Grid>
                </Grid>

                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  <Button size="small" variant="contained" startIcon={<AuditIcon />} onClick={() => handleAudit('audit_only')} disabled={actionLoading}>
                    Auditer
                  </Button>
                  <Button size="small" variant="outlined" startIcon={<ProvisionIcon />} onClick={() => setProvisionDialogOpen(true)} disabled={actionLoading}>
                    Provisionner
                  </Button>
                  <Button size="small" variant="outlined" startIcon={<UpdateIcon />} onClick={() => handleUpdateFirmware('routeros')} disabled={actionLoading}>
                    Mise à jour
                  </Button>
                </Box>

                {actionLoading && <LinearProgress sx={{ mb: 2 }} />}

                {actionResult && (
                  <MuiAlert severity={actionResult.type === 'error' ? 'error' : 'success'} sx={{ mb: 2 }}>
                    {actionResult.type === 'error' ? actionResult.message : 'Action réussie'}
                  </MuiAlert>
                )}

                <Tabs value={detailTab} onChange={(_, v) => setDetailTab(v)}>
                  <Tab label="Audits" />
                  <Tab label="Détails" />
                </Tabs>

                {detailTab === 0 && (
                  <Box sx={{ mt: 2 }}>
                    {audits.length === 0 ? (
                      <Typography color="text.secondary">Aucun audit</Typography>
                    ) : (
                      audits.slice(0, 5).map((audit) => (
                        <Accordion key={audit.id} disableGutters>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                              {audit.compliance_status === 'compliant' ? <CheckIcon color="success" fontSize="small" /> :
                               audit.compliance_status === 'compliant_with_warnings' ? <WarningIcon color="warning" fontSize="small" /> :
                               <ErrorIcon color="error" fontSize="small" />}
                              <Typography variant="body2" sx={{ flexGrow: 1 }}>
                                {new Date(audit.created_at).toLocaleString('fr-FR')}
                              </Typography>
                              <Chip size="small" label={`${audit.compliance_score}%`} />
                            </Box>
                          </AccordionSummary>
                          <AccordionDetails>
                            {audit.checks && audit.checks.length > 0 && (
                              <Box>
                                {audit.checks.map((check, idx) => (
                                  <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.5 }}>
                                    {check.status === 'compliant' ? <CheckIcon color="success" fontSize="small" /> :
                                     check.status === 'warning' ? <WarningIcon color="warning" fontSize="small" /> :
                                     <ErrorIcon color="error" fontSize="small" />}
                                    <Typography variant="body2" sx={{ flexGrow: 1 }}>{check.name}</Typography>
                                    <Typography variant="caption" color="text.secondary">{check.category}</Typography>
                                  </Box>
                                ))}
                              </Box>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      ))
                    )}
                  </Box>
                )}

                {detailTab === 1 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2"><strong>PPPoE Login:</strong> {selectedRouter.pppoe_login || '-'}</Typography>
                    <Typography variant="body2"><strong>SSID 2.4:</strong> {selectedRouter.ssid_2ghz || '-'}</Typography>
                    <Typography variant="body2"><strong>SSID 5:</strong> {selectedRouter.ssid_5ghz || '-'}</Typography>
                    <Typography variant="body2"><strong>Découvert:</strong> {selectedRouter.is_discovered ? 'Oui' : 'Non'}</Typography>
                    <Typography variant="body2"><strong>Provisionné:</strong> {selectedRouter.is_provisioned ? 'Oui' : 'Non'}</Typography>
                    <Typography variant="body2"><strong>Dernière vue:</strong> {selectedRouter.last_seen ? new Date(selectedRouter.last_seen).toLocaleString('fr-FR') : '-'}</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Dialog Ajouter */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Ajouter un routeur</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="normal" label="Hostname" value={newRouter.hostname} onChange={(e) => setNewRouter({ ...newRouter, hostname: e.target.value })} />
          <TextField fullWidth margin="normal" label="Adresse IP" value={newRouter.ip_address} onChange={(e) => setNewRouter({ ...newRouter, ip_address: e.target.value })} />
          <TextField fullWidth margin="normal" label="Username" value={newRouter.username} onChange={(e) => setNewRouter({ ...newRouter, username: e.target.value })} />
          <TextField fullWidth margin="normal" label="Password" type="password" value={newRouter.password} onChange={(e) => setNewRouter({ ...newRouter, password: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Annuler</Button>
          <Button variant="contained" onClick={handleAddRouter}>Ajouter</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Découverte */}
      <Dialog open={discoverDialogOpen} onClose={() => { setDiscoverDialogOpen(false); setActionResult(null); }} maxWidth="sm" fullWidth>
        <DialogTitle>Découverte automatique</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Connectez-vous à un routeur Mikrotik neuf ou réinitialisé (192.168.88.1 par défaut)
          </Typography>
          <TextField fullWidth margin="normal" label="Adresse IP" value={discoveryForm.ip_address} onChange={(e) => setDiscoveryForm({ ...discoveryForm, ip_address: e.target.value })} />
          <TextField fullWidth margin="normal" label="Username" value={discoveryForm.username} onChange={(e) => setDiscoveryForm({ ...discoveryForm, username: e.target.value })} />
          <TextField fullWidth margin="normal" label="Password" type="password" value={discoveryForm.password} onChange={(e) => setDiscoveryForm({ ...discoveryForm, password: e.target.value })} />
          <TextField fullWidth margin="normal" label="Port API" type="number" value={discoveryForm.api_port} onChange={(e) => setDiscoveryForm({ ...discoveryForm, api_port: parseInt(e.target.value) })} />

          {actionLoading && <LinearProgress sx={{ mt: 2 }} />}

          {actionResult?.type === 'discovery' && (
            <MuiAlert severity={actionResult.data.template_found ? 'success' : 'warning'} sx={{ mt: 2 }}>
              <Typography variant="body2"><strong>Modèle:</strong> {actionResult.data.model}</Typography>
              <Typography variant="body2"><strong>Numéro de série:</strong> {actionResult.data.serial_number}</Typography>
              <Typography variant="body2"><strong>RouterOS:</strong> {actionResult.data.routeros_version}</Typography>
              <Typography variant="body2"><strong>Template:</strong> {actionResult.data.template_found ? actionResult.data.template_name : 'NON TROUVÉ'}</Typography>
            </MuiAlert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDiscoverDialogOpen(false); setActionResult(null); }}>Fermer</Button>
          <Button variant="contained" onClick={handleDiscover} disabled={actionLoading}>Découvrir</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Provisionnement */}
      <Dialog open={provisionDialogOpen} onClose={() => { setProvisionDialogOpen(false); setActionResult(null); }} maxWidth="md" fullWidth>
        <DialogTitle>Provisionnement - {selectedRouter?.hostname}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Le provisioning va: vérifier les mises à jour, importer le template, appliquer la configuration et redémarrer le routeur.
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Hostname" defaultValue={selectedRouter?.hostname} onChange={(e) => setProvisionVariables(v => ({ ...v, hostname: e.target.value }))} size="small" margin="dense" />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="SSID 2.4 GHz" defaultValue={selectedRouter?.ssid_2ghz} onChange={(e) => setProvisionVariables(v => ({ ...v, ssid_2ghz: e.target.value }))} size="small" margin="dense" />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="SSID 5 GHz" defaultValue={selectedRouter?.ssid_5ghz} onChange={(e) => setProvisionVariables(v => ({ ...v, ssid_5ghz: e.target.value }))} size="small" margin="dense" />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="PPPoE Login" defaultValue={selectedRouter?.pppoe_login} onChange={(e) => setProvisionVariables(v => ({ ...v, pppoe_login: e.target.value }))} size="small" margin="dense" />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="PPPoE Password" type="password" onChange={(e) => setProvisionVariables(v => ({ ...v, pppoe_password: e.target.value }))} size="small" margin="dense" />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="WiFi Key" type="password" onChange={(e) => setProvisionVariables(v => ({ ...v, wifi_key: e.target.value }))} size="small" margin="dense" />
            </Grid>
          </Grid>

          {actionLoading && <LinearProgress sx={{ mt: 2 }} />}

          {actionResult?.type === 'provision' && (
            <Box sx={{ mt: 2 }}>
              <MuiAlert severity={actionResult.data.success ? 'success' : 'error'}>
                {actionResult.data.success ? 'Provisionnement réussi' : actionResult.data.error}
              </MuiAlert>
              {actionResult.data.steps?.map((step: any, idx: number) => (
                <Typography key={idx} variant="body2" sx={{ mt: 0.5 }}>
                  [{step.status}] {step.step}: {step.message}
                </Typography>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setProvisionDialogOpen(false); setActionResult(null); }}>Fermer</Button>
          <Button variant="contained" color="warning" onClick={handleProvision} disabled={actionLoading}>
            Lancer le provisioning
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Routers;
