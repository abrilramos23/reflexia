import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ClinicTherapistsPage } from './ClinicTherapistsPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('ClinicTherapistsPage', () => {
  it('allows clinic admins represented as therapists to access therapist management', () => {
    useAuth.mockReturnValue({
      user: {
        role: 'therapist',
        organisation: {
          id: 'org-1',
          name: 'Clínica Central',
        },
      },
      isClinicAdmin: true,
      listClinicTherapists: vi.fn().mockResolvedValue([]),
      registerTherapist: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/admin/therapists']}>
        <Routes>
          <Route path="/admin/therapists" element={<ClinicTherapistsPage />} />
          <Route path="/dashboard" element={<div>Dashboard</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Terapeutes')).toBeInTheDocument()
    expect(screen.getByText('Clínica Central')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
  })
})
