import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AlertDetailPage } from './AlertDetailPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const baseAlert = {
  id: 'alert-1',
  patient_id: 'patient-1',
  patient_name: 'Paula Sanchez',
  patient_email: 'paula@example.com',
  entry_id: 'entry-1',
  entry_date: '2026-05-20T10:00:00Z',
  entry_content: '<p>Em sento sobrepassada avui.</p>',
  risk_level: 'high',
  status: 'pending',
  justification: '',
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
    expect(screen.getByRole('link', { name: 'Revisar entrada' })).toHaveAttribute(
      'href',
      '/patients/patient-1/entries/entry-1',
    )
    expect(screen.getByText('Ansietat')).toBeInTheDocument()
    expect(screen.getByText('Risc alt detectat.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Validar alerta' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Descartar alerta' })).toBeInTheDocument()
    expect(screen.getByText('Enviada')).toBeInTheDocument()
  })

  it('validates a pending alert through the API and shows feedback', async () => {
    const { api } = renderAlertDetailPage()

    await screen.findByRole('button', { name: 'Validar alerta' })
    fireEvent.change(screen.getByLabelText('Justificació clínica'), {
      target: { value: 'El contingut descriu risc alt i cal activar suport proper.' },
    })
    fireEvent.change(screen.getByLabelText('Nota interna (opcional)'), {
      target: { value: 'Fer seguiment avui.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Validar alerta' }))

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/alerts/alert-1/', {
        action: 'VALIDATE',
        validation_note: 'Fer seguiment avui.',
        justification: 'El contingut descriu risc alt i cal activar suport proper.',
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
        justification: '',
      })
    })
    expect(await screen.findByText('Alerta descartada correctament.')).toBeInTheDocument()
  })

  it('notifies selected contacts, shows section feedback and resets the notification form', async () => {
    const { api } = renderAlertDetailPage({
      alert: {
        ...baseAlert,
        status: 'validated',
        justification: 'Cal activar el contacte de suport per risc alt.',
      },
    })

    await screen.findByRole('button', { name: 'Notificar 1 contacte' })
    fireEvent.click(screen.getByRole('button', { name: 'Notificar 1 contacte' }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/alerts/alert-1/notify-contacts/', {
        contact_ids: ['contact-1'],
        justification: 'Cal activar el contacte de suport per risc alt.',
      })
    })

    const notificationSection = screen.getByText('Notificar contactes').closest('section')
    const feedback = await within(notificationSection).findByText('Notificacions enviades: 1.')
    const textarea = within(notificationSection).getByLabelText('Justificació per als contactes')
    const checkbox = within(notificationSection).getByRole('checkbox', { name: /Maria Perez/ })

    expect(
      within(notificationSection).getByText(
        'La normativa exigeix registrar el motiu clínic abans d\'avisar els contactes.',
      ),
    ).toBeInTheDocument()
    expect(feedback.compareDocumentPosition(textarea) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(textarea).toHaveValue('')
    expect(checkbox).not.toBeChecked()
    expect(within(notificationSection).getByRole('button', { name: 'Notificar 0 contactes' })).toBeDisabled()
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument()
  })

  it('disables contact notification when no contacts are selected', async () => {
    renderAlertDetailPage({
      alert: {
        ...baseAlert,
        status: 'validated',
        justification: 'Cal activar el contacte de suport per risc alt.',
      },
    })

    const checkbox = await screen.findByRole('checkbox', { name: /Maria Perez/ })
    fireEvent.click(checkbox)

    expect(screen.getByRole('button', { name: 'Notificar 0 contactes' })).toBeDisabled()
  })

  it('shows clinical next steps when a validated alert has no contacts', async () => {
    renderAlertDetailPage({
      alert: {
        ...baseAlert,
        status: 'validated',
        justification: 'Cal activar suport proper.',
        associated_contacts: [],
      },
    })

    expect(
      await screen.findByText(/Gestiona aquesta alerta per altres canals/),
    ).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Notificar/ })).not.toBeInTheDocument()
  })
})
