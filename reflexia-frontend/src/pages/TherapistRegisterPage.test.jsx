import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { TherapistRegisterPage } from './TherapistRegisterPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('TherapistRegisterPage', () => {
  it('renders the public therapist registration paths', () => {
    useAuth.mockReturnValue({ user: null, registerTherapist: vi.fn() })

    render(
      <MemoryRouter initialEntries={['/register/therapist?token=abc-123&email=joan%40example.com']}>
        <Routes>
          <Route path="/register/therapist" element={<TherapistRegisterPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('radio', { name: 'Independent' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Clínica' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Invitació' })).toBeInTheDocument()
    expect(screen.getByLabelText('Token d\'invitació')).toHaveValue('abc-123')
    expect(screen.getByLabelText('Correu electrònic')).toHaveValue('joan@example.com')
    expect(screen.getByRole('button', { name: 'Crear compte' })).toBeInTheDocument()
  })
})
