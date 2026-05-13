import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EntryAnalysisPanel } from './EntryAnalysisPanel'

const baseAnalysis = {
  entry_id: 'entry-1',
  emotions: [
    { emotion: 'Tristesa', percentage: 62 },
    { emotion: 'Esperanca', percentage: 38 },
  ],
  primary_emotion: 'Tristesa',
  risk_level: 'moderate',
  summary: 'Predomina la tristesa amb alguns indicadors de regulacio.',
  recommendations: ['Respiracio guiada', 'Contactar terapeuta'],
  reviewed_by_therapist: false,
  therapist_correction: '',
}

describe('EntryAnalysisPanel', () => {
  it('allows a therapist to mark the analysis as reviewed without adding a correction', async () => {
    const onSaveCorrection = vi.fn().mockResolvedValue()

    render(
      <EntryAnalysisPanel
        analysis={baseAnalysis}
        canCorrect
        onSaveCorrection={onSaveCorrection}
      />,
    )

    expect(screen.getByText('Pendent de revisió')).toBeInTheDocument()
    fireEvent.submit(screen.getByRole('button', { name: 'Guardar correcció' }).closest('form'))

    await waitFor(() => {
      expect(onSaveCorrection).toHaveBeenCalledWith('')
    })
  })

  it('renders existing clinical corrections and the reviewed state', () => {
    render(
      <EntryAnalysisPanel
        analysis={{
          ...baseAnalysis,
          reviewed_by_therapist: true,
          therapist_correction: 'Lectura revisada manualment pel terapeuta.',
        }}
      />,
    )

    expect(screen.getByText('Revisada pel terapeuta')).toBeInTheDocument()
    expect(screen.getByText('Correcció del terapeuta')).toBeInTheDocument()
    expect(screen.getByText('Lectura revisada manualment pel terapeuta.')).toBeInTheDocument()
  })
})
