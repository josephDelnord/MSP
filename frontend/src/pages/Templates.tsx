import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Button, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, IconButton,
  Tooltip, Card, CardContent, Grid, Tabs, Tab, Chip,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  Refresh as RefreshIcon, Description as RscIcon,
  Rule as YamlIcon,
} from '@mui/icons-material';
import { templatesApi } from '../services/api';
import type { Template } from '../types';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState({
    name: '', model: '', description: '',
    rsc_content: '', yaml_content: '',
    target_routeros_version: '',
  });

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await templatesApi.list();
      setTemplates(data);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleOpenDialog = (template?: Template) => {
    if (template) {
      setEditingTemplate(template);
      setFormData({
        name: template.name,
        model: template.model,
        description: template.description || '',
        rsc_content: template.rsc_content || '',
        yaml_content: template.yaml_content || '',
        target_routeros_version: template.target_routeros_version || '',
      });
    } else {
      setEditingTemplate(null);
      setFormData({ name: '', model: '', description: '', rsc_content: '', yaml_content: '', target_routeros_version: '' });
    }
    setTabValue(0);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editingTemplate) {
        await templatesApi.update(editingTemplate.id, formData);
      } else {
        await templatesApi.create(formData);
      }
      setDialogOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Supprimer ce template ?')) {
      try {
        await templatesApi.delete(id);
        fetchTemplates();
      } catch (error) {
        console.error('Erreur:', error);
      }
    }
  };

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'Nom', flex: 1, minWidth: 180 },
    { field: 'model', headerName: 'Modèle', width: 150 },
    { field: 'description', headerName: 'Description', flex: 1, minWidth: 200 },
    { field: 'target_routeros_version', headerName: 'RouterOS cible', width: 130 },
    {
      field: 'is_active',
      headerName: 'Actif',
      width: 80,
      renderCell: (params) => <Chip size="small" label={params.value ? 'Oui' : 'Non'} color={params.value ? 'success' : 'default'} />,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <Tooltip title="Modifier">
            <IconButton size="small" onClick={() => handleOpenDialog(params.row)}><EditIcon fontSize="small" /></IconButton>
          </Tooltip>
          <Tooltip title="Supprimer">
            <IconButton size="small" color="error" onClick={() => handleDelete(params.row.id)}><DeleteIcon fontSize="small" /></IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Templates</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>Nouveau template</Button>
          <IconButton onClick={fetchTemplates}><RefreshIcon /></IconButton>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        {templates.map((t) => (
          <Grid item xs={12} sm={6} md={4} key={t.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <Box>
                    <Typography variant="h6">{t.name}</Typography>
                    <Typography variant="body2" color="text.secondary">{t.model}</Typography>
                  </Box>
                  <Chip size="small" label={t.is_active ? 'Actif' : 'Inactif'} color={t.is_active ? 'success' : 'default'} />
                </Box>
                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Chip size="small" icon={<RscIcon />} label=".rsc" variant="outlined" />
                  <Chip size="small" icon={<YamlIcon />} label=".yaml" variant="outlined" />
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  RouterOS cible: {t.target_routeros_version || '-'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ height: 400 }}>
        <DataGrid
          rows={templates}
          columns={columns}
          loading={loading}
          sx={{ border: 'none' }}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          pageSizeOptions={[10, 25]}
        />
      </Paper>

      {/* Dialog Édition */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>{editingTemplate ? 'Modifier' : 'Nouveau'} template</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Nom" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Modèle" value={formData.model} onChange={(e) => setFormData({ ...formData, model: e.target.value })} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Description" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="RouterOS cible" value={formData.target_routeros_version} onChange={(e) => setFormData({ ...formData, target_routeros_version: e.target.value })} />
            </Grid>
          </Grid>

          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mt: 2 }}>
            <Tab icon={<RscIcon />} label="Template .rsc" />
            <Tab icon={<YamlIcon />} label="Conformité .yaml" />
          </Tabs>

          {tabValue === 0 && (
            <TextField
              fullWidth multiline rows={15} sx={{ mt: 2 }}
              label="Contenu du template RouterOS (.rsc)"
              value={formData.rsc_content}
              onChange={(e) => setFormData({ ...formData, rsc_content: e.target.value })}
              InputProps={{ sx: { fontFamily: 'monospace', fontSize: '0.875rem' } }}
            />
          )}
          {tabValue === 1 && (
            <TextField
              fullWidth multiline rows={15} sx={{ mt: 2 }}
              label="Contenu du template de conformité (.yaml)"
              value={formData.yaml_content}
              onChange={(e) => setFormData({ ...formData, yaml_content: e.target.value })}
              InputProps={{ sx: { fontFamily: 'monospace', fontSize: '0.875rem' } }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button variant="contained" onClick={handleSave}>Enregistrer</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Templates;
