export function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        padding: '16px 18px',
        flex: 1,
        minWidth: 140,
      }}
    >
      <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </div>
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 28,
          fontWeight: 700,
          marginTop: 6,
          color: accent || 'var(--text)',
        }}
      >
        {value}
      </div>
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  CREADO: '#8b93a3',
  PENDIENTE: '#8b93a3',
  PREPARANDO: '#5b9dff',
  LISTO: '#5b9dff',
  ASIGNADO: '#f5a623',
  SALIDA_BODEGA: '#f5a623',
  EN_RUTA: '#f5a623',
  LLEGADA_CLIENTE: '#f5a623',
  ENTREGA_EN_PROCESO: '#f5a623',
  ENTREGADO: '#2dd4a7',
  NO_ENTREGADO: '#ff6b5b',
  INCIDENCIA: '#ff6b5b',
  REGRESO_BODEGA: '#f5a623',
  LLEGADA_BODEGA: '#2dd4a7',
  COMPLETADO: '#2dd4a7',
  CANCELADO: '#8b93a3',
};

export function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || '#8b93a3';
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '3px 9px',
        borderRadius: 999,
        fontSize: 11,
        fontFamily: 'var(--font-mono)',
        border: `1px solid ${color}55`,
        color,
        background: `${color}14`,
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: color }} />
      {status}
    </span>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div style={{ padding: '24px 28px 16px' }}>
      <h2 style={{ fontSize: 20 }}>{title}</h2>
      {subtitle && <p style={{ color: 'var(--text-dim)', fontSize: 13, marginTop: 4 }}>{subtitle}</p>}
    </div>
  );
}
