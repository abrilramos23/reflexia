import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader.jsx'
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
                first_name: 'Deleted',
                last_name: 'Patient',
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
      <AppHeader />

      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Gestió de pacients</p>
            <h1 className="section-title">Pacients assignats al teu compte.</h1>
            <p className="muted">
              Des d’aquí pots donar d’alta nous pacients, consultar l’estat del seu accés i gestionar baixes quan sigui necessari.
            </p>
          </div>

          <div className="button-row">
            <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/dashboard">
              Tornar al tauler
            </Link>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Alta de pacient</p>
            <h2>Registrar un nou pacient</h2>
            <p className="muted">
              En crear el compte, s’envia un correu d’activació perquè el pacient estableixi la seva contrasenya i, al primer accés, accepti el consentiment informat.
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

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Llista actual</p>
            <h2>Llista de pacients</h2>
            <p className="muted">
              Pots veure si el compte està actiu i si el consentiment informat ja s’ha acceptat.
            </p>
          </div>

          {patientsError ? <div className="error-banner">{patientsError}</div> : null}

          {therapistPatients.length === 0 ? (
            <p className="muted">Encara no tens pacients assignats.</p>
          ) : (
            <ul className="patient-list">
              {therapistPatients.map((patient) => (
                <li className="patient-item compact-list-item" key={patient.id}>
                  <div>
                    <div className="item-heading-row">
                      <strong>{patient.first_name} {patient.last_name}</strong>
                      <span className="status-pill">
                        {patient.is_active ? 'Compte actiu' : 'Compte inactiu'}
                      </span>
                    </div>
                    <p className="muted" style={{ fontWeight: 'bold' }}>{patient.email}</p>
                    <p className="muted">
                      Naixement: {patient.birth_date}
                      <br />
                      Consentiment: {patient.consent_accepted ? 'Acceptat' : 'Pendent'}
                    </p>
                  </div>

                  <div className="list-actions">
                    <button
                      className="action-chip action-chip--danger"
                      type="button"
                      disabled={!patient.is_active || busyPatientId === patient.id}
                      onClick={() => handleDeactivatePatient(patient)}
                    >
                      {busyPatientId === patient.id ? 'Donant de baixa...' : 'Donar de baixa'}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
