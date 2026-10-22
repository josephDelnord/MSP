import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Chip, IconButton, Tooltip,
  Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, Grid, Card, CardContent,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  Refresh as RefreshIcon,
  Check as ResolveIcon,
  Notifications as NotifyIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { alertsApi, routersApi } from '../services/api';
import type { Alert, Router } from '../types';

const Alerts: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [routers, setRouters] = useState<Record<string, Router>>({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('active');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newAlert, setNewAlert] = useState({ title: '', severity: 'warning', description: '', router_id: '' });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [alertsData, routersData] = await Promise.all([
        alertsApi.list({ status: filter === 'all' ? undefined : filter }),
        routersApi.list(),
      ]);
      setAlerts(alertsData);
      const routerMap: Record<string, Router> = {};
      routersData.forEach((r) => { routerMap[r.id] = r; });
      setRouters(routerMap);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filter]);

  const handleResolve = async (id: string) => {
    try {
      await alertsApi.resolve(id);
      fetchData();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const handleNotify = async (id: string) => {
    try {
      await alertsApi.notify(id, ['email', 'webhook']);
      fetchData();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const handleCreate = async () => {
    try {
      await alertsApi.create(newAlert);
      setCreateDialogOpen(false);
      setNewAlert({ title: '', severity: 'warning', description: '', router_id: '' });
      fetchData();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'created_at',
      headerName: 'Date',
      width: 180,
      valueFormatter: (params) => new Date(params.value).toLocaleString('fr-FR'),
    },
    {
      field: 'severity',
      headerName: 'Sévérité',
      width: 100,
      renderCell: (params) => (
        <Chip size="small" label={params.value} color={getSeverityColor(params.value) as any} />
      ),
    },
    {
      field: 'status',
      headerName: 'Statut',
      width: 120,
      renderCell: (params) => (
        <Chip size="small" label={params.value} color={params.value === 'active' ? 'error' : params.value === 'acknowledged' ? 'warning' : 'success'} />
      ),
    },
    { field: 'title', headerName: 'Titre', flex: 1, minWidth: 200 },
    {
      field: 'router',
      headerName: 'Routeur',
      width: 150,
      valueGetter: (params) => params.row.router_id ? routers[params.row.router_id]?.hostname || '-' : '-',
    },
    { field: 'category', headerName: 'Catégorie', width: 120 },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
      sortable: false,
      renderCell: (params) => (
        <Box>
          {params.row.status === 'active' && (
            <>
              <Tooltip title="Notifier">
                <IconButton size="small" onClick={() => handleNotify(params.row.id)}><NotifyIcon fontSize="small" /></IconButton>
              </Tooltip>
              <Tooltip title="Résoudre">
                <IconButton size="small" color="success" onClick={() => handleResolve(params.row.id)}><ResolveIcon fontSize="small" /></IconButton>
              </Tooltip>
            </>
          )}
        </Box>
      ),
    },
  ];

  const stats = {
    total: alerts.length,
    critical: alerts.filter((a) => a.severity === 'critical' && a.status === 'active').length,
    warning: alerts.filter((a) => a.severity === 'warning' && a.status === 'active').length,
    resolved: alerts.filter((a) => a.status === 'resolved').length,
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Alertes</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<AddIcon />} onClick={() => setCreateDialogOpen(true)}>Créer</Button>
          <IconButton onClick={fetchData}><RefreshIcon /></IconButton>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Card><CardContent><Typography color="text.secondary" variant="body2">Total</Typography><Typography variant="h4">{stats.total}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card><CardContent><Typography color="error" variant="body2">Critiques</Typography><Typography variant="h4" color="error">{stats.critical}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card><CardContent><Typography color="warning.main" variant="body2">Warnings</Typography><Typography variant="h4" color="warning.main">{stats.warning}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card><CardContent><Typography color="success.main" variant="body2">Résolues</Typography><Typography variant="h4" color="success.main">{stats.resolved}</Typography></CardContent></Card>
        </Grid>
      </Grid>

      {/* Filtres */}
      <Box sx={{ mb: 2 }}>
        <Chip label="Actives" color={filter === 'active' ? 'primary' : 'default'} onClick={() => setFilter('active')} sx={{ mr: 1 }} />
        <Chip label="Acquittées" color={filter === 'acknowledged' ? 'primary' : 'default'} onClick={() => setFilter('acknowledged')} sx={{ mr: 1 }} />
        <Chip label="Résolues" color={filter === 'resolved' ? 'primary' : 'default'} onClick={() => setFilter('resolved')} sx={{ mr: 1 }} />
        <Chip label="Toutes" color={filter === 'all' ? 'primary' : 'default'} onClick={() => setFilter('all')} />
      </Box>

      <Paper sx={{ height: 500 }}>
        <DataGrid
          rows={alerts}
          columns={columns}
          loading={loading}
          getRowId={(row) => row.id}
          sx={{ border: 'none' }}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          pageSizeOptions={[10, 25, 50]}
        />
      </Paper>

      {/* Dialog Création */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Créer une alerte</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="normal" label="Titre" value={newAlert.title} onChange={(e) => setNewAlert({ ...newAlert, title: e.target.value })} />
          <TextField fullWidth margin="normal" select label="Sévérité" value={newAlert.severity} onChange={(e) => setNewAlert({ ...newAlert, severity: e.target.value })}>
            <MenuItem value="info">Info</MenuItem>
            <MenuItem value="warning">Warning</MenuItem>
            <MenuItem value="critical">Critical</MenuItem>
          </TextField>
          <TextField fullWidth margin="normal" multiline rows={3} label="Description" value={newAlert.description} onChange={(e) => setNewAlert({ ...newAlert, description: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Annuler</Button>
          <Button variant="contained" onClick={handleCreate}>Créer</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Alerts;
