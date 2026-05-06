import { useEffect, useState } from 'react'
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

export function SupportTherapistsPage() {
  const {
    user,
    listSupportTherapists,
    listAvailableSupportTherapists,
    createSupportTherapist,
    deleteSupportTherapist,
  } = useAuth()

  const [supportTherapists, setSupportTherapists] = useState([])
  const [availableSupportTherapists, setAvailableSupportTherapists] = useState([])
  const [selectedSupportId, setSelectedSupportId] = useState('')
  const [showSupportForm, setShowSupportForm] = useState(false)
  const [supportMessage, setSupportMessage] = useState('')
  const [supportError, setSupportError] = useState('')

  const canHaveSupport = user?.role === 'therapist' && user?.memberships?.some(m => m.organisation.type === 'clinic')

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
        const [currentSupportTherapists, availableTherapists] = await Promise.all([
          listSupportTherapists(),
          listAvailableSupportTherapists(),
        ])

        if (!isCancelled) {
          setSupportTherapists(currentSupportTherapists)
          setAvailableSupportTherapists(availableTherapists)
        }
      } catch {
        if (!isCancelled) {
          setSupportError('No s’han pogut carregar els terapeutes de suport.')
        }
      }
    }

    loadSupportData()

    return () => {
      isCancelled = true
    }
  }, [listSupportTherapists, listAvailableSupportTherapists])

  async function handleSupportTherapistSubmit(event) {
    event.preventDefault()
    setSupportError('')
    setSupportMessage('')

    try {
      const createdSupportTherapist = await createSupportTherapist({
        support_id: selectedSupportId,
      })

      setSupportTherapists((currentTherapists) => [...currentTherapists, createdSupportTherapist])
      setAvailableSupportTherapists((currentTherapists) =>
        currentTherapists.filter((therapist) => therapist.id !== selectedSupportId),
      )
      setSelectedSupportId('')
      setShowSupportForm(false)
      setSupportMessage('Terapeuta de suport afegit correctament.')
    } catch (error) {
      setSupportError(firstErrorMessage(error.response?.data || error))
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

    try {
      await deleteSupportTherapist(supportTherapist.support_id)
      setSupportTherapists((currentTherapists) =>
        currentTherapists.filter(
          (currentTherapist) => currentTherapist.support_id !== supportTherapist.support_id,
        ),
      )
      setAvailableSupportTherapists((currentTherapists) =>
        [...currentTherapists, {
          id: supportTherapist.support_id,
          first_name: supportTherapist.first_name,
          last_name: supportTherapist.last_name,
          email: supportTherapist.email,
          license_number: supportTherapist.license_number,
          specialty: supportTherapist.specialty,
        }].sort((left, right) =>
          `${left.first_name} ${left.last_name}`.localeCompare(`${right.first_name} ${right.last_name}`),
        ),
      )
      setSupportMessage('Terapeuta de suport eliminat correctament.')
    } catch (error) {
      setSupportError(firstErrorMessage(error.response?.data || error))
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card profile-card profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Terapeutes de suport</p>
            {supportMessage ? <div className="message" style={{ marginBottom: '1rem' }}>{supportMessage}</div> : null}
            {supportError ? <div className="error-banner" style={{ marginBottom: '1rem' }}>{supportError}</div> : null}
            <h3>Gestionar terapeutes de suport</h3>
          </div>

          {!canHaveSupport ? (
            <div className="content-card section-stack" style={{ borderLeft: '4px solid var(--accent-color)', backgroundColor: 'var(--bg-card-alt)' }}>
              <p className="muted">
                <strong>Aquest servei només està disponible per a professionals que pertanyen a una clínica.</strong>
              </p>
              <p className="muted" style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                Com a professional independent, actualment no disposes d&apos;un equip clínic assignat per gestionar la cobertura de suport d&apos;alertes.
              </p>
            </div>
          ) : null}

          {canHaveSupport && !showSupportForm ? (
            <div className="section-toolbar">
              <button
                className="button"
                type="button"
                onClick={() => {
                  setShowSupportForm(true)
                }}
              >
                Afegir terapeuta de suport
              </button>
            </div>
          ) : null}

          {showSupportForm ? (
            <form className="form-stack collapsible-form-card" onSubmit={handleSupportTherapistSubmit}>
              <div className="field-group">
                <label htmlFor="support-therapist">Selecciona un terapeuta</label>
                <select
                  id="support-therapist"
                  value={selectedSupportId}
                  onChange={(event) => setSelectedSupportId(event.target.value)}
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
                <button className="button" type="submit" disabled={!selectedSupportId}>
                  Afegir terapeuta
                </button>
                <button
                  className="button-ghost"
                  type="button"
                  onClick={() => {
                    setShowSupportForm(false)
                    setSelectedSupportId('')
                  }}
                >
                  Cancel·lar
                </button>
              </div>
            </form>
          ) : null}

          <div className="content-card section-stack">
            <h3>Llista actual</h3>

            {supportTherapists.length === 0 ? (
              <p className="muted">Encara no tens terapeutes de suport assignats.</p>
            ) : (
              <ul className="patient-list">
                {supportTherapists.map((supportTherapist) => (
                  <li className="patient-item compact-list-item" key={supportTherapist.support_id}>
                    <div>
                      <div className="item-heading-row">
                        <strong>
                          {supportTherapist.first_name} {supportTherapist.last_name}
                        </strong>
                        <span className="status-pill">Suport actiu</span>
                      </div>
                      <p className="muted">{supportTherapist.specialty}</p>
                      <p className="muted">{supportTherapist.email}</p>
                    </div>

                    <div className="list-actions">
                      <button
                        className="action-chip action-chip--danger"
                        type="button"
                        onClick={() => handleDeleteSupportTherapist(supportTherapist)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
