import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

function renderLogin(initialEntries = ['/login'], state = undefined) {
  useAuth.mockReturnValue({ user: null, login: vi.fn() })

  const entries = state
    ? [{ pathname: '/login', state }]
    : initialEntries

  render(
    <MemoryRouter initialEntries={entries}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  it('renders the login form with all required fields and the submit button', () => {
    renderLogin()

    expect(screen.getByLabelText('Correu electrònic')).toBeInTheDocument()
    expect(screen.getByLabelText('Contrasenya')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'He oblidat la contrasenya' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Registre terapeuta' })).toBeInTheDocument()
  })

  it('shows a success message passed via route state', () => {
    renderLogin(['/login'], { message: 'Has restablert la contrasenya correctament.' })

    expect(
      screen.getByText('Has restablert la contrasenya correctament.'),
    ).toBeInTheDocument()
  })

  it('submit button is enabled while the form is idle', () => {
    renderLogin()

    expect(screen.getByRole('button', { name: 'Entrar' })).not.toBeDisabled()
  })
})
