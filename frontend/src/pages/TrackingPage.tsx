import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface TimelineEntry {
  estado: string;
  created_at: string;
}

interface LivePosition {
  latitude: number;
  longitude: number;
  recorded_at: string;
}

interface TrackingData {
  numero: string;
  estado: string;
  destino_comuna: string;
  destino_ciudad: string;
  fecha_programada: string;
  cliente_nombre: string;
  timeline: TimelineEntry[];
  live_position: LivePosition | null;
}

const TIMELINE_STEPS = [
  { estado: 'PENDIENTE', label: 'Despacho creado' },
  { estado: 'PREPARANDO', label: 'Preparando pedido' },
  { estado: 'ASIGNADO', label: 'Asignado a transporte' },
  { estado: 'SALIDA_BODEGA', label: 'Salió de bodega' },
  { estado: 'EN_RUTA', label: 'En ruta' },
  { estado: 'LLEGADA_CLIENTE', label: 'Próximo a llegar' },
  { estado: 'ENTREGADO', label: 'Entregado' },
];

const truckIcon = L.divIcon({
  className: '',
  html: `<div style="width: 18px; height: 18px; border-radius: 50%; background: #f5a623; border: 3px solid #14181f; box-shadow: 0 0 0 3px #f5a62355;"></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

export default function TrackingPage() {
  const { trackingCode } = useParams<{ trackingCode: string }>();
  const [data, setData] = useState<TrackingData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!trackingCode) return;
    fetch(`/api/public/tracking/${trackingCode}`)
      .then((r) => {
        if (!r.ok) throw new Error('No encontramos ese despacho. Verifica el enlace.');
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message));
  }, [trackingCode]);

  useEffect(() => {
    if (!trackingCode) return;
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/tracking/${trackingCode}`);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      const pos: LivePosition = JSON.parse(event.data);
      setData((prev) => (prev ? { ...prev, live_position: pos } : prev));
    };
    return () => ws.close();
  }, [trackingCode]);

  if (error) {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <p style={{ color: 'var(--danger)' }}>{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <p style={{ color: 'var(--text-dim)' }}>Cargando seguimiento…</p>
        </div>
      </div>
    );
  }

  const currentIndex = TIMELINE_STEPS.findIndex((s) => s.estado === data.estado);
  // Estados que no calzan 1:1 con el timeline simplificado (ej. ENTREGA_EN_PROCESO,
  // NO_ENTREGADO, INCIDENCIA) se tratan como "en curso" en el paso más avanzado conocido.
  const effectiveIndex = currentIndex >= 0 ? currentIndex : TIMELINE_STEPS.length - 2;

  return (
    <div style={pageStyle}>
      <div style={{ width: '100%', maxWidth: 480 }}>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            DESPACHO #{data.numero}
          </div>
          <h1 style={{ fontSize: 20, marginTop: 4 }}>{data.cliente_nombre}</h1>
          <div style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 2 }}>
            Destino: {data.destino_comuna}, {data.destino_ciudad}
          </div>

          {data.live_position && (
            <div style={{ marginTop: 16, borderRadius: 10, overflow: 'hidden', border: '1px solid var(--border)', height: 220 }}>
              <MapContainer
                center={[data.live_position.latitude, data.live_position.longitude]}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
                zoomControl={false}
              >
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <Marker position={[data.live_position.latitude, data.live_position.longitude]} icon={truckIcon} />
              </MapContainer>
            </div>
          )}

          <div style={{ marginTop: 20 }}>
            {TIMELINE_STEPS.map((step, i) => {
              const done = i <= effectiveIndex;
              const isCurrent = i === effectiveIndex;
              return (
                <div key={step.estado} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 0' }}>
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      background: done ? (isCurrent ? 'var(--accent)' : 'var(--success)') : 'transparent',
                      border: `1.5px solid ${done ? (isCurrent ? 'var(--accent)' : 'var(--success)') : 'var(--border)'}`,
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ fontSize: 13, color: done ? 'var(--text)' : 'var(--text-dim)', fontWeight: isCurrent ? 600 : 400 }}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: 'var(--bg)',
  padding: 20,
};

const cardStyle: React.CSSProperties = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: 12,
  padding: 24,
};
