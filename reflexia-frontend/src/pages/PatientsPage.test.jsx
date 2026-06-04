import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { PatientsPage } from './PatientsPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const patients = [
  {
    id: 'patient-1',
    first_name: 'Paula',
    last_name: 'Sanchez',
    email: 'paula@example.com',
    birth_date: '1994-05-10',
    is_active: true,
    consent_accepted: true,
  },
  {
    id: 'patient-2',
    first_name: 'Nil',
    last_name: 'Costa',
    email: 'nil@example.com',
    birth_date: '1990-03-12',
    is_active: false,
    consent_accepted: false,
  },
]

function renderPatientsPage(authOverrides = {}) {
  useAuth.mockReturnValue({
    user: { role: 'therapist' },
    registerPatient: vi.fn(),
    listTherapistPatients: vi.fn().mockResolvedValue(patients),
    deactivatePatient: vi.fn(),
    ...authOverrides,
  })

  render(
    <MemoryRouter initialEntries={['/patients']}>
      <Routes>
        <Route path="/patients" element={<PatientsPage />} />
        <Route path="/dashboard" element={<p>Dashboard</p>} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PatientsPage', () => {
  it('filters therapist patients by search and account status', async () => {
    renderPatientsPage()

    expect(await screen.findByText('Paula Sanchez')).toBeInTheDocument()
    expect(screen.getByText('Nil Costa')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Cerca'), {
      target: { value: 'paula' },
    })

    expect(screen.getByText('Paula Sanchez')).toBeInTheDocument()
    expect(screen.queryByText('Nil Costa')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Netejar filtres/i }))
    fireEvent.change(screen.getByLabelText('Estat del compte'), {
      target: { value: 'inactive' },
    })

    expect(screen.queryByText('Paula Sanchez')).not.toBeInTheDocument()
    expect(screen.getByText('Nil Costa')).toBeInTheDocument()
  })
})
