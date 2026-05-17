import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from './SideBar'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('Sidebar Component', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders correct navigation items for a patient', () => {
    useAuth.mockReturnValue({
      user: { role: 'patient' },
      isClinicAdmin: false,
      logout: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.getByText('Entrades')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Perfil')).toBeInTheDocument()
    expect(screen.queryByText('Pacients')).not.toBeInTheDocument()
  })

  it('renders correct navigation items for a therapist', () => {
    useAuth.mockReturnValue({
      user: { role: 'therapist' },
      isClinicAdmin: false,
      logout: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.getByText('Pacients')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Perfil')).toBeInTheDocument()
    expect(screen.queryByText('Entrades')).not.toBeInTheDocument()
    expect(screen.queryByText('Suport')).not.toBeInTheDocument()
  })

  it('shows support for non-admin therapists assigned to a clinic', () => {
    useAuth.mockReturnValue({
      user: {
        role: 'therapist',
        memberships: [
          {
            organisation: { type: 'clinic' },
            is_admin: false,
          },
        ],
      },
      isClinicAdmin: false,
      logout: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.getByText('Suport')).toBeInTheDocument()
    expect(screen.queryByText('Clínica')).not.toBeInTheDocument()
    expect(screen.queryByText('Terapeutes')).not.toBeInTheDocument()
  })
})
