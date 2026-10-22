import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Card, CardContent, TextField, Button, Typography,
  Alert, Container, Avatar, InputAdornment, IconButton,
} from '@mui/material';
import {
  Router as RouterIcon,
  Visibility, VisibilityOff,
  Login as LoginIcon,
} from '@mui/icons-material';
import { authApi } from '../services/api';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { access_token } = await authApi.login(username, password);
      localStorage.setItem('msp_token', access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Card sx={{ width: '100%', p: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
              <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main', mb: 2 }}>
                <RouterIcon fontSize="large" />
              </Avatar>
              <Typography variant="h4" fontWeight="bold">MSP</Typography>
              <Typography variant="body2" color="text.secondary">
                Mikrotik Provisioning Manager
              </Typography>
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Nom d'utilisateur"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                margin="normal"
                autoFocus
                required
              />
              <TextField
                fullWidth
                label="Mot de passe"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                margin="normal"
                required
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
                startIcon={<LoginIcon />}
              >
                {loading ? 'Connexion...' : 'Se connecter'}
              </Button>
            </form>

            <Typography variant="caption" color="text.secondary" align="center" display="block">
              Identifiants par défaut: admin / admin
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default Login;
