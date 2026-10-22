import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Chip, Grid, Card, CardContent,
  LinearProgress, IconButton, Tooltip, Accordion,
  AccordionSummary, AccordionDetails,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { auditsApi, routersApi } from '../services/api';
import type { Audit, Router } from '../types';

const Audits: React.FC = () => {
  const [audits, setAudits] = useState<Audit[]>([]);
  const [routers, setRouters] = useState<Record<string, Router>>({});
  const [loading, setLoading] = useState(true);
  const [expandedAudit, setExpandedAudit] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [auditsData, routersData] = await Promise.all([
        auditsApi.list(),
        routersApi.list(),
      ]);
      setAudits(auditsData);
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
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'success';
      case 'compliant_with_warnings': return 'warning';
      case 'non_compliant': return 'error';
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
      field: 'router',
      headerName: 'Routeur',
      width: 180,
      valueGetter: (params) => routers[params.row.router_id]?.hostname || params.row.router_id,
    },
    {
      field: 'compliance_status',
      headerName: 'Statut',
      width: 180,
      renderCell: (params) => (
        <Chip size="small" label={params.value} color={getStatusColor(params.value) as any} />
      ),
    },
    {
      field: 'compliance_score',
      headerName: 'Score',
      width: 120,
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
    {
      field: 'remediation_mode',
      headerName: 'Mode',
      width: 150,
    },
    {
      field: 'duration_seconds',
      headerName: 'Durée',
      width: 100,
      valueFormatter: (params) => params.value ? `${params.value.toFixed(1)}s` : '-',
    },
    {
      field: 'checks',
      headerName: 'Vérifications',
      width: 120,
      valueGetter: (params) => params.row.checks?.length || 0,
    },
    {
      field: 'anomalies',
      headerName: 'Anomalies',
      width: 100,
      valueGetter: (params) => params.row.anomalies?.length || 0,
      renderCell: (params) => (
        <Chip
          size="small"
          label={params.value}
          color={params.value > 0 ? 'error' : 'success'}
          variant={params.value > 0 ? 'filled' : 'outlined'}
        />
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Audits de conformité</Typography>
        <Tooltip title="Actualiser">
          <IconButton onClick={fetchData}><RefreshIcon /></IconButton>
        </Tooltip>
      </Box>

      <Paper sx={{ height: 500 }}>
        <DataGrid
          rows={audits}
          columns={columns}
          loading={loading}
          onRowClick={(params) => setExpandedAudit(expandedAudit === params.row.id ? null : params.row.id)}
          sx={{ border: 'none', cursor: 'pointer' }}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          pageSizeOptions={[10, 25, 50]}
        />
      </Paper>

      {/* Détail audit sélectionné */}
      {expandedAudit && (() => {
        const audit = audits.find((a) => a.id === expandedAudit);
        if (!audit) return null;
        return (
          <Paper sx={{ mt: 3, p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Détail de l'audit - {routers[audit.router_id]?.hostname}
            </Typography>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Score</Typography>
                <Typography variant="h5">{audit.compliance_score}%</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Statut</Typography>
                <Chip label={audit.compliance_status} color={getStatusColor(audit.compliance_status) as any} />
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Mode</Typography>
                <Typography>{audit.remediation_mode}</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Durée</Typography>
                <Typography>{audit.duration_seconds?.toFixed(1)}s</Typography>
              </Grid>
            </Grid>

            {audit.checks && audit.checks.length > 0 && (
              <>
                <Typography variant="subtitle1" gutterBottom>Vérifications ({audit.checks.length})</Typography>
                {audit.checks.map((check, idx) => (
                  <Accordion key={idx} disableGutters>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                        {check.status === 'compliant' ? <CheckIcon color="success" fontSize="small" /> :
                         check.status === 'warning' ? <WarningIcon color="warning" fontSize="small" /> :
                         <ErrorIcon color="error" fontSize="small" />}
                        <Typography sx={{ flexGrow: 1 }}>{check.name}</Typography>
                        <Chip size="small" label={check.category} variant="outlined" />
                        <Chip size="small" label={check.severity} color={check.severity === 'critical' ? 'error' : check.severity === 'high' ? 'warning' : 'default'} />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" color="text.secondary">Attendu</Typography>
                          <Typography>{check.expected || '-'}</Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" color="text.secondary">Trouvé</Typography>
                          <Typography>{check.found || '-'}</Typography>
                        </Grid>
                        {check.explanation && (
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">Explication</Typography>
                            <Typography>{check.explanation}</Typography>
                          </Grid>
                        )}
                        {check.remediation_commands && check.remediation_commands.length > 0 && (
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">Commandes de remédiation</Typography>
                            {check.remediation_commands.map((cmd, i) => (
                              <Typography key={i} variant="body2" fontFamily="monospace" sx={{ bgcolor: 'action.hover', p: 1, borderRadius: 1, mt: 0.5 }}>
                                {cmd}
                              </Typography>
                            ))}
                          </Grid>
                        )}
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </>
            )}
          </Paper>
        );
      })()}
    </Box>
  );
};

export default Audits;
