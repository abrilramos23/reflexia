import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AlertDetailPage } from './AlertDetailPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const baseAlert = {
  id: 'alert-1',
  patient_name: 'Paula Sanchez',
  patient_email: 'paula@example.com',
  entry_date: '2026-05-20T10:00:00Z',
  entry_content: '<p>Em sento sobrepassada avui.</p>',
  risk_level: 'high',
  status: 'pending',
  analysis_primary_emotion: 'anxiety',
  analysis_summary: 'Risc alt detectat.',
  associated_contacts: [
    {
      id: 'contact-1',
      name: 'Maria Perez',
      email: 'maria@example.com',
      relation: 'sister',
    },
  ],
}

const history = [
  {
    id: 'notification-1',
    contact_name: 'Maria Perez',
    contact_email: 'maria@example.com',
    status: 'sent',
    sent_at: '2026-05-20T11:00:00Z',
  },
]

function renderAlertDetailPage({ alert = baseAlert, apiOverrides = {}, user = { role: 'therapist' } } = {}) {
  const api = {
    get: vi.fn((url) => {
      if (url.endsWith('/history/')) {
        return Promise.resolve({ data: history })
      }

      return Promise.resolve({ data: alert })
    }),
    patch: vi.fn().mockResolvedValue({
      data: {
        ...alert,
        status: 'validated',
      },
    }),
    post: vi.fn().mockResolvedValue({
      data: {
        notified_count: 1,
        message: 'Notifications enqueued for 1 contact(s)',
      },
    }),
    ...apiOverrides,
  }

  useAuth.mockReturnValue({ user, api })

  render(
    <MemoryRouter initialEntries={['/alerts/alert-1']}>
      <Routes>
        <Route path="/alerts/:alertId" element={<AlertDetailPage />} />
        <Route path="/dashboard" element={<p>Dashboard</p>} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>,
  )

  return { api }
}

describe('AlertDetailPage', () => {
  it('renders pending alert details with validation actions and history', async () => {
    renderAlertDetailPage()

    expect(await screen.findByRole('heading', { name: 'Paula Sanchez' })).toBeInTheDocument()
    expect(screen.getByText('paula@example.com')).toBeInTheDocument()
    expect(screen.getByText('Em sento sobrepassada avui.')).toBeInTheDocument()
    expect(screen.getByText('Ansietat')).toBeInTheDocument()
    expect(screen.getByText('Risc alt detectat.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Validar alerta' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Descartar alerta' })).toBeInTheDocument()
    expect(screen.getByText('Enviada')).toBeInTheDocument()
  })

  it('validates a pending alert through the API and shows feedback', async () => {
    const { api } = renderAlertDetailPage()

    await screen.findByRole('button', { name: 'Validar alerta' })
    fireEvent.change(screen.getByLabelText('Nota (opcional)'), {
      target: { value: 'Fer seguiment avui.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Validar alerta' }))

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/alerts/alert-1/', {
        action: 'VALIDATE',
        validation_note: 'Fer seguiment avui.',
      })
    })
    expect(await screen.findByText('Alerta validada correctament.')).toBeInTheDocument()
  })

  it('dismisses a pending alert through the API and shows feedback', async () => {
    const { api } = renderAlertDetailPage({
      apiOverrides: {
        patch: vi.fn().mockResolvedValue({
          data: {
            ...baseAlert,
            status: 'dismissed',
          },
        }),
      },
    })

    await screen.findByRole('button', { name: 'Descartar alerta' })
    fireEvent.click(screen.getByRole('button', { name: 'Descartar alerta' }))

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/alerts/alert-1/', {
        action: 'DISMISS',
        validation_note: '',
      })
    })
    expect(await screen.findByText('Alerta descartada correctament.')).toBeInTheDocument()
  })

  it('notifies selected contacts without rendering undefined failed counts', async () => {
    const { api } = renderAlertDetailPage({
      alert: {
        ...baseAlert,
        status: 'validated',
      },
    })

    await screen.findByRole('button', { name: 'Notificar 1 contacte' })
    fireEvent.click(screen.getByRole('button', { name: 'Notificar 1 contacte' }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/alerts/alert-1/notify-contacts/', {
        contact_ids: ['contact-1'],
      })
    })
    expect(await screen.findByText('Notificacions enviades: 1.')).toBeInTheDocument()
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument()
  })

  it('disables contact notification when no contacts are selected', async () => {
    renderAlertDetailPage({
      alert: {
        ...baseAlert,
        status: 'validated',
      },
    })

    const checkbox = await screen.findByRole('checkbox', { name: /Maria Perez/ })
    fireEvent.click(checkbox)

    expect(screen.getByRole('button', { name: 'Notificar 0 contactes' })).toBeDisabled()
  })
})
