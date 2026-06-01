import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AlertsPage } from './AlertsPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const alerts = [
  {
    id: 'alert-1',
    patient_name: 'Paula Sanchez',
    status: 'pending',
    risk_level: 'high',
    created_at: '2026-05-20T10:00:00Z',
  },
  {
    id: 'alert-2',
    patient_name: 'Nil Costa',
    status: 'validated',
    risk_level: 'high',
    created_at: '2026-05-19T10:00:00Z',
  },
]

function renderAlertsPage(authOverrides = {}) {
  const api = authOverrides.api ?? {
    get: vi.fn().mockResolvedValue({ data: alerts }),
  }

  useAuth.mockReturnValue({
    user: { role: 'therapist' },
    api,
    ...authOverrides,
  })

  render(
    <MemoryRouter initialEntries={['/alerts']}>
      <Routes>
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/dashboard" element={<p>Dashboard</p>} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>,
  )

  return { api }
}

describe('AlertsPage', () => {
  it('renders therapist alerts with counters and status/risk labels', async () => {
    renderAlertsPage()

    expect(await screen.findByText('Paula Sanchez')).toBeInTheDocument()
    expect(screen.getByText('Nil Costa')).toBeInTheDocument()
    expect(screen.getByText('1 pendents')).toBeInTheDocument()
    expect(screen.getByText('1 risc alt')).toBeInTheDocument()
    expect(screen.getByText('2 totals')).toBeInTheDocument()
    expect(screen.getAllByText('Pendent')).toHaveLength(2)
    expect(screen.getByText('Risc alt')).toBeInTheDocument()
  })

  it('sends status and risk filters as API params', async () => {
    const { api } = renderAlertsPage()

    await screen.findByText('Paula Sanchez')
    fireEvent.change(screen.getByLabelText('Estat'), {
      target: { value: 'validated' },
    })
    fireEvent.change(screen.getByLabelText('Nivell de risc'), {
      target: { value: 'high' },
    })

    await waitFor(() => {
      expect(api.get).toHaveBeenLastCalledWith('/alerts/', {
        params: {
          status: 'validated',
          risk_level: 'high',
        },
      })
    })
    expect(screen.getByText('Nil Costa')).toBeInTheDocument()
    expect(screen.queryByText('Paula Sanchez')).not.toBeInTheDocument()
  })

  it('redirects non-therapist users away from the alerts list', async () => {
    renderAlertsPage({
      user: { role: 'patient' },
      api: { get: vi.fn() },
    })

    expect(await screen.findByText('Dashboard')).toBeInTheDocument()
  })
})
