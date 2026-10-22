import React, { useEffect, useState } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Paper,
  LinearProgress, Chip, IconButton, Tooltip,
} from '@mui/material';
import {
  Router as RouterIcon,
  CheckCircle as OnlineIcon,
  Cancel as OfflineIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Notifications as AlertIcon,
  SystemUpdate as UpdateIcon,
} from '@mui/icons-material';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { dashboardApi } from '../services/api';
import type { DashboardStats } from '../types';

const COLORS = ['#2e7d32', '#d32f2f', '#ed6c02', '#1976d2', '#9c27b0'];

const StatCard: React.FC<{
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}> = ({ title, value, icon, color, subtitle }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box sx={{ color, mr: 1 }}>{icon}</Box>
        <Typography variant="h6" color="text.secondary">{title}</Typography>
      </Box>
      <Typography variant="h3" sx={{ color, fontWeight: 'bold' }}>
        {value}
      </Typography>
      {subtitle && (
        <Typography variant="body2" color="text.secondary">{subtitle}</Typography>
      )}
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [routersStatus, setRoutersStatus] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, routersData] = await Promise.all([
        dashboardApi.getStats(),
        dashboardApi.getRoutersStatus(),
      ]);
      setStats(statsData);
      setRoutersStatus(routersData);
    } catch (error) {
      console.error('Erreur chargement dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading || !stats) {
    return <LinearProgress />;
  }

  const statusData = [
    { name: 'En ligne', value: stats.online_routers, color: '#2e7d32' },
    { name: 'Hors ligne', value: stats.offline_routers, color: '#d32f2f' },
    { name: 'Non conformes', value: stats.non_compliant_routers, color: '#ed6c02' },
    { name: 'En erreur', value: stats.error_routers, color: '#9c27b0' },
  ];

  const complianceData = routersStatus.map((r) => ({
    name: r.hostname,
    score: r.compliance_score,
  }));

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Dashboard</Typography>
        <Tooltip title="Actualiser">
          <IconButton onClick={fetchData}><RefreshIcon /></IconButton>
        </Tooltip>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Routeurs"
            value={stats.total_routers}
            icon={<RouterIcon fontSize="large" />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="En ligne"
            value={stats.online_routers}
            icon={<OnlineIcon fontSize="large" />}
            color="#2e7d32"
            subtitle={`${stats.offline_routers} hors ligne`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Non conformes"
            value={stats.non_compliant_routers}
            icon={<WarningIcon fontSize="large" />}
            color="#ed6c02"
            subtitle={`${stats.outdated_routers} obsolètes`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Alertes actives"
            value={stats.active_alerts}
            icon={<AlertIcon fontSize="large" />}
            color="#d32f2f"
            subtitle={`${stats.critical_alerts} critiques`}
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>État des routeurs</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Score de conformité</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={complianceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Bar dataKey="score" fill="#1976d2" name="Score %" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Routers */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>Routeurs récents</Typography>
        <Grid container spacing={2}>
          {routersStatus.slice(0, 6).map((router) => (
            <Grid item xs={12} sm={6} md={4} key={router.id}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {router.hostname}
                    </Typography>
                    <Chip
                      size="small"
                      label={router.status}
                      color={
                        router.status === 'online' ? 'success' :
                        router.status === 'offline' ? 'error' : 'warning'
                      }
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {router.model} - {router.ip_address}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Conformité: {router.compliance_score}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={router.compliance_score}
                      color={
                        router.compliance_score >= 95 ? 'success' :
                        router.compliance_score >= 70 ? 'warning' : 'error'
                      }
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default Dashboard;
