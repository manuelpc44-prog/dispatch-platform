import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { PageHeader, StatCard } from '../components/ui';

interface Shipment {
  id: string;
  estado: string;
}

export default function DashboardPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Shipment[]>('/shipments?limit=200')
      .then(setShipments)
      .finally(() => setLoading(false));
  }, []);

  const counts = shipments.reduce<Record<string, number>>((acc, s) => {
    acc[s.estado] = (acc[s.estado] || 0) + 1;
    return acc;
  }, {});

  const enRuta = (counts['EN_RUTA'] || 0) + (counts['SALIDA_BODEGA'] || 0);
  const entregados = counts['ENTREGADO'] || 0;
  const incidencias = counts['INCIDENCIA'] || 0;

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Vista general de la operación de hoy" />
      <div style={{ padding: '0 28px 28px', display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <StatCard label="Despachos totales" value={loading ? '—' : shipments.length} />
        <StatCard label="En ruta" value={loading ? '—' : enRuta} accent="var(--accent)" />
        <StatCard label="Entregados" value={loading ? '—' : entregados} accent="var(--success)" />
        <StatCard label="Incidencias" value={loading ? '—' : incidencias} accent="var(--danger)" />
      </div>

      <div style={{ padding: '0 28px' }}>
        <h3 style={{ fontSize: 14, marginBottom: 12, color: 'var(--text-dim)' }}>
          Distribución por estado
        </h3>
        <div
          style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 10,
            padding: 16,
          }}
        >
          {Object.entries(counts).length === 0 && !loading && (
            <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No hay despachos registrados todavía.</p>
          )}
          {Object.entries(counts).map(([estado, count]) => (
            <div
              key={estado}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '8px 0',
                borderBottom: '1px solid var(--border)',
                fontSize: 13,
              }}
            >
              <span className="mono" style={{ color: 'var(--text-dim)' }}>{estado}</span>
              <span style={{ fontWeight: 600 }}>{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
