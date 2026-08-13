import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { PageHeader } from '../components/ui';

interface Customer {
  id: string;
  business_name: string;
  phone: string | null;
  email: string | null;
  addresses: { comuna: string; es_principal: boolean }[];
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Customer[]>('/customers?limit=100')
      .then(setCustomers)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Clientes" subtitle="Clientes y sus direcciones registradas" />
      <div style={{ padding: '0 28px 28px' }}>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Cargando…</p>}
        {!loading && customers.length === 0 && (
          <p style={{ color: 'var(--text-dim)' }}>No hay clientes registrados todavía.</p>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
          {customers.map((c) => {
            const principal = c.addresses.find((a) => a.es_principal) || c.addresses[0];
            return (
              <div
                key={c.id}
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: 16 }}
              >
                <div style={{ fontWeight: 600, fontSize: 14 }}>{c.business_name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 6 }}>
                  {principal ? principal.comuna : 'Sin dirección registrada'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>
                  {c.email || c.phone || '—'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
