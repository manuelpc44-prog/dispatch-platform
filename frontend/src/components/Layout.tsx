import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Route as RouteIcon,
  MapPin,
  Users,
  Truck,
  Building2,
  History,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/mapa', label: 'Mapa en vivo', icon: MapPin },
  { to: '/despachos', label: 'Despachos', icon: Package },
  { to: '/rutas', label: 'Rutas', icon: RouteIcon },
  { to: '/clientes', label: 'Clientes', icon: Building2 },
  { to: '/flota', label: 'Flota', icon: Truck },
  { to: '/historial', label: 'Historial', icon: History },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: 'var(--sidebar-width)',
          background: 'var(--surface)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          padding: '20px 12px',
          flexShrink: 0,
        }}
      >
        <div style={{ padding: '0 8px 24px 8px' }}>
          <h1 style={{ fontSize: 18, letterSpacing: '-0.02em' }}>
            Despacho<span style={{ color: 'var(--accent)' }}>.</span>
          </h1>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
            PANEL DESPACHADOR
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1 }}>
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '9px 10px',
                borderRadius: 'var(--radius)',
                textDecoration: 'none',
                color: isActive ? 'var(--text)' : 'var(--text-dim)',
                background: isActive ? 'var(--surface-raised)' : 'transparent',
                fontSize: 13,
                fontWeight: isActive ? 600 : 500,
                borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              })}
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 12 }}>
          <div style={{ padding: '0 8px', marginBottom: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{user?.full_name}</div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
              {user?.roles.join(', ')}
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              width: '100%',
              padding: '8px 10px',
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              color: 'var(--text-dim)',
              fontSize: 13,
            }}
          >
            <LogOut size={14} />
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main style={{ flex: 1, minWidth: 0, background: 'var(--bg)' }}>
        <Outlet />
      </main>
    </div>
  );
}
