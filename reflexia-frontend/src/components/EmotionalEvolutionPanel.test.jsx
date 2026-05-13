import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EmotionalEvolutionPanel } from './EmotionalEvolutionPanel'

vi.mock('react-chartjs-2', () => ({
  Bar: ({ data, options }) => (
    <div
      data-testid="evolution-chart"
      data-labels={data.labels.join(',')}
      data-datasets={data.datasets.map((dataset) => dataset.label).join(',')}
      data-stacked={String(options.scales.x.stacked && options.scales.y.stacked)}
    />
  ),
}))

describe('EmotionalEvolutionPanel', () => {
  it('renders stacked emotional evolution data for analyzed entries', () => {
    render(
      <EmotionalEvolutionPanel
        evolution={{
          analyzed_entries_count: 2,
          has_enough_data: true,
          risk_counts: { high: 1 },
          frequent_emotions: [
            { emotion: 'Tristesa', average_percentage: 55, occurrences: 2 },
            { emotion: 'Calma', average_percentage: 35, occurrences: 1 },
          ],
          data_points: [
            {
              date: '2026-05-07T10:00:00Z',
              primary_emotion: 'Tristesa',
              risk_level: 'high',
              emotions: { Tristesa: 60, Calma: 20 },
            },
            {
              date: '2026-05-10T10:00:00Z',
              primary_emotion: 'Calma',
              risk_level: 'low',
              emotions: { Tristesa: 50, Calma: 50 },
            },
          ],
        }}
      />,
    )

    expect(screen.getByText('Entrades analitzades')).toBeInTheDocument()
    expect(screen.getByText('Emoció principal')).toBeInTheDocument()
    expect(screen.getByText('Tristesa: 55%')).toBeInTheDocument()
    expect(screen.getByTestId('evolution-chart')).toHaveAttribute('data-datasets', 'Tristesa,Calma')
    expect(screen.getByTestId('evolution-chart')).toHaveAttribute('data-stacked', 'true')
  })
})
