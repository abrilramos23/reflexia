import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { EntriesPage } from './EntriesPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('react-chartjs-2', () => ({
  Bar: () => <div data-testid="evolution-chart" />,
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
      exportEntriesPdf: vi.fn(),
      getMyEvolution: vi.fn().mockResolvedValue({
        analyzed_entries_count: 2,
        has_enough_data: true,
        risk_counts: { high: 0 },
        frequent_emotions: [
          { emotion: 'Calma', average_percentage: 62, occurrences: 2 },
          { emotion: 'Tristesa', average_percentage: 24, occurrences: 1 },
        ],
        data_points: [
          {
            date: '2026-04-10T10:00:00Z',
            primary_emotion: 'Tristesa',
            risk_level: 'low',
            emotions: { Calma: 50, Tristesa: 30 },
          },
          {
            date: '2026-04-12T10:00:00Z',
            primary_emotion: 'Calma',
            risk_level: 'low',
            emotions: { Calma: 74, Tristesa: 18 },
          },
        ],
      }),
    })

    render(
      <MemoryRouter>
        <EntriesPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Primera entrada del pacient.')).toBeInTheDocument()
    expect(screen.getByTestId('evolution-chart')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Escriure nova entrada' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Primera entrada del pacient/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Veure detall' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Editar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Eliminar' })).toBeInTheDocument()
  })
})
