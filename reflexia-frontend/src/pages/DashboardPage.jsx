import { Link, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { FaPlus } from 'react-icons/fa'
import { EmotionalEvolutionPanel } from '../components/EmotionalEvolutionPanel.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { formatEntryDate, formatEntryStatus, formatRiskLevel } from '../lib/entries.js'

function formatRole(role) {
  if (role === 'therapist') return 'Terapeuta'
  if (role === 'patient') return 'Pacient'
  return 'Usuari'
}

function firstErrorMessage(error) {
  if (!error) {
    return 'S’ha produït un error inesperat.'
  }

  if (typeof error === 'string') {
    return error
  }

  const firstEntry = Object.values(error)[0]

  if (Array.isArray(firstEntry)) {
    return String(firstEntry[0])
  }

  if (typeof firstEntry === 'string') {
    return firstEntry
  }

  return 'S’ha produït un error inesperat.'
}

function sortByRegistrationDate(items) {
  return [...items].sort(
    (left, right) => new Date(right.registration_date).getTime() - new Date(left.registration_date).getTime(),
  )
}

export function DashboardPage() {
  const {
    user,
    isClinicAdmin,
    getMyEvolution,
    listEntries,
    listTherapistPatients,
    listPatientEntries,
    registerTherapist,
    getTherapistDashboardData,
    getEntriesEditorContext,
    api,
  } = useAuth()
  const [patientEvolution, setPatientEvolution] = useState(null)
  const [recentEntries, setRecentEntries] = useState([])
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [isEvolutionLoading, setIsEvolutionLoading] = useState(false)
  const [therapistPatients, setTherapistPatients] = useState([])
  const [therapistDashboardData, setTherapistDashboardData] = useState(null)
  const [therapistAlerts, setTherapistAlerts] = useState([])
  const [isTherapistDataLoading, setIsTherapistDataLoading] = useState(false)
  const [selectedEntryMetric, setSelectedEntryMetric] = useState(null)
  const [metricEntries, setMetricEntries] = useState([])
  const [metricEntriesError, setMetricEntriesError] = useState('')
  const [isMetricEntriesLoading, setIsMetricEntriesLoading] = useState(false)
  const [therapistInviteForm, setTherapistInviteForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    license_number: '',
    specialty: '',
  })
  const [inviteMessage, setInviteMessage] = useState('')
  const [inviteError, setInviteError] = useState('')
  const [isSubmittingInvite, setIsSubmittingInvite] = useState(false)
  const [dashboardError, setDashboardError] = useState('')

  if (!user) {
    return <Navigate to="/login" replace />
  }

  useEffect(() => {
    let isCancelled = false

    async function loadDashboardData() {
      setDashboardError('')

      try {
        if (user.role === 'patient') {
          setIsEvolutionLoading(true)
          const [evolution, entries, context] = await Promise.all([
            getMyEvolution(),
            listEntries(),
            getEntriesEditorContext(),
          ])

          if (!isCancelled) {
            setPatientEvolution(evolution)
            setRecentEntries(entries.slice(0, 3))
            setActiveQuestion(context.active_question)
          }
        }

        if (user.role === 'therapist' || isClinicAdmin) {
          setIsTherapistDataLoading(true)
          const [patients, dashboardData, alertsResponse] = await Promise.all([
            listTherapistPatients(),
            getTherapistDashboardData(),
            api.get('/alerts/'),
          ])

          if (!isCancelled) {
            setTherapistPatients(sortByRegistrationDate(patients))
            setTherapistDashboardData(dashboardData)
            setTherapistAlerts(alertsResponse.data)
          }
        }
      } catch (error) {
        if (!isCancelled) {
          setDashboardError(firstErrorMessage(error.response?.data || error))
        }
      } finally {
        if (!isCancelled) {
          setIsEvolutionLoading(false)
          setIsTherapistDataLoading(false)
        }
      }
    }

    loadDashboardData()

    return () => {
      isCancelled = true
    }
  }, [user.role])

  async function handleTherapistInviteSubmit(event) {
    event.preventDefault()
    setInviteError('')
    setInviteMessage('')
    setIsSubmittingInvite(true)

    try {
      const response = await registerTherapist(therapistInviteForm)
      setInviteMessage(
        response.activation_email_sent
          ? `Invitació enviada correctament a ${response.email}. El terapeuta haurà d'activar el compte des del correu.`
          : 'Terapeuta registrat correctament.',
      )
      setTherapistInviteForm({
        first_name: '',
        last_name: '',
        email: '',
        license_number: '',
        specialty: '',
      })
    } catch (error) {
      setInviteError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsSubmittingInvite(false)
    }
  }

  async function handleEntryMetricClick(metric) {
    setSelectedEntryMetric(metric)
    setMetricEntriesError('')
    setIsMetricEntriesLoading(true)

    try {
      const patientsWithEntries = await Promise.all(
        therapistPatients.map(async (patient) => {
          const entries = await listPatientEntries(patient.id)
          return entries.map((entry) => ({
            ...entry,
            patient_id: patient.id,
            patient_name: `${patient.first_name} ${patient.last_name}`,
          }))
        }),
      )

      const todayKey = new Date().toDateString()
      const entries = patientsWithEntries
        .flat()
        .filter((entry) => {
          if (metric === 'today') {
            return new Date(entry.created_at).toDateString() === todayKey
          }

          if (metric === 'pending_analyses') {
            return entry.analysis?.reviewed_by_therapist === false
          }

          return true
        })
        .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())

      setMetricEntries(entries)
    } catch (error) {
      setMetricEntries([])
      setMetricEntriesError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsMetricEntriesLoading(false)
    }
  }

  const pendingAlerts = therapistAlerts.filter((alert) => alert.status === 'pending')
  const highRiskAlerts = therapistAlerts.filter((alert) => alert.risk_level === 'high')
  const priorityAlerts = therapistAlerts
    .filter((alert) => alert.status === 'pending' || alert.risk_level === 'high')
    .slice(0, 3)
  const hasPriorityAlerts = pendingAlerts.length > 0 || highRiskAlerts.length > 0
  const selectedMetricConfig = selectedEntryMetric ? entryMetricConfigs[selectedEntryMetric] : null

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <h1 className="section-title">
              {user.role === 'therapist'
                ? 'Resum de la teva activitat'
                : user.role === 'patient'
                  ? 'El teu espai personal'
                  : 'Compte actiu'}
            </h1>
          </div>

          {dashboardError ? <div className="error-banner">{dashboardError}</div> : null}

          <div className="stat-list">
            <div className="stat-card">
              <span>Rol</span>
              <strong>{formatRole(user.role)}</strong>
            </div>
            <div className="stat-card">
              <span>2FA</span>
              <strong>{user.two_factor_enabled ? 'Activat' : 'No activat'}</strong>
            </div>
            <div className="stat-card">
              <span>Consentiment</span>
              <strong>{user.legal_terms_accepted ? 'Acceptat' : 'Pendent'}</strong>
            </div>
          </div>
        </section>

        {user.role === 'patient' ? (
          <>
            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Evolució emocional</p>
              </div>

              <EmotionalEvolutionPanel evolution={patientEvolution} isLoading={isEvolutionLoading} />
            </section>

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow" style={{ marginBlockEnd: '0' }}>Pregunta activa</p>
              </div>

              <div className="content-card section-stack">
                {activeQuestion ? (
                  <>
                    <h3 style={{ marginBlockEnd: '0' }}>{activeQuestion.text}</h3>
                  </>
                ) : (
                  <>
                    <p className="muted" style={{ marginBlockEnd: '0' }}>Cap pregunta activa disponible</p>
                  </>
                )}
              </div>
            </section>

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Entrades recents</p>
                <div style={{ display: 'flex', flexDirection: 'row', gap: '10px', justifyContent: 'space-between' }}>
                  <h2 style={{ marginBlockEnd: '0' }}>El teu historial més recent</h2>
                  <div className="button-row">
                    <Link className="button" style={{ textDecoration: 'none' }} to="/entries/new">
                      <FaPlus />
                      Escriure
                    </Link>
                  </div>
                </div>
              </div>

              <div className="content-card section-stack">
                {recentEntries.length ? (
                  <ul className="patient-list">
                    {recentEntries.map((entry) => (
                      <li className="compact-list-item" key={entry.id}>
                        <Link to={`/entries/${entry.id}`} style={{ textDecoration: 'none' }}>
                          <div className="item-heading-row">
                            <strong>{formatEntryDate(entry.updated_at)}</strong>
                            <span className="status-pill">
                              {entry.analysis ? entry.analysis.primary_emotion : 'Sense anàlisi'}
                            </span>
                          </div>
                          <p className="muted">{entry.preview}</p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <>
                    <p className="muted">Encara no hi ha entrades disponibles</p>
                  </>
                )}
              </div>
            </section>
          </>
        ) : null}

        {user.role === 'therapist' || isClinicAdmin ? (
          <>
            {isClinicAdmin && (
              <section className="screen-card dashboard-panel profile-card--wide">
                <div className="panel-heading">
                  <p className="eyebrow">Administració</p>
                  <h2>Gestió de la Clínica</h2>
                </div>
                <div className="button-row">
                  <Link className="button-secondary" style={{ textDecoration: 'none' }} to="/clinic">
                    Gestionar clínica
                  </Link>
                  <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/admin/therapists">
                    Gestionar equip
                  </Link>
                </div>
              </section>
            )}

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Visió clínica</p>
              </div>

              {!isTherapistDataLoading ? (
                <Link
                  to="/alerts"
                  className={`dashboard-metric-card dashboard-alert-summary ${hasPriorityAlerts ? 'dashboard-metric-card--alert' : ''}`}
                >
                  <div className="item-heading-row">
                    <strong>Alertes clíniques</strong>
                  </div>
                  <p>
                    {hasPriorityAlerts
                      ? 'Revisa primer els casos pendents o amb risc alt.'
                      : 'No hi ha alertes pendents ni de risc alt ara mateix.'}
                  </p>
                  <div className="entries-toolbar">
                    <span className="status-pill dashboard-status-pill--pending">
                      {pendingAlerts.length} pendents
                    </span>
                    <span className="status-pill risk-pill--high">
                      {highRiskAlerts.length} risc alt
                    </span>
                  </div>
                </Link>
              ) : null}

              <div className="dashboard-metrics-grid">
                <Link className="dashboard-metric-card dashboard-metric-card--active" to="/patients" style={{ textDecoration: 'none' }}>
                  <span style={{ fontWeight: 'bold' }}>Pacients actius</span>
                  <strong>{therapistDashboardData?.metrics.active_patients ?? '-'}</strong>
                </Link>

                <button
                  className={`dashboard-metric-card dashboard-metric-card--button ${selectedEntryMetric === 'all' ? 'dashboard-metric-card--selected' : ''}`}
                  type="button"
                  onClick={() => handleEntryMetricClick('all')}
                >
                  <span style={{ fontWeight: 'bold' }}>Total d&apos;entrades</span>
                  <strong>{therapistDashboardData?.metrics.total_entries ?? '-'}</strong>
                </button>

                <button
                  className={`dashboard-metric-card dashboard-metric-card--button ${selectedEntryMetric === 'today' ? 'dashboard-metric-card--selected' : ''}`}
                  type="button"
                  onClick={() => handleEntryMetricClick('today')}
                >
                  <span style={{ fontWeight: 'bold' }}>Entrades d&apos;avui</span>
                  <strong>{therapistDashboardData?.metrics.entries_today ?? '-'}</strong>
                </button>

                <button
                  className={`dashboard-metric-card dashboard-metric-card--button dashboard-metric-card--pending ${selectedEntryMetric === 'pending_analyses' ? 'dashboard-metric-card--selected' : ''}`}
                  type="button"
                  onClick={() => handleEntryMetricClick('pending_analyses')}
                >
                  <span style={{ fontWeight: 'bold' }}>Anàlisis pendents</span>
                  <strong>{therapistDashboardData?.metrics.pending_analyses ?? '-'}</strong>
                </button>
              </div>
            </section>

            {selectedMetricConfig ? (
              <section className="screen-card dashboard-panel profile-card--wide">
                <div className="panel-heading" style={{ marginBottom: '0rem' }}>
                  <p className="eyebrow">{selectedMetricConfig.eyebrow}</p>
                  <h2>{selectedMetricConfig.title}</h2>
                </div>

                <div className="content-card section-stack">
                  {metricEntriesError ? <div className="error-banner">{metricEntriesError}</div> : null}
                  {isMetricEntriesLoading ? (
                    <p className="muted">Carregant entrades...</p>
                  ) : metricEntries.length ? (
                    <ul className="patient-list">
                      {metricEntries.map((entry) => (
                        <li className={`compact-list-item ${riskItemClassName(entry.analysis?.risk_level)}`} key={entry.id}>
                          <Link to={`/patients/${entry.patient_id}/entries/${entry.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block', width: '100%' }}>
                            <div className="item-heading-row">
                              <strong>{entry.patient_name}</strong>
                              <span>{formatEntryDate(entry.created_at)}</span>
                              <span className="status-pill">{formatEntryStatus(entry)}</span>
                            </div>
                            <p className="muted">{entry.preview}</p>
                            <div className="entries-toolbar">
                              <span className={`status-pill risk-pill--${entry.analysis?.risk_level || 'none'}`}>
                                {formatRiskLevel(entry.analysis?.risk_level)}
                              </span>
                              {entry.analysis?.reviewed_by_therapist === false ? (
                                <span className="status-pill dashboard-status-pill--pending">Pendent de revisió</span>
                              ) : null}
                            </div>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted">{selectedMetricConfig.empty}</p>
                  )}
                </div>
              </section>
            ) : null}

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading" style={{ marginBottom: '0rem' }}>
                <p className="eyebrow">Activitat recent dels pacients</p>
              </div>

              <div className="content-card section-stack">
                {isTherapistDataLoading ? (
                  <p className="muted">Carregant activitat...</p>
                ) : therapistDashboardData?.recent_activity.length ? (
                  <ul className="patient-list">
                    {therapistDashboardData.recent_activity.map((item) => (
                      <li className={`compact-list-item ${riskItemClassName(item.risk_level)}`} key={item.id}>
                        <Link to={`/patients/${item.patient_id}/entries/${item.id}`} style={{ textDecoration: 'none' }}>
                          <div className="item-heading-row">
                            <strong>{item.patient_name}</strong>
                            <span className="muted"> </span>
                            <span>{formatEntryDate(item.updated_at)}</span>
                            {item.primary_emotion ? (
                              <span className={`status-pill risk-pill--${item.risk_level?.toLowerCase() || 'none'}`}>
                                {item.primary_emotion}
                              </span>
                            ) : (
                              <span className="status-pill">Sense anàlisi</span>
                            )}
                          </div>
                          <p className="muted">{item.preview}</p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Encara no hi ha activitat recent dels teus pacients.</p>
                )}
              </div>
            </section>
          </>
        ) : null}


      </div>
    </div>
  )
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

const entryMetricConfigs = {
  all: {
    eyebrow: 'Entrades dels pacients',
    title: 'Totes les entrades',
    empty: 'Encara no hi ha entrades dels teus pacients.',
  },
  today: {
    eyebrow: 'Entrades dels pacients',
    title: 'Entrades creades avui',
    empty: 'Avui encara no hi ha cap entrada.',
  },
  pending_analyses: {
    eyebrow: 'Revisió clínica',
    title: 'Entrades amb anàlisi pendent',
    empty: 'No hi ha anàlisis pendents de revisió.',
  },
}
