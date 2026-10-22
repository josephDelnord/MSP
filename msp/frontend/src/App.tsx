import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeContextProvider } from './context/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Routers from './pages/Routers';
import Audits from './pages/Audits';
import Alerts from './pages/Alerts';
import Templates from './pages/Templates';
import Clients from './pages/Clients';
import Sites from './pages/Sites';
import Login from './pages/Login';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('msp_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <ThemeContextProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="routers" element={<Routers />} />
            <Route path="audits" element={<Audits />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="templates" element={<Templates />} />
            <Route path="clients" element={<Clients />} />
            <Route path="sites" element={<Sites />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeContextProvider>
  );
};

export default App;
