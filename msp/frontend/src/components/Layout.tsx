import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, AppBar, Toolbar, List, Typography, Divider,
  ListItem, ListItemButton, ListItemIcon, ListItemText,
  IconButton, Avatar, Menu, MenuItem, Badge, Tooltip,
  useTheme, useMediaQuery,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Router as RouterIcon,
  Assessment as AuditIcon,
  Notifications as AlertIcon,
  Settings as TemplateIcon,
  Business as ClientIcon,
  LocationOn as SiteIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Logout as LogoutIcon,
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
} from '@mui/icons-material';
import { useThemeMode } from '../context/ThemeContext';
import { authApi } from '../services/api';
import type { User } from '../types';

const drawerWidth = 260;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Routeurs', icon: <RouterIcon />, path: '/routers' },
  { text: 'Audits', icon: <AuditIcon />, path: '/audits' },
  { text: 'Alertes', icon: <AlertIcon />, path: '/alerts' },
  { text: 'Templates', icon: <TemplateIcon />, path: '/templates' },
  { text: 'Clients', icon: <ClientIcon />, path: '/clients' },
  { text: 'Sites', icon: <SiteIcon />, path: '/sites' },
];

const Layout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { mode, toggleMode } = useThemeMode();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await authApi.me();
        setUser(data);
      } catch {
        navigate('/login');
      }
    };
    fetchUser();
  }, [navigate]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = () => {
    localStorage.removeItem('msp_token');
    navigate('/login');
  };

  const drawer = (
    <Box>
      <Toolbar sx={{ gap: 2, py: 2 }}>
        <Avatar sx={{ bgcolor: 'primary.main' }}>M</Avatar>
        <Box>
          <Typography variant="h6" noWrap>MSP</Typography>
          <Typography variant="caption" color="text.secondary">
            Mikrotik Provisioning Manager
          </Typography>
        </Box>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                if (isMobile) setMobileOpen(false);
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {menuItems.find((i) => i.path === location.pathname)?.text || 'MSP'}
          </Typography>

          <Tooltip title={mode === 'light' ? 'Mode sombre' : 'Mode clair'}>
            <IconButton color="inherit" onClick={toggleMode}>
              {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Compte">
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} sx={{ ml: 1 }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </Avatar>
            </IconButton>
          </Tooltip>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
          >
            <MenuItem disabled>
              <Typography variant="body2">{user?.full_name || user?.username}</Typography>
            </MenuItem>
            <MenuItem disabled>
              <Typography variant="caption" color="text.secondary">{user?.role}</Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
              Déconnexion
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;
