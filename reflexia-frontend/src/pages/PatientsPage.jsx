import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { FaPlus, FaUserSlash } from 'react-icons/fa'
import { useAuth } from '../context/AuthContext.jsx'

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

function sortPatients(patients) {
  return [...patients].sort((left, right) =>
    `${left.first_name} ${left.last_name}`.localeCompare(`${right.first_name} ${right.last_name}`),
  )
}

export function PatientsPage() {
  const { user, registerPatient, listTherapistPatients, deactivatePatient } = useAuth()
  const [patientForm, setPatientForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    birth_date: '',
  })
  const [therapistPatients, setTherapistPatients] = useState([])
  const [patientMessage, setPatientMessage] = useState('')
  const [patientError, setPatientError] = useState('')
  const [patientsError, setPatientsError] = useState('')
  const [isSubmittingPatient, setIsSubmittingPatient] = useState(false)
  const [busyPatientId, setBusyPatientId] = useState('')
  const [isRegisterSectionOpen, setIsRegisterSectionOpen] = useState(false)

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'therapist') {
    return <Navigate to="/dashboard" replace />
  }

  useEffect(() => {
    let isCancelled = false

    async function loadPatients() {
      try {
        const patients = await listTherapistPatients()
        if (!isCancelled) {
          setTherapistPatients(sortPatients(patients))
        }
      } catch (error) {
        if (!isCancelled) {
          setPatientsError(firstErrorMessage(error.response?.data || error))
        }
      }
    }

    loadPatients()

    return () => {
      isCancelled = true
    }
  }, [listTherapistPatients])

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
      setTherapistPatients((currentPatients) => sortPatients([...currentPatients, response]))
    } catch (error) {
      setPatientError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsSubmittingPatient(false)
    }
  }

  async function handleDeactivatePatient(patient) {
    const confirmed = window.confirm(
      `Vols donar de baixa ${patient.first_name} ${patient.last_name}? Aquesta acció desactivarà el compte del pacient.`,
    )

    if (!confirmed) {
      return
    }

    setPatientsError('')
    setPatientMessage('')
    setBusyPatientId(patient.id)

    try {
      await deactivatePatient(patient.id)
      setTherapistPatients((currentPatients) =>
        currentPatients.map((currentPatient) =>
          currentPatient.id === patient.id
            ? {
                ...currentPatient,
                is_active: false,
                email: `deleted-${patient.id}@deleted.reflexia.local`,
                first_name: 'Pacient',
                last_name: 'Eliminat',
              }
            : currentPatient,
        ),
      )
      setPatientMessage('Pacient donat de baixa correctament.')
    } catch (error) {
      setPatientsError(firstErrorMessage(error.response?.data || error))
    } finally {
      setBusyPatientId('')
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Gestió de pacients</p>
            <h1 className="section-title">Pacients assignats</h1>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <button
            className="section-toggle"
            type="button"
            onClick={() => setIsRegisterSectionOpen((currentState) => !currentState)}
          >
            <div className="panel-heading">
              <p className="eyebrow">Alta de pacient</p>
              <h2>Registrar un nou pacient</h2>
            </div>
            <span className={`section-toggle-indicator ${isRegisterSectionOpen ? 'section-toggle-indicator--open' : ''}`}>
              <FaPlus />
            </span>
          </button>

          {isRegisterSectionOpen ? (
            <div className="collapsible-section-body">
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
            </div>
          ) : null}
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow" style={{ marginBottom: '0rem' }}>Llista de pacients</p>
          </div>

          {patientsError ? <div className="error-banner">{patientsError}</div> : null}

          {therapistPatients.length === 0 ? (
            <p className="muted">Encara no tens pacients assignats.</p>
          ) : (
            <ul className="patient-list">
              {therapistPatients.map((patient) => (
                <li className="compact-list-item" key={patient.id}>
                  <Link
                    to={`/patients/${patient.id}`}
                    style={{ textDecoration: 'none', color: 'inherit', display: 'flex', padding: '14px 16px', width: '100%', alignItems: 'center', transition: 'background-color 0.2s' }}
                    className="patient-card-link"
                  >
                    <div style={{ flex: 1 }}>
                      <div className="item-heading-row">
                        <strong>{patient.first_name} {patient.last_name}</strong>
                        <span className="status-pill">
                          {patient.is_active ? 'Compte actiu' : 'Compte inactiu'}
                        </span>
                      </div>
                      <p className="muted" style={{ fontWeight: 'bold', margin: '0.5rem 0' }}>{patient.email}</p>
                      <p className="muted" style={{ margin: 0 }}>
                        Naixement: {patient.birth_date}
                        <br />
                        Consentiment: {patient.consent_accepted ? 'Acceptat' : 'Pendent'}
                      </p>
                    </div>

                    <div className="list-actions" style={{ marginLeft: '1rem' }}>
                       <button
                        className="action-chip action-chip--danger action-chip--icon"
                        type="button"
                        disabled={!patient.is_active || busyPatientId === patient.id}
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          handleDeactivatePatient(patient)
                        }}
                        title="Donar de baixa"
                        aria-label="Donar de baixa"
                      >
                        {busyPatientId === patient.id ? '...' : <FaUserSlash />}
                      </button>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
