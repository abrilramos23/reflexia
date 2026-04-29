import { Link, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { consentDocumentUrl } from '../lib/api.js'
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
    description: 'El pacient està actiu i amb el consentiment acceptat, preparat per continuar el seguiment.',
    tone: 'active',
  }
}

export function DashboardPage() {
  const {
    user,
    isClinicAdmin,
    listAssociatedContacts,
    listTherapistPatients,
    registerTherapist,
  } = useAuth()
  const [patientContactsCount, setPatientContactsCount] = useState(0)
  const [defaultContactsCount, setDefaultContactsCount] = useState(0)
  const [therapistPatients, setTherapistPatients] = useState([])
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
          const contacts = await listAssociatedContacts()

          if (!isCancelled) {
            setPatientContactsCount(contacts.length)
            setDefaultContactsCount(
              contacts.filter((contact) => contact.is_default).length,
            )
          }
        }

        if (user.role === 'therapist') {
          const patients = await listTherapistPatients()

          if (!isCancelled) {
            setTherapistPatients(sortByRegistrationDate(patients))
          }
        }
      } catch (error) {
        if (!isCancelled) {
          setDashboardError(firstErrorMessage(error.response?.data || error))
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
          ? `Invitació enviada correctament a ${response.email}. El terapeuta haurà d’activar el compte des del correu.`
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
    return <ClinicAdminDashboard />
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Tauler inicial</p>
            <h1 className="section-title">
              {user.role === 'therapist'
                ? 'Visió general de la teva activitat clínica.'
                : user.role === 'patient'
                  ? 'El teu espai personal de Reflexia.'
                  : 'Compte actiu i llest per continuar.'}
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
                <p className="eyebrow" style={{ marginBlockEnd: '0' }}>Pregunta activa</p>
              </div>

              <div className="content-card section-stack">
                <h3 style={{ marginBlockEnd: '0' }}>Cap pregunta activa disponible</h3>
                <p className="muted">
                  Quan el teu terapeuta publiqui una nova pregunta de seguiment, la veuràs aquí per poder-la respondre.
                </p>
                <div className="button-row">
                  <Link className="button-secondary" style={{ marginBlockStart: '1rem', textDecoration: 'none' }} to="/entries/new">
                    Obrir editor
                  </Link>
                </div>
              </div>
            </section>

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Evolució emocional</p>
              </div>

              <div className="stat-list">
                <div className="stat-card">
                  <span>Entrades analitzades</span>
                  <strong>0</strong>
                </div>
                <div className="stat-card">
                  <span>Tendència emocional</span>
                  <strong>Sense dades</strong>
                </div>
                <div className="stat-card">
                  <span>Contactes actius</span>
                  <strong>{patientContactsCount}</strong>
                </div>
              </div>

              <div className="content-card section-stack">
                <h3>Encara no hi ha prou informació</h3>
                <p className="muted">
                  Quan tinguis prou entrades escrites i analitzades, aquí es mostraran algunes mètriques d’evolució emocional per ajudar-te a veure el teu progrés.
                </p>
              </div>
            </section>

            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Entrades recents</p>
                <h2>El teu historial més recent</h2>
              </div>

              <div className="content-card section-stack">
                <h3>Encara no hi ha entrades disponibles</h3>
                <p className="muted">
                  Quan escriguis les primeres entrades, aquí apareixeran ordenades de la més recent a la més antiga amb el resultat de l’anàlisi emocional.
                </p>
                <p className="muted">
                  Et recomanem començar amb una primera entrada per tal que el sistema pugui començar a construir el teu context emocional.
                </p>
                <div className="button-row" style={{ marginBlockStart: '1rem' }}>
                  <Link className="button" style={{ textDecoration: 'none' }} to="/entries/new">
                    Escriure
                  </Link>
                  <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/profile">
                    Gestionar perfil i contactes
                  </Link>
                  <a
                    className="button-ghost"
                    style={{ textDecoration: 'none' }}
                    href={consentDocumentUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Veure consentiment PDF
                  </a>
                </div>
              </div>
            </section>
          </>
        ) : null}

        {user.role === 'therapist' ? (
          <>
            <section className="screen-card dashboard-panel profile-card--wide">
              <div className="panel-heading">
                <p className="eyebrow">Visió clínica</p>
                <h2>Panell d’activitat del terapeuta</h2>
                <p className="muted">
                  Aquí tens una lectura ràpida de l’estat actual dels teus pacients assignats i dels espais que requeriran revisió a mesura que avancem amb entrades, anàlisi i alertes.
                </p>
              </div>

              <div className="dashboard-metrics-grid">
                <div className="dashboard-metric-card dashboard-metric-card--alert">
                  <span>Alertes pendents</span>
                  <strong>0</strong>
                  <p>Quan activem el mòdul d’alertes, aquí veuràs els casos que necessiten resposta.</p>
                </div>

                <div className="dashboard-metric-card dashboard-metric-card--active">
                  <span>Pacients actius</span>
                  <strong>{therapistPatients.filter((patient) => patient.is_active).length}</strong>
                  <p>Total de pacients assignats amb accés actiu a la plataforma.</p>
                </div>

                <div className="dashboard-metric-card">
                  <span>Entrades del dia</span>
                  <strong>0</strong>
                  <p>Aquest comptador s’omplirà quan connectem el mòdul d’entrades de journaling.</p>
                </div>

                <div className="dashboard-metric-card dashboard-metric-card--pending">
                  <span>Anàlisis pendents</span>
                  <strong>{therapistPatients.filter((patient) => patient.is_active && !patient.consent_accepted).length}</strong>
                  <p>De moment mostrem els pacients actius que encara no han completat el consentiment.</p>
                </div>
              </div>

              <div className="button-row">
                <Link className="button" style={{ textDecoration: 'none' }} to="/patients">
                  Veure pacients
                </Link>
              </div>
            </section>
          </>
        ) : null}


      </div>
    </div>
  )
}
