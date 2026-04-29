import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AppHeader } from './AppHeader';
import { useAuth } from '../context/AuthContext';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('AppHeader Component', () => {
  it('renders correctly for a patient', () => {
    useAuth.mockReturnValue({
      user: { role: 'patient' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter>
        <AppHeader />
      </MemoryRouter>
    );

    expect(screen.getByText('Reflexia')).toBeInTheDocument();
    expect(screen.getByText('Pacient')).toBeInTheDocument();
    expect(screen.queryByText('Entrades')).not.toBeInTheDocument();
    expect(screen.queryByText('Pacients')).not.toBeInTheDocument();
  });

  it('renders correctly for a therapist', () => {
    useAuth.mockReturnValue({
      user: { role: 'therapist' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter>
        <AppHeader />
      </MemoryRouter>
    );

    expect(screen.getByText('Reflexia')).toBeInTheDocument();
    expect(screen.getByText('Terapeuta')).toBeInTheDocument();
    expect(screen.queryByText('Pacients')).not.toBeInTheDocument();
  });
});
