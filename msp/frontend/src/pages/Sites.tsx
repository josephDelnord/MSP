import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Button, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem, IconButton,
  Grid, Card, CardContent,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Add as AddIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { sitesApi, clientsApi } from '../services/api';
import type { Site, Client } from '../types';

const Sites: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    client_id: '', name: '', address: '', city: '', postal_code: '', country: 'France', vlan: '', ip_lan: '', ip_wan: '',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sitesData, clientsData] = await Promise.all([
        sitesApi.list(),
        clientsApi.list(),
      ]);
      setSites(sitesData);
      setClients(clientsData);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSave = async () => {
    try {
      await sitesApi.create({
        ...formData,
        vlan: formData.vlan ? parseInt(formData.vlan) : undefined,
      });
      setDialogOpen(false);
      fetchData();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'Nom', flex: 1, minWidth: 150 },
    {
      field: 'client',
      headerName: 'Client',
      width: 150,
      valueGetter: (params) => clients.find((c) => c.id === params.row.client_id)?.name || '-',
    },
    { field: 'city', headerName: 'Ville', width: 120 },
    { field: 'postal_code', headerName: 'CP', width: 80 },
    { field: 'vlan', headerName: 'VLAN', width: 70 },
    { field: 'ip_lan', headerName: 'IP LAN', width: 130 },
    { field: 'ip_wan', headerName: 'IP WAN', width: 130 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Sites</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>Nouveau site</Button>
          <IconButton onClick={fetchData}><RefreshIcon /></IconButton>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        {sites.map((s) => (
          <Grid item xs={12} sm={6} md={4} key={s.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{s.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {clients.find((c) => c.id === s.client_id)?.name || '-'} - {s.city || '-'} {s.postal_code || ''}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>VLAN: {s.vlan || '-'} | LAN: {s.ip_lan || '-'}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ height: 400 }}>
        <DataGrid rows={sites} columns={columns} loading={loading} sx={{ border: 'none' }}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }} />
      </Paper>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nouveau site</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="normal" select label="Client" value={formData.client_id} onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}>
            {clients.map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
          </TextField>
          <TextField fullWidth margin="normal" label="Nom" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          <TextField fullWidth margin="normal" label="Adresse" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} />
          <Grid container spacing={2}>
            <Grid item xs={8}><TextField fullWidth margin="normal" label="Ville" value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} /></Grid>
            <Grid item xs={4}><TextField fullWidth margin="normal" label="CP" value={formData.postal_code} onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })} /></Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs={4}><TextField fullWidth margin="normal" label="VLAN" type="number" value={formData.vlan} onChange={(e) => setFormData({ ...formData, vlan: e.target.value })} /></Grid>
            <Grid item xs={4}><TextField fullWidth margin="normal" label="IP LAN" value={formData.ip_lan} onChange={(e) => setFormData({ ...formData, ip_lan: e.target.value })} /></Grid>
            <Grid item xs={4}><TextField fullWidth margin="normal" label="IP WAN" value={formData.ip_wan} onChange={(e) => setFormData({ ...formData, ip_wan: e.target.value })} /></Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button variant="contained" onClick={handleSave}>Créer</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Sites;
