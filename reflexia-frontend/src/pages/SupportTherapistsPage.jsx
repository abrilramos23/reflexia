import { useEffect, useState } from 'react'
import { FaTrash } from 'react-icons/fa'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function firstErrorMessage(error) {
  if (!error) return 'S’ha produït un error inesperat.'
  if (typeof error === 'string') return error
  const firstEntry = Object.values(error)[0]
  if (Array.isArray(firstEntry)) return String(firstEntry[0])
  if (typeof firstEntry === 'string') return firstEntry
  return 'S’ha produït un error inesperat.'
}

function sortTherapists(therapists) {
  return [...therapists].sort((left, right) =>
    `${left.first_name} ${left.last_name}`.localeCompare(`${right.first_name} ${right.last_name}`),
  )
}

export function SupportTherapistsPage() {
  const {
    user,
    listSupportTherapists,
    listAvailableSupportTherapists,
    listIncomingSupportTherapistRequests,
    createSupportTherapist,
    respondSupportTherapistRequest,
    deleteSupportTherapist,
  } = useAuth()

  const [supportTherapists, setSupportTherapists] = useState([])
  const [availableSupportTherapists, setAvailableSupportTherapists] = useState([])
  const [incomingRequests, setIncomingRequests] = useState([])
  const [selectedSupportId, setSelectedSupportId] = useState('')
  const [isAddSectionOpen, setIsAddSectionOpen] = useState(false)
  const [supportMessage, setSupportMessage] = useState('')
  const [supportError, setSupportError] = useState('')
  const [isSubmittingSupport, setIsSubmittingSupport] = useState(false)
  const [busySupportId, setBusySupportId] = useState('')
  const [busyRequestId, setBusyRequestId] = useState('')

  const canHaveSupport =
    user?.role === 'therapist' && user?.memberships?.some((m) => m.organisation.type === 'clinic')

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'therapist') {
    return <Navigate to="/dashboard" replace />
  }

  useEffect(() => {
    let isCancelled = false

    async function loadSupportData() {
      try {
        const [currentSupportTherapists, availableTherapists, requests] = await Promise.all([
          listSupportTherapists(),
          listAvailableSupportTherapists(),
          listIncomingSupportTherapistRequests(),
        ])

        if (!isCancelled) {
          setSupportTherapists(sortTherapists(currentSupportTherapists))
          setAvailableSupportTherapists(sortTherapists(availableTherapists))
          setIncomingRequests(sortTherapists(requests))
        }
      } catch (error) {
        if (!isCancelled) {
          setSupportError('No s’han pogut carregar els terapeutes de suport.')
        }
      }
    }

    loadSupportData()

    return () => {
      isCancelled = true
    }
  }, [listSupportTherapists, listAvailableSupportTherapists, listIncomingSupportTherapistRequests])

  async function handleSupportTherapistSubmit(event) {
    event.preventDefault()
    setSupportError('')
    setSupportMessage('')
    setIsSubmittingSupport(true)

    try {
      const createdSupportTherapist = await createSupportTherapist({
        support_id: selectedSupportId,
      })

      setSupportTherapists((currentTherapists) =>
        sortTherapists([...currentTherapists, createdSupportTherapist]),
      )
      setAvailableSupportTherapists((currentTherapists) =>
        currentTherapists.filter((therapist) => therapist.id !== selectedSupportId),
      )
      setSelectedSupportId('')
      setSupportMessage('Sol·licitud enviada. El terapeuta haurà d’acceptar-la abans de quedar assignat.')
    } catch (error) {
      setSupportError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsSubmittingSupport(false)
    }
  }

  async function handleRespondRequest(request, action) {
    setSupportError('')
    setSupportMessage('')
    setBusyRequestId(request.id)

    try {
      await respondSupportTherapistRequest(request.id, action)
      setIncomingRequests((currentRequests) =>
        currentRequests.filter((currentRequest) => currentRequest.id !== request.id),
      )
      setSupportMessage(
        action === 'accept'
          ? 'Has acceptat ser terapeuta de suport.'
          : 'Has rebutjat la sol·licitud de suport.',
      )
    } catch (error) {
      setSupportError(firstErrorMessage(error.response?.data || error))
    } finally {
      setBusyRequestId('')
    }
  }

  async function handleDeleteSupportTherapist(supportTherapist) {
    const confirmed = window.confirm(
      `Vols eliminar ${supportTherapist.first_name} ${supportTherapist.last_name} com a terapeuta de suport?`,
    )

    if (!confirmed) {
      return
    }

    setSupportError('')
    setSupportMessage('')
    setBusySupportId(supportTherapist.support_id)

    try {
      await deleteSupportTherapist(supportTherapist.support_id)
      setSupportTherapists((currentTherapists) =>
        currentTherapists.filter(
          (currentTherapist) => currentTherapist.support_id !== supportTherapist.support_id,
        ),
      )
      setAvailableSupportTherapists((currentTherapists) =>
        sortTherapists([
          ...currentTherapists,
          {
            id: supportTherapist.support_id,
            first_name: supportTherapist.first_name,
            last_name: supportTherapist.last_name,
            email: supportTherapist.email,
            license_number: supportTherapist.license_number,
            specialty: supportTherapist.specialty,
          },
        ]),
      )
      setSupportMessage('Terapeuta de suport eliminat correctament.')
    } catch (error) {
      setSupportError(firstErrorMessage(error.response?.data || error))
    } finally {
      setBusySupportId('')
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Terapeutes de suport</p>
            <h1 className="section-title">El teu equip de suport</h1>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <button
            className="section-toggle"
            type="button"
            onClick={() => setIsAddSectionOpen((currentState) => !currentState)}
          >
            <div className="panel-heading">
              <p className="eyebrow">Nou suport</p>
              <h2>Afegir terapeuta de suport</h2>
            </div>
            <span
              className={`section-toggle-indicator ${isAddSectionOpen ? 'section-toggle-indicator--open' : ''}`}
            >
              <span aria-hidden="true">▾</span>
            </span>
          </button>

          {isAddSectionOpen ? (
            <div className="collapsible-section-body">
              {!canHaveSupport ? (
                <div
                  className="content-card section-stack"
                  style={{ borderLeft: '4px solid var(--accent-color)', backgroundColor: 'var(--bg-card-alt)' }}
                >
                  <p className="muted">
                    <strong>Disponible només per a professionals vinculats a una clínica.</strong>
                  </p>
                </div>
              ) : (
                <>
                  {supportMessage ? <div className="message">{supportMessage}</div> : null}
                  {supportError ? <div className="error-banner">{supportError}</div> : null}

                  <form className="form-stack" onSubmit={handleSupportTherapistSubmit}>
                    <div className="field-group">
                      <label htmlFor="support-therapist">Selecciona un terapeuta</label>
                      <select
                        id="support-therapist"
                        value={selectedSupportId}
                        onChange={(event) => setSelectedSupportId(event.target.value)}
                        required
                      >
                        <option value="">Selecciona un terapeuta del sistema</option>
                        {availableSupportTherapists.map((therapist) => (
                          <option key={therapist.id} value={therapist.id}>
                            {therapist.first_name} {therapist.last_name} · {therapist.specialty}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="button-row">
                      <button
                        className="button-secondary"
                        type="submit"
                        disabled={!selectedSupportId || isSubmittingSupport}
                      >
                        {isSubmittingSupport ? 'Afegint...' : 'Afegir terapeuta'}
                      </button>
                    </div>
                  </form>
                </>
              )}
            </div>
          ) : null}
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow" style={{ marginBottom: '0rem' }}>
              Llista de terapeutes de suport
            </p>
          </div>

          {supportTherapists.length === 0 ? (
            <p className="muted">Encara no tens terapeutes de suport assignats.</p>
          ) : (
            <ul className="patient-list">
              {supportTherapists.map((supportTherapist) => (
                <li
                  className="compact-list-item"
                  key={supportTherapist.support_id}
                >
                  <div
                    style={{
                      display: 'flex',
                      padding: '14px 16px',
                      width: '100%',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div className="item-heading-row">
                        <strong>
                          {supportTherapist.first_name} {supportTherapist.last_name}
                        </strong>
                        <span className={`status-pill ${supportTherapist.status === 'accepted' ? 'dashboard-status-pill--active' : 'dashboard-status-pill--pending'}`}>
                          {supportTherapist.status === 'accepted' ? 'Suport actiu' : 'Pendent d’acceptació'}
                        </span>
                      </div>
                      <p className="muted" style={{ fontWeight: 'bold', margin: '0.5rem 0' }}>
                        {supportTherapist.email}
                      </p>
                      <p className="muted" style={{ margin: 0 }}>
                        Especialitat: {supportTherapist.specialty}
                      </p>
                    </div>

                     <div className="list-actions" style={{ marginLeft: '1rem' }}>
                      <button
                        className="action-chip action-chip--danger"
                        type="button"
                        disabled={busySupportId === supportTherapist.support_id}
                        onClick={() => handleDeleteSupportTherapist(supportTherapist)}
                        title="Eliminar"
                        aria-label="Eliminar"
                      >
                        {busySupportId === supportTherapist.support_id ? '...' : <FaTrash />}
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow" style={{ marginBottom: '0rem' }}>
              Sol·licituds rebudes
            </p>
          </div>

          {incomingRequests.length === 0 ? (
            <p className="muted">No tens sol·licituds pendents per ser terapeuta de suport.</p>
          ) : (
            <ul className="patient-list">
              {incomingRequests.map((request) => (
                <li className="compact-list-item" key={request.id}>
                  <div
                    style={{
                      display: 'flex',
                      padding: '14px 16px',
                      width: '100%',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div className="item-heading-row">
                        <strong>
                          {request.first_name} {request.last_name}
                        </strong>
                        <span className="status-pill dashboard-status-pill--pending">Pendent</span>
                      </div>
                      <p className="muted" style={{ fontWeight: 'bold', margin: '0.5rem 0' }}>
                        {request.email}
                      </p>
                      <p className="muted" style={{ margin: 0 }}>
                        Si acceptes, quedaràs associat com a suport en casos de risc extrem i l’accés quedarà auditat.
                      </p>
                    </div>

                    <div className="list-actions" style={{ marginLeft: '1rem' }}>
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={busyRequestId === request.id}
                        onClick={() => handleRespondRequest(request, 'accept')}
                      >
                        Acceptar
                      </button>
                      <button
                        className="button-ghost"
                        type="button"
                        disabled={busyRequestId === request.id}
                        onClick={() => handleRespondRequest(request, 'reject')}
                      >
                        Rebutjar
                      </button>
                    </div>
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
