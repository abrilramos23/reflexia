import { useEffect, useState } from 'react'
import { FaPlus, FaUser } from 'react-icons/fa'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage, formatEntryDate } from '../lib/entries.js'

export function TherapistQuestionsPage() {
  const { user, listAllTherapistQuestions, listTherapistPatients, createPatientQuestion } = useAuth()
  const [questions, setQuestions] = useState([])
  const [patients, setPatients] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isAddOpen, setIsAddOpen] = useState(false)
  const [newQuestion, setNewQuestion] = useState({
    patientId: '',
    text: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    let isCancelled = false

    async function loadData() {
      setIsLoading(true)
      try {
        const [questionsData, patientsData] = await Promise.all([
          listAllTherapistQuestions(),
          listTherapistPatients(),
        ])
        if (!isCancelled) {
          setQuestions(questionsData)
          setPatients(patientsData.filter(p => p.is_active))
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

    loadData()
    return () => {
      isCancelled = true
    }
  }, [listAllTherapistQuestions, listTherapistPatients])

  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'therapist') return <Navigate to="/dashboard" replace />

  const handleCreateQuestion = async (e) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')
    setIsSubmitting(true)

    try {
      const response = await createPatientQuestion(newQuestion.patientId, {
        text: newQuestion.text,
      })
      setSuccessMessage('Pregunta enviada correctament.')
      setNewQuestion({ patientId: '', text: '' })
      setIsAddOpen(false)
      
      const updatedQuestions = await listAllTherapistQuestions()
      setQuestions(updatedQuestions)
    } catch (err) {
      setError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsSubmitting(false)
    }
  }

  const activeQuestions = questions.filter(q => q.is_active)
  const historyQuestions = questions.filter(q => !q.is_active)

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Gestió de Preguntes</p>
            <h1 className="section-title">Gestiona les teves preguntes</h1>
            <p className="muted">
              Envia preguntes personalitzades als teus pacients per guiar el seu procés de reflexió. 
              Cada pacient només pot tenir una pregunta activa a la vegada.
            </p>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <button
            className="section-toggle"
            type="button"
            onClick={() => setIsAddOpen(!isAddOpen)}
          >
            <div className="panel-heading">
              <p className="eyebrow">Nova interacció</p>
              <h2>Envia una nova pregunta</h2>
            </div>
            <span className={`section-toggle-indicator ${isAddOpen ? 'section-toggle-indicator--open' : ''}`}>
              <FaPlus />
            </span>
          </button>

          {isAddOpen && (
            <div className="collapsible-section-body">
              <form className="form-stack" onSubmit={handleCreateQuestion}>
                <div className="field-group">
                  <label htmlFor="patient-select">Selecciona un pacient</label>
                  <select
                    id="patient-select"
                    value={newQuestion.patientId}
                    onChange={(e) => setNewQuestion({ ...newQuestion, patientId: e.target.value })}
                    required
                  >
                    <option value="">Selecciona un pacient...</option>
                    {patients.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.first_name} {p.last_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="field-group">
                  <label htmlFor="question-text">Pregunta</label>
                  <textarea
                    id="question-text"
                    value={newQuestion.text}
                    onChange={(e) => setNewQuestion({ ...newQuestion, text: e.target.value })}
                    placeholder="Què t'ha fet sentir millor aquesta setmana?"
                    required
                    style={{ minHeight: '100px' }}
                  />
                </div>

                <div className="button-row">
                  <button className="button-secondary" type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Enviant...' : 'Enviar pregunta'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </section>

        {successMessage && <div className="message" style={{ margin: '1rem 0' }}>{successMessage}</div>}
        {error && <div className="error-banner" style={{ margin: '1rem 0' }}>{error}</div>}

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Preguntes actives</p>
          </div>

          {isLoading ? (
            <p className="muted">Carregant preguntes...</p>
          ) : activeQuestions.length === 0 ? (
            <p className="muted">No hi ha preguntes actives actualment.</p>
          ) : (
            <div className="questions-list">
              {activeQuestions.map(q => (
                <div key={q.id} className="compact-list-item" style={{ padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <FaUser className="muted" size={14} />
                        <Link to={`/patients/${q.patient_id}`} style={{ fontWeight: 'bold', color: 'var(--brand-primary)', textDecoration: 'none' }}>
                          {q.patient_name}
                        </Link>
                        <span className="status-pill dashboard-status-pill--active">Activa</span>
                      </div>
                      <p style={{ fontSize: '1.05rem', margin: '0.5rem 0' }}>{q.question}</p>
                      <p className="muted" style={{ fontSize: '0.85rem' }}>
                        Enviada el {formatEntryDate(q.created_at)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Historial de preguntes</p>
          </div>

          {isLoading ? (
            <p className="muted">Carregant historial...</p>
          ) : historyQuestions.length === 0 ? (
            <p className="muted">L&apos;historial està buit.</p>
          ) : (
            <div className="questions-list">
              {historyQuestions.slice(0, 10).map(q => (
                <div key={q.id} className="compact-list-item" style={{ padding: '1rem', opacity: 0.8 }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Link to={`/patients/${q.patient_id}`} style={{ fontWeight: 'bold', textDecoration: 'none' }}>
                      {q.patient_name}
                    </Link>
                    <span className="status-pill dashboard-status-pill">Resolta</span>
                  </div>
                  <p style={{ fontSize: '0.95rem', margin: '0.4rem 0' }}>{q.question}</p>
                  <p className="muted" style={{ fontSize: '0.8rem' }}>
                    Del {formatEntryDate(q.created_at)}
                  </p>
                </div>
              ))}
              {historyQuestions.length > 10 && (
                <p className="muted" style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.9rem' }}>
                  Mostrant les darreres 10 preguntes de l&apos;historial.
                </p>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
