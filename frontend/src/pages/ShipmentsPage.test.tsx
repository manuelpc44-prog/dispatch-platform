import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ShipmentsPage from './ShipmentsPage';

vi.mock('../lib/api', () => ({
  apiFetch: vi.fn(() =>
    Promise.resolve([
      {
        id: '1', numero: 'DES-2026-000001', estado: 'EN_RUTA',
        fecha_programada: '2026-08-12', prioridad: 'NORMAL', driver_id: null,
      },
    ])
  ),
}));

describe('ShipmentsPage', () => {
  it('muestra los despachos obtenidos de la API', async () => {
    render(<ShipmentsPage />);
    expect(await screen.findByText('DES-2026-000001')).toBeInTheDocument();
    expect(screen.getByText('EN_RUTA')).toBeInTheDocument();
  });

  it('muestra un mensaje cuando no hay despachos', async () => {
    const { apiFetch } = await import('../lib/api');
    vi.mocked(apiFetch).mockResolvedValueOnce([]);
    render(<ShipmentsPage />);
    expect(await screen.findByText(/no hay despachos/i)).toBeInTheDocument();
  });
});
