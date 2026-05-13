import { useEffect, useState } from 'react'
import { FaArrowLeft } from 'react-icons/fa'
import { Link, Navigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage, formatEntryDate } from '../lib/entries.js'

export function TherapistQuestionDetailPage() {
  const { user, getPatientQuestion } = useAuth()
  const { patientId, questionId } = useParams()
  const [question, setQuestion] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isCancelled = false
    async function loadQuestion() {
      setIsLoading(true)
      try {
        const data = await getPatientQuestion(patientId, questionId)
        if (!isCancelled) {
          setQuestion(data)
        }
      } catch (err) {
        if (!isCancelled) {
          setError(firstErrorMessage(err.response?.data || err))
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }
    loadQuestion()
    return () => { isCancelled = true }
  }, [patientId, questionId, getPatientQuestion])

  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'therapist') return <Navigate to="/dashboard" replace />

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
           <div className="button-row">
            <Link to={`/patients/${patientId}`} className="button-ghost" title="Tornar" aria-label="Tornar">
              <FaArrowLeft />
            </Link>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          {isLoading ? (
            <p className="muted">Carregant pregunta...</p>
          ) : error ? (
            <div className="error-banner">{error}</div>
          ) : question ? (
            <>
              <div className="panel-heading">
                <p className="eyebrow">Pregunta del Terapeuta</p>
                <h1 className="section-title">Detall de la pregunta</h1>
                <p className="muted">
                  Creada el {formatEntryDate(question.created_at)}.
                </p>
              </div>

              <div className="entries-toolbar" style={{ margin: '1.5rem 0' }}>
                <span className={`status-pill ${question.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--muted'}`}>
                  {question.is_active ? 'Pregunta activa' : 'Pregunta resolta'}
                </span>
              </div>

              <div className="content-card section-stack">
                <h3>Pregunta</h3>
                <p style={{ fontSize: '1.1rem', lineHeight: '1.6' }}>{question.question}</p>
              </div>
            </>
          ) : null}
        </section>
      </div>
    </div>
  )
}
