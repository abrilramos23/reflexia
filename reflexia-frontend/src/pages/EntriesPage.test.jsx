import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { EntriesPage } from './EntriesPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('EntriesPage', () => {
  it('renders the active therapist question and disables analysis while the entry is empty', async () => {
    useAuth.mockReturnValue({
      user: {
        role: 'patient',
        consent_accepted: true,
      },
      getEntriesEditorContext: vi.fn().mockResolvedValue({
        active_question: {
          id: 'question-1',
          question: 'Quin moment del dia t’ha afectat més?',
          created_at: '2026-04-12T10:00:00Z',
        },
        entries: [],
      }),
      createEntryDraft: vi.fn(),
      updateEntryDraft: vi.fn(),
      analyzeEntry: vi.fn(),
    })

    render(
      <MemoryRouter>
        <EntriesPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Quin moment del dia t’ha afectat més?')).toBeInTheDocument()

    expect(screen.getByRole('button', { name: 'Guardar i analitzar' })).toBeDisabled()
  })
})
