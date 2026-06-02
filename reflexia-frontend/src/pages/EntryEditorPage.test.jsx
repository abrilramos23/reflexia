import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { EntryEditorPage } from './EntryEditorPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('EntryEditorPage', () => {
  it('renders the active question and disables actions while the editor is empty', async () => {
    useAuth.mockReturnValue({
      user: {
        role: 'patient',
        consent_accepted: true,
        legal_terms_accepted: true,
      },
      getEntriesEditorContext: vi.fn().mockResolvedValue({
        active_question: {
          id: 'question-1',
          question: 'Quin moment del dia t’ha afectat més?',
          created_at: '2026-04-12T10:00:00Z',
        },
      }),
      getEntry: vi.fn(),
      createEntryDraft: vi.fn(),
      updateEntryDraft: vi.fn(),
      analyzeEntry: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/entries/new']}>
        <Routes>
          <Route path="/entries/new" element={<EntryEditorPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Quin moment del dia t’ha afectat més?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar esborrany' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Guardar i analitzar' })).toBeDisabled()
  })
})
