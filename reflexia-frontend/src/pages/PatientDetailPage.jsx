import { useEffect, useState } from 'react'
import { FaArrowLeft } from 'react-icons/fa'
import { Link, Navigate, useParams } from 'react-router-dom'
import { EmotionalEvolutionPanel } from '../components/EmotionalEvolutionPanel.jsx'
import { PrivateNotesPanel } from '../components/PrivateNotesPanel.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage, formatEntryDate, formatEntryStatus, formatRiskLevel } from '../lib/entries.js'

export function PatientDetailPage() {
  const {
    user,
    api,
    getPatient,
    getPatientEvolution,
    listPatientEntries,
    listPatientQuestions,
    createPatientQuestion,
    listPatientNotes,
    createPatientNote,
    updatePatientNote,
    deletePatientNote,
    exportPatientEntriesPdf,
  } = useAuth()
  const { patientId } = useParams()
  
  const [patient, setPatient] = useState(null)
  const [entries, setEntries] = useState([])
  const [questions, setQuestions] = useState([])
  const [notes, setNotes] = useState([])
  const [alerts, setAlerts] = useState([])
  const [evolution, setEvolution] = useState(null)
  const [activeTab, setActiveTab] = useState('entries') 
  const [newQuestionText, setNewQuestionText] = useState('')
  const [questionMessage, setQuestionMessage] = useState('')
  const [isCreatingQuestion, setIsCreatingQuestion] = useState(false)
  const [isExportingEntries, setIsExportingEntries] = useState(false)
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isCancelled = false

    async function loadData() {
      setIsLoading(true)
      setError('')
      try {
        const [patientData, entriesData, questionsData, notesData, evolutionData, alertsResponse] = await Promise.all([
          getPatient(patientId),
          listPatientEntries(patientId),
          listPatientQuestions(patientId),
          listPatientNotes(patientId),
          getPatientEvolution(patientId),
          api.get('/alerts/', { params: { patient_id: patientId } }),
        ])

        if (!isCancelled) {
          setPatient(patientData)
          setEntries(entriesData)
          setQuestions(questionsData)
          setNotes(notesData)
          setEvolution(evolutionData)
          setAlerts(alertsResponse.data)
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
  }, [patientId, getPatient, getPatientEvolution, listPatientEntries, listPatientQuestions, listPatientNotes])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'therapist') {
    return <Navigate to="/dashboard" replace />
  }

  async function handleCreateQuestion(event) {
    event.preventDefault()
    setQuestionMessage('')
    setError('')
    setIsCreatingQuestion(true)

    try {
      const response = await createPatientQuestion(patientId, { text: newQuestionText })
      setQuestions((currentQuestions) => [response.question, ...currentQuestions])
      setNewQuestionText('')
      setQuestionMessage(response.message)
      setActiveTab('questions')
    } catch (err) {
      setError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsCreatingQuestion(false)
    }
  }

  async function handleExportEntries() {
    setQuestionMessage('')
    setError('')
    setIsExportingEntries(true)

    try {
      const { blob, filename } = await exportPatientEntriesPdf(patientId)
      triggerBrowserDownload(blob, filename)
    } catch (err) {
      setError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsExportingEntries(false)
    }
  }

  async function handleCreateNote(content) {
    const response = await createPatientNote(patientId, { content })
    setNotes((currentNotes) => [response.note, ...currentNotes])
    return response
  }

  async function handleUpdateNote(noteId, content) {
    const response = await updatePatientNote(patientId, noteId, { content })
    setNotes((currentNotes) => currentNotes.map((note) => (note.id === noteId ? response.note : note)))
    return response
  }

  async function handleDeleteNote(noteId) {
    const response = await deletePatientNote(patientId, noteId)
    setNotes((currentNotes) => currentNotes.filter((note) => note.id !== noteId))
    return response
  }

  const pendingAlerts = alerts.filter((alert) => alert.status === 'pending')
  const highRiskAlerts = alerts.filter((alert) => alert.risk_level === 'high')
  const priorityAlerts = alerts
    .filter((alert) => alert.status === 'pending' || alert.risk_level === 'high')
    .slice(0, 4)

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

  if (error && !patient) {
    return (
      <div className="screen-shell">
        <div className="profile-grid">
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="error-banner">{error}</div>
            <Link to="/patients" className="button-ghost" style={{ textDecoration: 'none' }} icon="arrow-left">
            </Link>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Link to="/patients" className="button-ghost" style={{ textDecoration: 'none' }} title="Tornar" aria-label="Tornar">
              <FaArrowLeft />
            </Link>
            <button className="button-secondary" type="button" disabled={isExportingEntries} onClick={handleExportEntries}>
              {isExportingEntries ? 'Generant PDF...' : 'Exportar historial PDF'}
            </button>
          </div>
        </section>
        <section className="screen-card dashboard-panel profile-card--wide">
          {error ? <div className="error-banner">{error}</div> : null}
          <div className="panel-heading">
            <p className="eyebrow">Detall del Pacient</p>
            <h1 className="section-title">{patient.first_name} {patient.last_name}</h1>
            <div className="entries-toolbar" style={{ marginTop: '0.5rem' }}>
              <span className={`status-pill ${patient.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--muted'}`}>
                {patient.is_active ? 'Compte actiu' : 'Compte inactiu'}
              </span>
              <span className={`status-pill ${patient.consent_accepted ? 'dashboard-status-pill--active' : 'dashboard-status-pill--pending'}`}>
                Consentiment {patient.consent_accepted ? 'acceptat' : 'pendent'}
              </span>
            </div>
            <p className="muted" style={{ marginTop: '1rem' }}>
              <strong>Email:</strong> {patient.email} <br />
              <strong>Data de naixement:</strong> {patient.birth_date ? new Date(patient.birth_date).toLocaleDateString() : 'No disponible'} <br />
              <strong>Data de registre:</strong> {new Date(patient.registration_date).toLocaleDateString()}
            </p>
          </div>
        </section>

        <section className={`screen-card dashboard-panel profile-card--wide patient-alert-panel ${priorityAlerts.length ? 'patient-alert-panel--urgent' : ''}`}>
          <div className="panel-heading">
            <p className="eyebrow">Alertes del pacient</p>
            <div className="entries-toolbar">
              <span className="status-pill dashboard-status-pill--pending">
                {pendingAlerts.length} pendents
              </span>
              <span className="status-pill risk-pill--high">
                {highRiskAlerts.length} risc alt
              </span>
              <span className="status-pill dashboard-status-pill--muted">
                {alerts.length} totals
              </span>
            </div>
          </div>

          {priorityAlerts.length ? (
            <ul className="patient-list">
              {priorityAlerts.map((alert) => (
                <li key={alert.id} className={`compact-list-item ${alertListItemClassName(alert)}`}>
                  <Link to={`/alerts/${alert.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
                    <div className="item-heading-row">
                      <strong>{formatRiskLevel(alert.risk_level)}</strong>
                      <span className={`status-pill ${alertStatusClassName(alert.status)}`}>
                        {formatAlertStatus(alert.status)}
                      </span>
                      <span className="muted">{formatEntryDate(alert.created_at)}</span>
                    </div>
                    <p className="muted" style={{ margin: 0 }}>
                      Entrada associada: {formatEntryDate(alert.entry_date)}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted" style={{ margin: 0 }}>Aquest pacient no té alertes pendents ni de risc alt.</p>
          )}
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Evolució emocional</p>
          </div>
          <EmotionalEvolutionPanel evolution={evolution} />
        </section>

        <section className="screen-card dashboard-panel profile-card--wide" style={{ gap: '0' }}>
          <div className="entries-toolbar" style={{ borderBottom: '1px solid rgba(0,0,0,0.1)', gap: '2rem', display: 'flex', marginBottom: '1rem' }}>
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
            <button
              className={`text-link ${activeTab === 'notes' ? '' : 'muted'}`}
              onClick={() => setActiveTab('notes')}
              style={{ paddingBottom: '0.75rem', borderBottom: activeTab === 'notes' ? '2px solid var(--brand-deep)' : 'none', textDecoration: 'none' }}
            >
              Notes ({notes.length})
            </button>
          </div>

          {questionMessage ? <div className="message">{questionMessage}</div> : null}
          {activeTab === 'entries' ? (
            <div className="page-stack">
              {entries.length === 0 ? (
                <p className="muted">El pacient encara no ha creat cap entrada.</p>
              ) : (
                <ul className="patient-list">
                  {entries.map((entry) => (
                    <li key={entry.id} className={`compact-list-item ${riskItemClassName(entry.analysis?.risk_level)}`}>
                      <Link to={`/patients/${patientId}/entries/${entry.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block', width: '100%' }}>
                        <div className="item-heading-row">
                          <strong>{formatEntryDate(entry.created_at)}</strong>
                          <span className="status-pill">{formatEntryStatus(entry)}</span>
                        </div>
                        <p className="muted" style={{ margin: '0.5rem 0' }}>{entry.preview}</p>
                        <span className={`status-pill risk-pill--${entry.analysis?.risk_level || 'none'}`} style={{ fontSize: '0.75rem' }}>
                          {formatRiskLevel(entry.analysis?.risk_level)}
                        </span>
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
          ) : activeTab === 'questions' ? (
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
                            {q.is_active ? 'Activa' : 'Resolta'}
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
          ) : (
            <PrivateNotesPanel
              notes={notes}
              onCreateNote={handleCreateNote}
              onUpdateNote={handleUpdateNote}
              onDeleteNote={handleDeleteNote}
            />
          )}
        </section>
      </div>
    </div>
  )
}

function formatAlertStatus(status) {
  const labels = {
    pending: 'Pendent',
    validated: 'Validada',
    dismissed: 'Descartada',
  }

  return labels[status] || status || 'Sense estat'
}

function alertStatusClassName(status) {
  if (status === 'validated') {
    return 'dashboard-status-pill--active'
  }

  if (status === 'dismissed') {
    return 'dashboard-status-pill--muted'
  }

  return 'dashboard-status-pill--pending'
}

function alertListItemClassName(alert) {
  if (alert.risk_level === 'high') {
    return 'alert-list-item alert-list-item--high'
  }

  if (alert.status === 'pending') {
    return 'alert-list-item alert-list-item--pending'
  }

  return 'alert-list-item'
}

function riskItemClassName(riskLevel) {
  if (riskLevel === 'high') {
    return 'clinical-risk-item clinical-risk-item--high'
  }

  if (riskLevel === 'moderate') {
    return 'clinical-risk-item clinical-risk-item--moderate'
  }

  return ''
}

function triggerBrowserDownload(blob, filename) {
  const fileUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = fileUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(fileUrl)
}
