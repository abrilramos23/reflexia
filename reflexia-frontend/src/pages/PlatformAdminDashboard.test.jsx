import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { PlatformAdminDashboard } from './PlatformAdminDashboard'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('PlatformAdminDashboard', () => {
  it('renders clinic admin totals from the dedicated stats field', async () => {
    useAuth.mockReturnValue({
      user: { role: 'platform_admin' },
      getPlatformStats: vi.fn().mockResolvedValue({
        total_organisations: 3,
        total_users: 12,
        total_clinic_admins: 17,
        users_by_role: {
          therapist: 5,
          patient: 6,
          platform_admin: 1,
        },
      }),
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<PlatformAdminDashboard />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('17')).toBeInTheDocument()
    expect(screen.getByText('Admins de Clínica')).toBeInTheDocument()
  })
})
