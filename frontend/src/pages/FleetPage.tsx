import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { PageHeader } from '../components/ui';

interface Vehicle {
  id: string;
  plate: string;
  brand: string | null;
  model: string | null;
  active: boolean;
}

interface Driver {
  id: string;
  full_name: string;
  email: string;
  license_number: string;
  active: boolean;
}

export default function FleetPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([apiFetch<Vehicle[]>('/vehicles?limit=100'), apiFetch<Driver[]>('/drivers?limit=100')])
      .then(([v, d]) => {
        setVehicles(v);
        setDrivers(d);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Flota" subtitle="Vehículos y choferes registrados" />
      <div style={{ padding: '0 28px 28px', display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 300 }}>
          <h3 style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 10 }}>VEHÍCULOS</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {!loading && vehicles.map((v) => (
              <div
                key={v.id}
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', display: 'flex', justifyContent: 'space-between' }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{v.plate}</span>
                <span style={{ color: 'var(--text-dim)', fontSize: 12 }}>{v.brand} {v.model}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 300 }}>
          <h3 style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 10 }}>CHOFERES</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {!loading && drivers.map((d) => (
              <div
                key={d.id}
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', display: 'flex', justifyContent: 'space-between' }}
              >
                <span style={{ fontWeight: 600 }}>{d.full_name}</span>
                <span style={{ color: 'var(--text-dim)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{d.license_number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
