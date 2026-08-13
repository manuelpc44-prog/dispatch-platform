import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { PageHeader } from '../components/ui';

interface RouteStop {
  id: string;
  shipment_id: string;
  orden: number;
  estado: string;
}

interface RouteItem {
  id: string;
  driver_id: string;
  vehicle_id: string;
  fecha: string;
  estado: string;
  stops: RouteStop[];
}

export default function RoutesPage() {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<RouteItem[]>('/routes?limit=100')
      .then(setRoutes)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Rutas" subtitle="Asignaciones de despachos a chofer + vehículo" />
      <div style={{ padding: '0 28px 28px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Cargando…</p>}
        {!loading && routes.length === 0 && (
          <p style={{ color: 'var(--text-dim)' }}>No hay rutas asignadas todavía.</p>
        )}
        {routes.map((r) => (
          <div
            key={r.id}
            style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: 16 }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                  Chofer {r.driver_id.slice(0, 8)}… · Vehículo {r.vehicle_id.slice(0, 8)}…
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>{r.fecha}</div>
              </div>
              <span style={{ fontSize: 12, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>{r.estado}</span>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {r.stops.map((stop) => (
                <div
                  key={stop.id}
                  style={{
                    fontSize: 11,
                    fontFamily: 'var(--font-mono)',
                    padding: '4px 8px',
                    borderRadius: 6,
                    background: 'var(--surface-raised)',
                    border: '1px solid var(--border)',
                  }}
                >
                  #{stop.orden} · {stop.estado}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
