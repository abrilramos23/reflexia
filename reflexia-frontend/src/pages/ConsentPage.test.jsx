import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ConsentPage } from './ConsentPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../lib/api.js', () => ({
  consentDocumentUrl: 'http://localhost/api/users/consent/document/',
  consentDocumentUrlForRole: (role = 'patient') => `http://localhost/api/users/consent/document/?role=${role}`,
}))

function renderConsent(user) {
  useAuth.mockReturnValue({
    user,
    acceptConsent: vi.fn(),
    rejectConsent: vi.fn(),
  })

  render(
    <MemoryRouter initialEntries={['/consent']}>
      <Routes>
        <Route path="/consent" element={<ConsentPage />} />
        <Route path="/dashboard" element={<div>Dashboard</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ConsentPage', () => {
  it('redirects to dashboard when consent has already been accepted', () => {
    renderConsent({ role: 'patient', legal_terms_accepted: true })

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.queryByText('Acceptar i continuar')).not.toBeInTheDocument()
  })

  it('renders accept and reject buttons for a patient without consent', () => {
    renderConsent({ role: 'patient', legal_terms_accepted: false })

    expect(screen.getByRole('button', { name: 'Acceptar i continuar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rebutjar i tancar compte' })).toBeInTheDocument()
  })

  it('shows an error when trying to accept without checking the checkbox', () => {
    renderConsent({ role: 'patient', legal_terms_accepted: false })

    fireEvent.click(screen.getByRole('button', { name: 'Acceptar i continuar' }))

    expect(
      screen.getByText('Has de marcar la casella per acceptar el document legal.'),
    ).toBeInTheDocument()
  })

  it('renders professional consent copy for therapists', () => {
    renderConsent({ role: 'therapist', legal_terms_accepted: false })

    expect(screen.getByText('Primer accés del terapeuta')).toBeInTheDocument()
    expect(screen.getByText('Consentiment professional')).toBeInTheDocument()
  })
})
