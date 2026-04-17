import { useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage, formatEntryDate, formatEntryStatus } from '../lib/entries.js'

export function PatientDetailPage() {
  const { user, getPatient, listPatientEntries, listPatientQuestions } = useAuth()
  const { patientId } = useParams()
  
  const [patient, setPatient] = useState(null)
  const [entries, setEntries] = useState([])
  const [questions, setQuestions] = useState([])
  const [activeTab, setActiveTab] = useState('entries') // 'entries' | 'questions'
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isCancelled = false

    async function loadData() {
      setIsLoading(true)
      setError('')
      try {
        const [patientData, entriesData, questionsData] = await Promise.all([
          getPatient(patientId),
          listPatientEntries(patientId),
          listPatientQuestions(patientId)
        ])

        if (!isCancelled) {
          setPatient(patientData)
          setEntries(entriesData)
          setQuestions(questionsData)
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
  }, [patientId, getPatient, listPatientEntries, listPatientQuestions])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'therapist') {
    return <Navigate to="/dashboard" replace />
  }

  if (isLoading) {
    return (
      <div className="screen-shell">
        <div className="profile-grid">
          <section className="screen-card dashboard-panel profile-card--wide">
            <p className="muted">Carregant dades del pacient...</p>
          </section>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="screen-shell">
        <div className="profile-grid">
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="error-banner">{error}</div>
            <Link to="/patients" className="button-ghost" style={{ textDecoration: 'none' }}>
              Tornar a la llista
            </Link>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        {/* Patient Header Card */}
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row" style={{ marginBottom: '1rem' }}>
            <Link to="/patients" className="button-ghost" style={{ textDecoration: 'none' }}>
              ← Tornar
            </Link>
          </div>
          <div className="panel-heading">
            <p className="eyebrow">Detall del Pacient</p>
            <h1 className="section-title">{patient.first_name} {patient.last_name}</h1>
            <div className="entries-toolbar" style={{ marginTop: '0.5rem' }}>
              <span className={`status-pill ${patient.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--muted'}`}>
                {patient.is_active ? 'Compte actiu' : 'Compte inactiu'}
              </span>
              <span className={`status-pill ${patient.consent_accepted ? 'dashboard-status-pill--active' : 'dashboard-status-pill--pending'}`}>
                Consentiment: {patient.consent_accepted ? 'Acceptat' : 'Pendent'}
              </span>
            </div>
            <p className="muted" style={{ marginTop: '1rem' }}>
              <strong>Email:</strong> {patient.email} <br />
              <strong>Data de naixement:</strong> {patient.birth_date} <br />
              <strong>Data de registre:</strong> {new Date(patient.registration_date).toLocaleDateString()}
            </p>
          </div>
        </section>

        {/* Emotional Evolution Placeholder */}
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Evolució emocional</p>
            <h3>Gràfics de seguiment</h3>
            <p className="muted">L&apos;evolució emocional estarà disponible properament.</p>
          </div>
          <div style={{ height: '100px', display: 'grid', placeItems: 'center', background: 'rgba(0,0,0,0.03)', borderRadius: '16px', border: '1px dashed rgba(0,0,0,0.1)' }}>
             <p className="muted">Evolució emocional (Pròximament)</p>
          </div>
        </section>

        {/* Tabs Control */}
        <section className="screen-card dashboard-panel profile-card--wide" style={{ paddingBottom: 0 }}>
          <div className="entries-toolbar" style={{ borderBottom: '1px solid rgba(0,0,0,0.1)', gap: '2rem' }}>
            <button 
              className={`text-link ${activeTab === 'entries' ? '' : 'muted'}`} 
              onClick={() => setActiveTab('entries')}
              style={{ paddingBottom: '0.75rem', borderBottom: activeTab === 'entries' ? '2px solid var(--brand-deep)' : 'none', textDecoration: 'none' }}
            >
              Entrades ({entries.length})
            </button>
            <button 
              className={`text-link ${activeTab === 'questions' ? '' : 'muted'}`} 
              onClick={() => setActiveTab('questions')}
              style={{ paddingBottom: '0.75rem', borderBottom: activeTab === 'questions' ? '2px solid var(--brand-deep)' : 'none', textDecoration: 'none' }}
            >
              Preguntes ({questions.length})
            </button>
          </div>
        </section>

        {/* Tab Content */}
        <section className="screen-card dashboard-panel profile-card--wide">
          {activeTab === 'entries' ? (
            <div className="page-stack">
              {entries.length === 0 ? (
                <p className="muted">El pacient encara no ha creat cap entrada.</p>
              ) : (
                <ul className="patient-list">
                  {entries.map((entry) => (
                    <li key={entry.id} className="compact-list-item">
                      <Link to={`/patients/${patientId}/entries/${entry.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block', width: '100%' }}>
                        <div className="item-heading-row">
                          <strong>{formatEntryDate(entry.created_at)}</strong>
                          <span className="status-pill">{formatEntryStatus(entry)}</span>
                        </div>
                        <p className="muted" style={{ margin: '0.5rem 0' }}>{entry.preview}</p>
                        {entry.therapist_question && (
                          <span className="status-pill dashboard-status-pill--active" style={{ fontSize: '0.75rem' }}>
                            Respondre a: {entry.therapist_question.question.substring(0, 30)}...
                          </span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <div className="page-stack">
              {questions.length === 0 ? (
                <p className="muted">No s&apos;han assignat preguntes a aquest pacient.</p>
              ) : (
                <ul className="patient-list">
                  {questions.map((q) => (
                    <li key={q.id} className="compact-list-item">
                      <Link to={`/patients/${patientId}/questions/${q.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block', width: '100%' }}>
                        <div className="item-heading-row">
                          <span className={`status-pill ${q.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--muted'}`}>
                            {q.is_active ? 'Activa' : 'Inactiva'}
                          </span>
                          <span className="muted" style={{ fontSize: '0.85rem' }}>{formatEntryDate(q.created_at)}</span>
                        </div>
                        <p style={{ margin: '0.5rem 0' }}>{q.question}</p>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
