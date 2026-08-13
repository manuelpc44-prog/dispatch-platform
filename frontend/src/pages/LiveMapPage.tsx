import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { PageHeader } from '../components/ui';
import { getAccessToken } from '../lib/api';

interface LivePosition {
  driver_id: string;
  driver_shift_id: string;
  vehicle_id: string;
  latitude: number;
  longitude: number;
  speed: number | null;
  heading: number | null;
  recorded_at: string;
}

const WAREHOUSE_CENTER: [number, number] = [-33.689, -71.215]; // Melipilla (bodega central del seed)

// Icono de marcador con el acento ámbar de la consola (evita el pin azul por defecto de Leaflet)
function driverIcon(isStale: boolean) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width: 16px; height: 16px; border-radius: 50%;
      background: ${isStale ? '#8b93a3' : '#f5a623'};
      border: 2px solid #14181f;
      box-shadow: 0 0 0 2px ${isStale ? '#8b93a355' : '#f5a62355'};
    "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function RecenterOnFirstFix({ positions }: { positions: Record<string, LivePosition> }) {
  const map = useMap();
  const centered = useRef(false);
  useEffect(() => {
    const first = Object.values(positions)[0];
    if (first && !centered.current) {
      map.setView([first.latitude, first.longitude], 12);
      centered.current = true;
    }
  }, [positions, map]);
  return null;
}

export default function LiveMapPage() {
  const [positions, setPositions] = useState<Record<string, LivePosition>>({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/dispatcher?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const data: LivePosition = JSON.parse(event.data);
      setPositions((prev) => ({ ...prev, [data.driver_id]: data }));
    };

    return () => ws.close();
  }, []);

  const positionList = Object.values(positions);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <PageHeader
        title="Mapa en vivo"
        subtitle={
          connected
            ? `Conectado — ${positionList.length} chofer(es) transmitiendo`
            : 'Conectando al canal en tiempo real…'
        }
      />
      <div style={{ padding: '0 28px 8px', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: connected ? 'var(--success)' : 'var(--text-dim)',
          }}
        />
        <span style={{ fontSize: 12, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
          {connected ? 'WS conectado' : 'WS desconectado'}
        </span>
      </div>

      <div style={{ flex: 1, margin: '0 28px 28px', borderRadius: 10, overflow: 'hidden', border: '1px solid var(--border)' }}>
        <MapContainer center={WAREHOUSE_CENTER} zoom={11} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <RecenterOnFirstFix positions={positions} />
          {positionList.map((p) => {
            const staleMs = Date.now() - new Date(p.recorded_at).getTime();
            const isStale = staleMs > 90_000; // ver docs/gps.md — umbral OFFLINE
            return (
              <Marker
                key={p.driver_id}
                position={[p.latitude, p.longitude]}
                icon={driverIcon(isStale)}
              >
                <Popup>
                  <div style={{ fontFamily: 'monospace', fontSize: 12 }}>
                    <div>Chofer: {p.driver_id.slice(0, 8)}…</div>
                    <div>Vehículo: {p.vehicle_id.slice(0, 8)}…</div>
                    <div>Velocidad: {p.speed ?? '—'} km/h</div>
                    <div>Actualizado: {new Date(p.recorded_at).toLocaleTimeString()}</div>
                    <div>Estado: {isStale ? 'OFFLINE (sin señal reciente)' : 'ONLINE'}</div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
