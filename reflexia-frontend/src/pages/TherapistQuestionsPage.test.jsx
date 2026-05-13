import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { TherapistQuestionsPage } from './TherapistQuestionsPage'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('TherapistQuestionsPage', () => {
  it('renders active/history questions and creates a new question for an active patient', async () => {
    const listAllTherapistQuestions = vi.fn().mockResolvedValue([
      {
        id: 'question-active',
        question: 'Què t’ha ajudat a regular-te aquesta setmana?',
        patient_id: 'patient-1',
        patient_name: 'Paula Sanchez',
        is_active: true,
        created_at: '2026-05-10T10:00:00Z',
      },
      {
        id: 'question-history',
        question: 'Quin moment vols revisar a sessió?',
        patient_id: 'patient-1',
        patient_name: 'Paula Sanchez',
        is_active: false,
        created_at: '2026-05-09T10:00:00Z',
      },
    ])
    const createPatientQuestion = vi.fn().mockResolvedValue({
      question: {
        id: 'question-new',
        question: 'Nova pregunta',
      },
    })

    useAuth.mockReturnValue({
      user: { role: 'therapist' },
      listAllTherapistQuestions,
      listTherapistPatients: vi.fn().mockResolvedValue([
        { id: 'patient-1', first_name: 'Paula', last_name: 'Sanchez', is_active: true },
        { id: 'patient-2', first_name: 'Joan', last_name: 'Serra', is_active: false },
      ]),
      createPatientQuestion,
    })

    render(
      <MemoryRouter>
        <TherapistQuestionsPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Què t’ha ajudat a regular-te aquesta setmana?')).toBeInTheDocument()
    expect(screen.getByText('Quin moment vols revisar a sessió?')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Envia una nova pregunta/i }))
    expect(screen.getByRole('option', { name: 'Paula Sanchez' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Joan Serra' })).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Selecciona un pacient'), {
      target: { value: 'patient-1' },
    })
    fireEvent.change(screen.getByLabelText('Pregunta'), {
      target: { value: 'Com valores el teu nivell d’energia avui?' },
    })
    fireEvent.submit(screen.getByRole('button', { name: 'Enviar pregunta' }).closest('form'))

    await waitFor(() => {
      expect(createPatientQuestion).toHaveBeenCalledWith('patient-1', {
        text: 'Com valores el teu nivell d’energia avui?',
      })
    })
    expect(await screen.findByText('Pregunta enviada correctament.')).toBeInTheDocument()
  })
})
