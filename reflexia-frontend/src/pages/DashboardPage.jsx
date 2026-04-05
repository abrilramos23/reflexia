import { Link, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { AppHeader } from '../components/AppHeader.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { consentDocumentUrl } from '../lib/api.js'

function formatRole(role) {
  if (role === 'therapist') return 'Terapeuta'
  if (role === 'patient') return 'Pacient'
  if (role === 'admin') return 'Administrador'
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

export function DashboardPage() {
  const {
    user,
    registerTherapist,
    listTherapistPatients,
    listSupportTherapists,
    listAssociatedContacts,
  } = useAuth()
  const [therapistForm, setTherapistForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    license_number: '',
    specialty: '',
  })
  const [therapistMessage, setTherapistMessage] = useState('')
  const [therapistError, setTherapistError] = useState('')
  const [isSubmittingTherapist, setIsSubmittingTherapist] = useState(false)
  const [therapistPatientsCount, setTherapistPatientsCount] = useState(0)
  const [activeTherapistPatientsCount, setActiveTherapistPatientsCount] = useState(0)
  const [pendingConsentPatientsCount, setPendingConsentPatientsCount] = useState(0)
  const [supportTherapistsCount, setSupportTherapistsCount] = useState(0)
  const [patientContactsCount, setPatientContactsCount] = useState(0)
  const [defaultContactsCount, setDefaultContactsCount] = useState(0)
  const [dashboardError, setDashboardError] = useState('')

  if (!user) {
    return <Navigate to="/login" replace />
  }

  useEffect(() => {
    let isCancelled = false

    async function loadDashboardData() {
      setDashboardError('')

      try {
        if (user.role === 'therapist') {
          const [patients, supportTherapists] = await Promise.all([
            listTherapistPatients(),
            listSupportTherapists(),
          ])

          if (!isCancelled) {
            setTherapistPatientsCount(patients.length)
            setActiveTherapistPatientsCount(
              patients.filter((patient) => patient.is_active).length,
            )
            setPendingConsentPatientsCount(
              patients.filter(
                (patient) => patient.is_active && patient.consent_accepted === false,
              ).length,
            )
            setSupportTherapistsCount(supportTherapists.length)
          }
        }

        if (user.role === 'patient') {
          const contacts = await listAssociatedContacts()

          if (!isCancelled) {
            setPatientContactsCount(contacts.length)
            setDefaultContactsCount(
              contacts.filter((contact) => contact.is_default).length,
            )
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

  async function handleTherapistSubmit(event) {
    event.preventDefault()
    setTherapistError('')
    setTherapistMessage('')
    setIsSubmittingTherapist(true)

    try {
      const response = await registerTherapist(therapistForm)
      setTherapistMessage(
        response.activation_email_sent
          ? `Compte creat i correu d'activació enviat a ${response.email}.`
          : 'Terapeuta creat correctament.',
      )
      setTherapistForm({
        first_name: '',
        last_name: '',
        email: '',
        license_number: '',
        specialty: '',
      })
    } catch (error) {
      setTherapistError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsSubmittingTherapist(false)
    }
  }

  return (
    <div className="screen-shell">
      <AppHeader />

      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Tauler inicial</p>
            <h1 className="section-title">
              {user.role === 'therapist'
                ? 'Visió general de la teva activitat clínica.'
                : user.role === 'patient'
                  ? 'Benvingut al teu espai personal de Reflexia.'
                  : 'Compte actiu i llest per continuar.'}
            </h1>
            <p className="muted">
              {user.role === 'therapist'
                ? 'Consulta l’estat dels teus pacients, revisa la cobertura de suport i accedeix ràpidament a la gestió clínica.'
                : user.role === 'patient'
                  ? 'Des d’aquí pots revisar l’estat del teu compte, mantenir actualitzats els teus contactes i reforçar la seguretat.'
                  : 'Administra les altes de terapeutes i mantén l’accés a la plataforma sota control.'}
            </p>
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
            <section className="screen-card dashboard-panel">
              <div className="panel-heading">
                <p className="eyebrow">Resum personal</p>
                <h2>Contactes i seguretat</h2>
              </div>

              <div className="stat-list">
                <div className="stat-card">
                  <span>Contactes associats</span>
                  <strong>{patientContactsCount}</strong>
                </div>
                <div className="stat-card">
                  <span>Per defecte</span>
                  <strong>{defaultContactsCount}</strong>
                </div>
                <div className="stat-card">
                  <span>Protecció</span>
                  <strong>{user.two_factor_enabled ? '2FA actiu' : '2FA pendent'}</strong>
                </div>
              </div>
            </section>

            <section className="screen-card dashboard-panel">
              <div className="panel-heading">
                <p className="eyebrow">Accions principals</p>
                <h2>Què pots fer ara</h2>
              </div>

              <div className="button-row">
                <Link className="button-secondary" style={{ textDecoration: 'none' }} to="/profile">
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

              <div className="content-card section-stack">
                <h3>Estat actual</h3>
                <p className="muted">
                  {user.consent_accepted
                    ? 'El teu compte està preparat per continuar amb normalitat.'
                    : 'Tens accions pendents al teu compte. Revisa el consentiment i la configuració de seguretat.'}
                </p>
              </div>
            </section>
          </>
        ) : null}

        {user.role === 'therapist' ? (
          <>
            <section className="screen-card dashboard-panel">
              <div className="panel-heading">
                <p className="eyebrow">Resum assistencial</p>
                <h2>Pacients i consentiments</h2>
              </div>

              <div className="stat-list">
                <div className="stat-card">
                  <span>Pacients assignats</span>
                  <strong>{therapistPatientsCount}</strong>
                </div>
                <div className="stat-card">
                  <span>Pacients actius</span>
                  <strong>{activeTherapistPatientsCount}</strong>
                </div>
                <div className="stat-card">
                  <span>Consentiments pendents</span>
                  <strong>{pendingConsentPatientsCount}</strong>
                </div>
              </div>
            </section>

            <section className="screen-card dashboard-panel">
              <div className="panel-heading">
                <p className="eyebrow">Cobertura clínica</p>
                <h2>Suport i accions ràpides</h2>
              </div>

              <div className="stat-list">
                <div className="stat-card">
                  <span>Terapeutes de suport</span>
                  <strong>{supportTherapistsCount}</strong>
                </div>
                <div className="stat-card">
                  <span>Espai principal</span>
                  <strong>Gestió clínica</strong>
                </div>
                <div className="stat-card">
                  <span>Acció clau</span>
                  <strong>Alta i seguiment</strong>
                </div>
              </div>

              <div className="button-row">
                <Link className="button-secondary" style={{ textDecoration: 'none' }} to="/patients">
                  Obrir gestió de pacients
                </Link>
                <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/profile">
                  Gestionar suport i perfil
                </Link>
              </div>
            </section>
          </>
        ) : null}

        {user.role === 'admin' ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Gestió de terapeutes</p>
              <h2>Crear terapeuta i enviar activació</h2>
              <p className="muted">
                L’admin crea el compte amb les dades bàsiques i el sistema envia un correu perquè el terapeuta defineixi la seva contrasenya i activi l’accés.
              </p>
            </div>

            {therapistMessage ? <div className="message">{therapistMessage}</div> : null}
            {therapistError ? <div className="error-banner">{therapistError}</div> : null}

            <form className="form-stack" onSubmit={handleTherapistSubmit}>
              <div className="inline-fields">
                <div className="field-group">
                  <label htmlFor="therapist-first-name">Nom</label>
                  <input
                    id="therapist-first-name"
                    value={therapistForm.first_name}
                    onChange={(event) =>
                      setTherapistForm((currentState) => ({
                        ...currentState,
                        first_name: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="therapist-last-name">Cognoms</label>
                  <input
                    id="therapist-last-name"
                    value={therapistForm.last_name}
                    onChange={(event) =>
                      setTherapistForm((currentState) => ({
                        ...currentState,
                        last_name: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
              </div>

              <div className="inline-fields">
                <div className="field-group">
                  <label htmlFor="therapist-email">Correu electrònic</label>
                  <input
                    id="therapist-email"
                    type="email"
                    value={therapistForm.email}
                    onChange={(event) =>
                      setTherapistForm((currentState) => ({
                        ...currentState,
                        email: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="therapist-license">Número de col·legiació</label>
                  <input
                    id="therapist-license"
                    value={therapistForm.license_number}
                    onChange={(event) =>
                      setTherapistForm((currentState) => ({
                        ...currentState,
                        license_number: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
              </div>

              <div className="field-group">
                <label htmlFor="therapist-specialty">Especialitat</label>
                <input
                  id="therapist-specialty"
                  value={therapistForm.specialty}
                  onChange={(event) =>
                    setTherapistForm((currentState) => ({
                      ...currentState,
                      specialty: event.target.value,
                    }))
                  }
                  required
                />
              </div>

              <div className="button-row">
                <button className="button" type="submit" disabled={isSubmittingTherapist}>
                  {isSubmittingTherapist ? 'Creant terapeuta...' : 'Crear terapeuta'}
                </button>
              </div>
            </form>
          </section>
        ) : null}
      </div>
    </div>
  )
}
