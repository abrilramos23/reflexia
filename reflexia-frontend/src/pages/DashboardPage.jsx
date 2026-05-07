import { Link, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { EmotionalEvolutionPanel } from '../components/EmotionalEvolutionPanel.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { consentDocumentUrl } from '../lib/api.js'
import { formatEntryDate } from '../lib/entries.js'
import { PlatformAdminDashboard } from './PlatformAdminDashboard.jsx'
import { ClinicAdminDashboard } from './ClinicAdminDashboard.jsx'

function formatRole(role) {
  if (role === 'therapist') return 'Terapeuta'
  if (role === 'patient') return 'Pacient'
  if (role === 'platform_admin') return 'Admin Plataforma'
  return 'Usuari'
}

function firstErrorMessage(error) {
  if (!error) {
    return 'S`ha produït un error inesperat.'
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

  return 'S`ha produït un error inesperat.'
}

function formatShortDate(value) {
  if (!value) {
    return 'Sense data'
  }

  try {
    return new Intl.DateTimeFormat('ca-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function sortByRegistrationDate(items) {
  return [...items].sort(
    (left, right) => new Date(right.registration_date).getTime() - new Date(left.registration_date).getTime(),
  )
}

function buildTherapistActivityItem(patient) {
  if (!patient.is_active) {
    return {
      label: 'Compte inactiu',
      description: 'Aquest pacient té el compte desactivat i no pot accedir a la plataforma.',
      tone: 'muted',
    }
  }

  if (!patient.consent_accepted) {
    return {
      label: 'Consentiment pendent',
      description: 'El pacient ja té el compte actiu, però encara no ha completat el consentiment informat.',
      tone: 'pending',
    }
  }

  return {
    label: 'Seguiment actiu',
    description: 'El pacient està actiu i amb el consentiment acceptat.',
    tone: 'active',
  }
}

export function DashboardPage() {
  const {
    user,
    isClinicAdmin,
    getMyEvolution,
    listEntries,
    listTherapistPatients,
    registerTherapist,
    getTherapistDashboardData,
    getEntriesEditorContext,
  } = useAuth()
  const [patientEvolution, setPatientEvolution] = useState(null)
  const [recentEntries, setRecentEntries] = useState([])
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [isEvolutionLoading, setIsEvolutionLoading] = useState(false)
  const [therapistPatients, setTherapistPatients] = useState([])
  const [therapistDashboardData, setTherapistDashboardData] = useState(null)
  const [isTherapistDataLoading, setIsTherapistDataLoading] = useState(false)
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
          const [patients, dashboardData] = await Promise.all([
            listTherapistPatients(),
            getTherapistDashboardData(),
          ])

          if (!isCancelled) {
            setTherapistPatients(sortByRegistrationDate(patients))
            setTherapistDashboardData(dashboardData)
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

  if (user.role === 'platform_admin') {
    return <PlatformAdminDashboard />
  }

  if (isClinicAdmin) {
    // We fall through to show the unified therapist/admin dashboard
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Tauler inicial</p>
            <h1 className="section-title">
              {user.role === 'therapist'
                ? 'Resum de la teva activitat.'
                : user.role === 'patient'
                  ? 'El teu espai personal.'
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
              <strong>
                {user.role === 'patient'
                  ? user.consent_accepted
                    ? 'Acceptat'
                    : 'Pendent'
                  : 'No aplica'}
              </strong>
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
                    <p className="muted">
                      Aquesta és una pregunta personalitzada del teu terapeuta per ajudar-te a aprofundir en el teu procés.
                    </p>
                  </>
                ) : (
                  <>
                    <h3 style={{ marginBlockEnd: '0' }}>Cap pregunta activa disponible</h3>
                    <p className="muted">
                      Quan el teu terapeuta publiqui una nova pregunta, la veuràs aquí per poder-la respondre.
                    </p>
                  </>
                )}
                <div className="button-row">
                  <Link
                    className="button-secondary"
                    style={{ marginBlockStart: '1rem', textDecoration: 'none' }}
                    to="/entries/new"
                  >
                    Obrir editor
                  </Link>
                </div>
              </div>
            </section>

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Entrades recents</p>
                <h2>El teu historial més recent</h2>
                <div className="button-row" style={{ marginBlockStart: '1rem' }}>
                  <Link className="button" style={{ textDecoration: 'none' }} to="/entries/new">
                    Escriure
                  </Link>
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
                              {entry.analysis ? entry.analysis.primary_emotion : 'Sense analisi'}
                            </span>
                          </div>
                          <p className="muted">{entry.preview}</p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <>
                    <h3>Encara no hi ha entrades disponibles</h3>
                    <p className="muted">
                      Quan escriguis les primeres entrades, aquí apareixeran ordenades de la més recent a la més antiga amb el resultat de l&apos;anàlisi emocional.
                    </p>
                    <p className="muted">
                      Et recomanem començar amb una primera entrada per tal que el sistema pugui començar a construir el teu context emocional.
                    </p>
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
                  <p className="muted">Com a administrador, tens accés a la configuració de l&apos;entitat i la gestió de l&apos;equip.</p>
                </div>
                <div className="button-row">
                  <Link className="button-secondary" style={{ textDecoration: 'none' }} to="/clinic">
                    Panell d&apos;Administrador
                  </Link>
                  <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/admin/therapists">
                    Gestionar Equip
                  </Link>
                </div>
              </section>
            )}

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Visió clínica</p>
                <h2>Panell d&apos;activitat del terapeuta</h2>
                <p className="muted">
                  Aquí tens una lectura ràpida de l&apos;estat actual dels teus pacients assignats i dels espais que requeriran revisió.
                </p>
              </div>

              <div className="dashboard-metrics-grid">
                <div className="dashboard-metric-card dashboard-metric-card--active">
                  <span>Pacients actius</span>
                  <strong>{therapistDashboardData?.metrics.active_patients ?? '-'}</strong>
                  <p>Total de pacients assignats amb accés actiu a la plataforma.</p>
                </div>

                <div className="dashboard-metric-card">
                  <span>Total d&apos;entrades</span>
                  <strong>{therapistDashboardData?.metrics.total_entries ?? '-'}</strong>
                  <p>Nombre total d&apos;entrades registrades pels teus pacients.</p>
                </div>

                <div className="dashboard-metric-card">
                  <span>Entrades d&apos;avui</span>
                  <strong>{therapistDashboardData?.metrics.entries_today ?? '-'}</strong>
                  <p>Entrades de journaling realitzades durant el dia d&apos;avui.</p>
                </div>

                <div className="dashboard-metric-card dashboard-metric-card--pending">
                  <span>Anàlisis pendents</span>
                  <strong>{therapistDashboardData?.metrics.pending_analyses ?? '-'}</strong>
                  <p>Entrades que encara no has revisat o corregit.</p>
                </div>
              </div>

              <div className="button-row" style={{ marginTop: '1rem' }}>
                <Link className="button" style={{ textDecoration: 'none' }} to="/patients">
                  Veure pacients
                </Link>
              </div>
            </section>

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Activitat recent</p>
                <h2>Últimes entrades dels teus pacients</h2>
                <p className="muted">
                  Segueix de prop l&apos;activitat més recent per detectar canvis d&apos;estat o riscos en temps real.
                </p>
              </div>

              <div className="content-card section-stack">
                {isTherapistDataLoading ? (
                  <p className="muted">Carregant activitat...</p>
                ) : therapistDashboardData?.recent_activity.length ? (
                  <ul className="patient-list">
                    {therapistDashboardData.recent_activity.map((item) => (
                      <li className="compact-list-item" key={item.id}>
                        <Link to={`/patients/${item.patient_id}/entries/${item.id}`} style={{ textDecoration: 'none' }}>
                          <div className="item-heading-row">
                            <strong>{item.patient_name}</strong>
                            <span className="muted">•</span>
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
