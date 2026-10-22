import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Button, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, IconButton,
  Grid, Card, CardContent,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Add as AddIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { clientsApi } from '../services/api';
import type { Client } from '../types';

const Clients: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', reference_crm: '', contact_email: '', contact_phone: '', address: '' });

  const fetchClients = async () => {
    setLoading(true);
    try {
      const data = await clientsApi.list();
      setClients(data);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleSave = async () => {
    try {
      await clientsApi.create(formData);
      setDialogOpen(false);
      setFormData({ name: '', reference_crm: '', contact_email: '', contact_phone: '', address: '' });
      fetchClients();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'Nom', flex: 1, minWidth: 200 },
    { field: 'reference_crm', headerName: 'Réf. CRM', width: 130 },
    { field: 'contact_email', headerName: 'Email', width: 200 },
    { field: 'contact_phone', headerName: 'Téléphone', width: 150 },
    { field: 'address', headerName: 'Adresse', flex: 1, minWidth: 200 },
    {
      field: 'is_active',
      headerName: 'Actif',
      width: 80,
      renderCell: (params) => params.value ? 'Oui' : 'Non',
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Clients</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>Nouveau client</Button>
          <IconButton onClick={fetchClients}><RefreshIcon /></IconButton>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        {clients.map((c) => (
          <Grid item xs={12} sm={6} md={4} key={c.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{c.name}</Typography>
                <Typography variant="body2" color="text.secondary">{c.reference_crm || '-'}</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>{c.contact_email || '-'}</Typography>
                <Typography variant="body2">{c.contact_phone || '-'}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ height: 400 }}>
        <DataGrid rows={clients} columns={columns} loading={loading} sx={{ border: 'none' }}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }} />
      </Paper>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nouveau client</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="normal" label="Nom" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          <TextField fullWidth margin="normal" label="Référence CRM" value={formData.reference_crm} onChange={(e) => setFormData({ ...formData, reference_crm: e.target.value })} />
          <TextField fullWidth margin="normal" label="Email" type="email" value={formData.contact_email} onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })} />
          <TextField fullWidth margin="normal" label="Téléphone" value={formData.contact_phone} onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })} />
          <TextField fullWidth margin="normal" label="Adresse" multiline rows={2} value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button variant="contained" onClick={handleSave}>Créer</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Clients;
