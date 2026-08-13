import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatusBadge, StatCard } from './ui';

describe('StatusBadge', () => {
  it('muestra el texto del estado', () => {
    render(<StatusBadge status="EN_RUTA" />);
    expect(screen.getByText('EN_RUTA')).toBeInTheDocument();
  });

  it('renderiza estados desconocidos sin fallar', () => {
    render(<StatusBadge status="ALGO_INESPERADO" />);
    expect(screen.getByText('ALGO_INESPERADO')).toBeInTheDocument();
  });
});

describe('StatCard', () => {
  it('muestra la etiqueta y el valor', () => {
    render(<StatCard label="Despachos" value={42} />);
    expect(screen.getByText('Despachos')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });
});
