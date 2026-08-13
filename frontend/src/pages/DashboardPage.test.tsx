import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import DashboardPage from './DashboardPage';

vi.mock('../lib/api', () => ({
  apiFetch: vi.fn(() =>
    Promise.resolve([
      { id: '1', estado: 'EN_RUTA' },
      { id: '2', estado: 'ENTREGADO' },
      { id: '3', estado: 'ENTREGADO' },
      { id: '4', estado: 'INCIDENCIA' },
    ])
  ),
}));

describe('DashboardPage', () => {
  it('muestra el conteo total de despachos y por estado', async () => {
    render(<DashboardPage />);

    expect(await screen.findByText('4')).toBeInTheDocument(); // total
    expect(screen.getAllByText('2').length).toBeGreaterThan(0); // entregados
  });

  it('muestra la distribución por estado', async () => {
    render(<DashboardPage />);
    expect(await screen.findByText('EN_RUTA')).toBeInTheDocument();
    expect(screen.getByText('INCIDENCIA')).toBeInTheDocument();
  });
});
