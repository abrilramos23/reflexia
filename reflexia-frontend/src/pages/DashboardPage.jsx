import { Link, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { AppHeader } from '../components/AppHeader.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function formatRole(role) {
  if (role === 'therapist') {
    return 'Terapeuta'
  }

  if (role === 'patient') {
    return 'Pacient'
  }

  if (role === 'admin') {
    return 'Administrador'
  }

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
  const { user, registerPatient, registerTherapist } = useAuth()
  const [therapistForm, setTherapistForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    license_number: '',
    specialty: '',
  })
  const [patientForm, setPatientForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    birth_date: '',
  })
  const [therapistMessage, setTherapistMessage] = useState('')
  const [therapistError, setTherapistError] = useState('')
  const [patientMessage, setPatientMessage] = useState('')
  const [patientError, setPatientError] = useState('')
  const [isSubmittingTherapist, setIsSubmittingTherapist] = useState(false)
  const [isSubmittingPatient, setIsSubmittingPatient] = useState(false)

  if (!user) {
    return <Navigate to="/login" replace />
  }

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

  async function handlePatientSubmit(event) {
    event.preventDefault()
    setPatientError('')
    setPatientMessage('')
    setIsSubmittingPatient(true)

    try {
      const response = await registerPatient(patientForm)
      setPatientMessage(
        response.activation_email_sent
          ? `Pacient creat i correu d'activació enviat a ${response.email}.`
          : 'Pacient creat correctament.',
      )
      setPatientForm({
        first_name: '',
        last_name: '',
        email: '',
        birth_date: '',
      })
    } catch (error) {
      setPatientError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsSubmittingPatient(false)
    }
  }

  return (
    <div className="screen-shell">
      <AppHeader />

      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Tauler inicial</p>
            <h1 className="section-title">Compte actiu i llest per continuar.</h1>
            <p className="muted">
              Aquesta és una primera base funcional del frontend del mòdul users. Des d’aquí ja podem provar els
              fluxos d’autenticació i gestió de perfil.
            </p>
          </div>

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
              <strong>{user.role === 'patient' ? (user.consent_accepted ? 'Acceptat' : 'Pendent') : 'No aplica'}</strong>
            </div>
          </div>
        </section>

        {user.role === 'admin' ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Gestió de terapeutes</p>
              <h2>Crear terapeuta i enviar activació</h2>
              <p className="muted">
                L’admin crea el compte amb les dades bàsiques i el sistema envia un correu perquè el terapeuta
                defineixi la seva contrasenya i activi l’accés.
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

        {user.role === 'therapist' ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Gestió de pacients</p>
              <h2>Registrar un nou pacient</h2>
              <p className="muted">
                En crear el compte, el backend envia el
                correu d’activació perquè el pacient estableixi la seva contrasenya i, al primer accés, accepti el
                consentiment informat.
              </p>
            </div>

            {patientMessage ? <div className="message">{patientMessage}</div> : null}
            {patientError ? <div className="error-banner">{patientError}</div> : null}

            <form className="form-stack" onSubmit={handlePatientSubmit}>
              <div className="inline-fields">
                <div className="field-group">
                  <label htmlFor="patient-first-name">Nom</label>
                  <input
                    id="patient-first-name"
                    value={patientForm.first_name}
                    onChange={(event) =>
                      setPatientForm((currentState) => ({
                        ...currentState,
                        first_name: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="patient-last-name">Cognoms</label>
                  <input
                    id="patient-last-name"
                    value={patientForm.last_name}
                    onChange={(event) =>
                      setPatientForm((currentState) => ({
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
                  <label htmlFor="patient-email">Correu electrònic</label>
                  <input
                    id="patient-email"
                    type="email"
                    value={patientForm.email}
                    onChange={(event) =>
                      setPatientForm((currentState) => ({
                        ...currentState,
                        email: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="patient-birth-date">Data de naixement</label>
                  <input
                    id="patient-birth-date"
                    type="date"
                    value={patientForm.birth_date}
                    onChange={(event) =>
                      setPatientForm((currentState) => ({
                        ...currentState,
                        birth_date: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
              </div>

              <div className="button-row">
                <button className="button-secondary" type="submit" disabled={isSubmittingPatient}>
                  {isSubmittingPatient ? 'Creant pacient...' : 'Crear pacient'}
                </button>
              </div>
            </form>
          </section>
        ) : null}

      </div>
    </div>
  )
}
