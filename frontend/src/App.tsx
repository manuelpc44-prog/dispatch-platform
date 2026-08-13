import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import LiveMapPage from './pages/LiveMapPage';
import ShipmentsPage from './pages/ShipmentsPage';
import RoutesPage from './pages/RoutesPage';
import CustomersPage from './pages/CustomersPage';
import FleetPage from './pages/FleetPage';
import HistoryPage from './pages/HistoryPage';
import TrackingPage from './pages/TrackingPage';

function ProtectedRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
        Cargando…
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="mapa" element={<LiveMapPage />} />
        <Route path="despachos" element={<ShipmentsPage />} />
        <Route path="rutas" element={<RoutesPage />} />
        <Route path="clientes" element={<CustomersPage />} />
        <Route path="flota" element={<FleetPage />} />
        <Route path="historial" element={<HistoryPage />} />
      </Route>
    </Routes>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/seguimiento/:trackingCode" element={<TrackingPage />} />
      <Route path="/*" element={<ProtectedRoutes />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
