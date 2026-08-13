import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import TrackingPage from './TrackingPage';

const mockTrackingData = {
  numero: 'DES-2026-000042',
  estado: 'EN_RUTA',
  destino_comuna: 'Melipilla',
  destino_ciudad: 'Melipilla',
  fecha_programada: '2026-08-12',
  cliente_nombre: 'Ferretería El Tornillo',
  timeline: [
    { estado: 'PENDIENTE', created_at: '2026-08-12T10:00:00Z' },
    { estado: 'EN_RUTA', created_at: '2026-08-12T11:00:00Z' },
  ],
  live_position: null,
};

beforeEach(() => {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockTrackingData),
    })
  ) as unknown as typeof fetch;

  // WebSocket no disponible en jsdom — se mockea para que el componente no falle al montarse
  class MockWebSocket {
    close = vi.fn();
    onmessage: ((event: MessageEvent) => void) | null = null;
  }
  globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;
});

function renderWithRoute(trackingCode: string) {
  return render(
    <MemoryRouter initialEntries={[`/seguimiento/${trackingCode}`]}>
      <Routes>
        <Route path="/seguimiento/:trackingCode" element={<TrackingPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('TrackingPage (portal público)', () => {
  it('muestra los datos del despacho sin requerir login', async () => {
    renderWithRoute('abc-123');
    expect(await screen.findByText(/DES-2026-000042/)).toBeInTheDocument();
    expect(screen.getByText('Ferretería El Tornillo')).toBeInTheDocument();
  });

  it('muestra un error si el tracking_code no existe', async () => {
    globalThis.fetch = vi.fn(() => Promise.resolve({ ok: false })) as unknown as typeof fetch;
    renderWithRoute('codigo-invalido');
    expect(await screen.findByText(/no encontramos ese despacho/i)).toBeInTheDocument();
  });
});
