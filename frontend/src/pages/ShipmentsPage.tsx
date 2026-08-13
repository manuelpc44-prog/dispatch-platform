import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { PageHeader, StatusBadge } from '../components/ui';

interface Shipment {
  id: string;
  numero: string;
  estado: string;
  fecha_programada: string;
  prioridad: string;
  driver_id: string | null;
}

export default function ShipmentsPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Shipment[]>('/shipments?limit=100')
      .then(setShipments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Despachos" subtitle="Listado de despachos y su estado actual" />
      <div style={{ padding: '0 28px 28px' }}>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Cargando…</p>}
        {error && <p style={{ color: 'var(--danger)' }}>{error}</p>}
        {!loading && shipments.length === 0 && (
          <p style={{ color: 'var(--text-dim)' }}>No hay despachos registrados todavía.</p>
        )}
        {shipments.length > 0 && (
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left' }}>
                  {['Número', 'Fecha', 'Prioridad', 'Estado', 'Chofer asignado'].map((h) => (
                    <th key={h} style={{ padding: '10px 16px', color: 'var(--text-dim)', fontWeight: 500, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shipments.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px 16px', fontFamily: 'var(--font-mono)' }}>{s.numero}</td>
                    <td style={{ padding: '10px 16px' }}>{s.fecha_programada}</td>
                    <td style={{ padding: '10px 16px' }}>{s.prioridad}</td>
                    <td style={{ padding: '10px 16px' }}><StatusBadge status={s.estado} /></td>
                    <td style={{ padding: '10px 16px', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                      {s.driver_id ? `${s.driver_id.slice(0, 8)}…` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
