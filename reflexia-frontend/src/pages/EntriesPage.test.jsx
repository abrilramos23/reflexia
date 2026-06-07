import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { EntriesPage } from './EntriesPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('EntriesPage', () => {
  it('renders the entries list and its actions', async () => {
    useAuth.mockReturnValue({
      user: {
        role: 'patient',
        consent_accepted: true,
        legal_terms_accepted: true,
      },
      listEntries: vi.fn().mockResolvedValue([
        {
          id: 'entry-1',
          content: '<p>Primera entrada del pacient.</p>',
          preview: 'Primera entrada del pacient.',
          status: 'active',
          created_at: '2026-04-12T10:00:00Z',
          updated_at: '2026-04-12T10:00:00Z',
          is_deleted: false,
          analysis: null,
          therapist_question: null,
        },
      ]),
      deleteEntry: vi.fn(),
    })

    render(
      <MemoryRouter>
        <EntriesPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Primera entrada del pacient.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Escriure nova entrada' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Primera entrada del pacient/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Veure detall' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Editar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Eliminar' })).toBeInTheDocument()
  })
})
