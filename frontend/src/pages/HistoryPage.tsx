import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { Play, Pause } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { PageHeader } from '../components/ui';

interface ShiftSummary {
  id: string;
  driver_name: string;
  vehicle_plate: string;
  estado: string;
  iniciada_at: string | null;
  finalizada_at: string | null;
  distancia_km: number;
  duracion_minutos: number | null;
  despachos_count: number;
  entregados_count: number;
}

interface ReplayPoint {
  latitude: number;
  longitude: number;
  speed: number | null;
  recorded_at: string;
}

const truckIcon = L.divIcon({
  className: '',
  html: `<div style="width: 16px; height: 16px; border-radius: 50%; background: #f5a623; border: 2px solid #14181f;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

export default function HistoryPage() {
  const [shifts, setShifts] = useState<ShiftSummary[]>([]);
  const [selectedShift, setSelectedShift] = useState<string | null>(null);
  const [points, setPoints] = useState<ReplayPoint[]>([]);
  const [playIndex, setPlayIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    apiFetch<ShiftSummary[]>('/reports/shifts').then(setShifts);
  }, []);

  useEffect(() => {
    if (!selectedShift) return;
    setPlaying(false);
    setPlayIndex(0);
    apiFetch<ReplayPoint[]>(`/reports/shifts/${selectedShift}/replay`).then(setPoints);
  }, [selectedShift]);

  useEffect(() => {
    if (playing && points.length > 0) {
      intervalRef.current = setInterval(() => {
        setPlayIndex((i) => {
          if (i >= points.length - 1) {
            setPlaying(false);
            return i;
          }
          return i + 1;
        });
      }, 500 / speedMultiplier);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [playing, points, speedMultiplier]);

  const polylinePositions = points.slice(0, playIndex + 1).map((p) => [p.latitude, p.longitude] as [number, number]);
  const currentPoint = points[playIndex];

  return (
    <div>
      <PageHeader title="Historial y reproducción de ruta" subtitle="Selecciona una jornada para ver su recorrido" />
      <div style={{ padding: '0 28px 28px', display: 'flex', gap: 20 }}>
        <div style={{ width: 320, flexShrink: 0 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 500, overflowY: 'auto' }}>
            {shifts.map((s) => (
              <div
                key={s.id}
                onClick={() => setSelectedShift(s.id)}
                style={{
                  cursor: 'pointer',
                  padding: 12,
                  borderRadius: 8,
                  background: selectedShift === s.id ? 'var(--surface-raised)' : 'var(--surface)',
                  border: `1px solid ${selectedShift === s.id ? 'var(--accent)' : 'var(--border)'}`,
                }}
              >
                <div style={{ fontWeight: 600, fontSize: 13 }}>{s.driver_name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                  {s.vehicle_plate} · {s.distancia_km} km · {s.duracion_minutos ?? '—'} min
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                  {s.entregados_count}/{s.despachos_count} entregados
                </div>
              </div>
            ))}
            {shifts.length === 0 && (
              <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No hay jornadas registradas todavía.</p>
            )}
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ borderRadius: 10, overflow: 'hidden', border: '1px solid var(--border)', height: 420 }}>
            {points.length > 0 ? (
              <MapContainer center={[points[0].latitude, points[0].longitude]} zoom={11} style={{ height: '100%', width: '100%' }}>
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <Polyline positions={polylinePositions} pathOptions={{ color: '#f5a623', weight: 3 }} />
                {currentPoint && <Marker position={[currentPoint.latitude, currentPoint.longitude]} icon={truckIcon} />}
              </MapContainer>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
                Selecciona una jornada para ver el recorrido
              </div>
            )}
          </div>

          {points.length > 0 && (
            <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
              <button
                onClick={() => setPlaying((p) => !p)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
                  background: 'var(--accent)', color: '#1a1204', border: 'none', borderRadius: 8, fontWeight: 600,
                }}
              >
                {playing ? <Pause size={14} /> : <Play size={14} />}
                {playing ? 'Pausar' : 'Reproducir'}
              </button>
              <input
                type="range"
                min={0}
                max={points.length - 1}
                value={playIndex}
                onChange={(e) => setPlayIndex(Number(e.target.value))}
                style={{ flex: 1 }}
              />
              <select
                value={speedMultiplier}
                onChange={(e) => setSpeedMultiplier(Number(e.target.value))}
                style={{ background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: 6, padding: '4px 8px' }}
              >
                <option value={1}>1x</option>
                <option value={2}>2x</option>
                <option value={4}>4x</option>
              </select>
              <span style={{ fontSize: 12, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                {playIndex + 1}/{points.length}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
