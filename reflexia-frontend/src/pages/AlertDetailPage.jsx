import { useEffect, useState } from 'react'
import { Link, useParams, Navigate } from 'react-router-dom'
import { FaArrowLeft } from 'react-icons/fa'
import { useAuth } from '../context/AuthContext.jsx'
import {
  formatAlertStatus,
  formatContactRelation,
  formatEmotion,
  formatNotificationStatus,
  formatRiskLevel,
  formatSelectedContactCount,
  translateKnownAlertMessage,
} from '../lib/alerts.js'
import { normalizeStoredContentToHtml } from '../lib/entries.js'

function firstErrorMessage(error) {
  if (!error) {
    return 'S\'ha produït un error inesperat.'
  }

  if (typeof error === 'string') {
    return translateKnownAlertMessage(error)
  }

  if (typeof error.detail === 'string') {
    return translateKnownAlertMessage(error.detail)
  }

  if (typeof error.message === 'string') {
    return translateKnownAlertMessage(error.message)
  }

  const firstEntry = Object.values(error)[0]

  if (Array.isArray(firstEntry)) {
    return translateKnownAlertMessage(String(firstEntry[0]))
  }

  if (typeof firstEntry === 'string') {
    return translateKnownAlertMessage(firstEntry)
  }

  return 'S\'ha produït un error inesperat.'
}

export function AlertDetailPage() {
  const { alertId } = useParams()
  const { user, api } = useAuth()
  const userRole = user?.role
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [validatingNote, setValidatingNote] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [selectedContacts, setSelectedContacts] = useState([])
  const [notifyingContacts, setNotifyingContacts] = useState(false)
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    let isCancelled = false

    async function loadAlert() {
      if (userRole !== 'therapist') {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError('')
        const response = await api.get(`/alerts/${alertId}/`)
        if (!isCancelled) {
          setAlert(response.data)
          const defaultContacts = (response.data.associated_contacts ?? []).map((contact) => contact.id)
          setSelectedContacts(defaultContacts)
        }

        const historyResponse = await api.get(`/alerts/${alertId}/history/`)
        if (!isCancelled) {
          setNotifications(historyResponse.data)
        }
      } catch (err) {
        if (!isCancelled) {
          setError(firstErrorMessage(err.response?.data || err))
        }
      } finally {
        if (!isCancelled) {
          setLoading(false)
        }
      }
    }

    loadAlert()

    return () => {
      isCancelled = true
    }
  }, [api, alertId, userRole])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'therapist') {
    return <Navigate to="/dashboard" replace />
  }

  async function handleValidate(action) {
    setError('')
    setSuccessMessage('')
    setIsValidating(true)

    try {
      const response = await api.patch(`/alerts/${alertId}/`, {
        action,
        validation_note: validatingNote,
      })

      setAlert(response.data)
      setSuccessMessage(
        action === 'VALIDATE'
          ? 'Alerta validada correctament.'
          : 'Alerta descartada correctament.',
      )
      setValidatingNote('')
    } catch (err) {
      setError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsValidating(false)
    }
  }

  async function handleNotifyContacts() {
    if (selectedContacts.length === 0) {
      setError('Selecciona almenys un contacte.')
      return
    }

    setError('')
    setSuccessMessage('')
    setNotifyingContacts(true)

    try {
      const response = await api.post(`/alerts/${alertId}/notify-contacts/`, {
        contact_ids: selectedContacts,
      })

      setSuccessMessage(
        `Notificacions enviades: ${response.data.notified_count}. Fallides: ${response.data.failed_count}.`,
      )

      const historyResponse = await api.get(`/alerts/${alertId}/history/`)
      setNotifications(historyResponse.data)
    } catch (err) {
      setError(firstErrorMessage(err.response?.data || err))
    } finally {
      setNotifyingContacts(false)
    }
  }

  if (loading) {
    return (
      <div className="screen-shell">
        <div className="profile-grid">
          <section className="screen-card dashboard-panel profile-card--wide">
            <p className="muted">Carregant alerta...</p>
          </section>
        </div>
      </div>
    )
  }

  if (!alert) {
    return (
      <div className="screen-shell">
        <div className="profile-grid">
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="error-banner">Alerta no trobada.</div>
            <Link to="/alerts" className="button-ghost" title="Tornar" aria-label="Tornar">
              <FaArrowLeft />
            </Link>
          </section>
        </div>
      </div>
    )
  }

  const canNotify = alert.status === 'validated'
  const associatedContacts = alert.associated_contacts ?? []

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <Link to="/alerts" className="button-ghost" title="Tornar" aria-label="Tornar">
            <FaArrowLeft />
          </Link>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          {error ? <div className="error-banner">{error}</div> : null}
          {successMessage ? <div className="message">{successMessage}</div> : null}

          <div className="panel-heading">
            <p className="eyebrow">Detall de l&apos;alerta</p>
            <h1 className="section-title">{alert.patient_name}</h1>
            <div className="entries-toolbar">
              <span className={`status-pill ${alertStatusClassName(alert.status)}`}>
                {formatAlertStatus(alert.status)}
              </span>
              <span className={`status-pill ${riskClassName(alert.risk_level)}`}>
                {formatRiskLevel(alert.risk_level)}
              </span>
              <span className="status-pill dashboard-status-pill--muted">
                {formatAlertDate(alert.entry_date)}
              </span>
            </div>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="content-card section-stack entries-summary-card">
            <h3>Informació del pacient</h3>
            <div className="inline-fields">
              <p className="muted">
                <strong>Nom:</strong> {alert.patient_name}
              </p>
              <p className="muted">
                <strong>Correu electrònic:</strong> {alert.patient_email}
              </p>
            </div>
          </div>

          <div className="content-card section-stack entries-summary-card">
            <div className="item-heading-row">
              <h3>Entrada</h3>
              <span className="status-pill dashboard-status-pill--muted">
                {formatAlertDate(alert.entry_date)}
              </span>
            </div>
            <div
              className="entries-rendered-content"
              dangerouslySetInnerHTML={{ __html: normalizeStoredContentToHtml(alert.entry_content) }}
            />
          </div>

          <div className="content-card section-stack entries-analysis-card">
            <div className="item-heading-row">
              <h3>Anàlisi emocional</h3>
              <span className={`status-pill ${riskClassName(alert.risk_level)}`}>
                {formatRiskLevel(alert.risk_level)}
              </span>
            </div>
            <p className="muted">
              <strong>Emoció principal:</strong> {formatEmotion(alert.analysis_primary_emotion)}
            </p>
            <p>{alert.analysis_summary}</p>
          </div>
        </section>

        {alert.status === 'pending' ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Validació</p>
            </div>
            <div className="form-stack">
              <div className="field-group">
                <label htmlFor="validation-note">Nota (opcional)</label>
                <textarea
                  id="validation-note"
                  value={validatingNote}
                  onChange={(e) => setValidatingNote(e.target.value)}
                  placeholder="Afegeix una nota sobre aquesta alerta..."
                />
              </div>

              <div className="button-row">
                <button
                  type="button"
                  className="button"
                  onClick={() => handleValidate('VALIDATE')}
                  disabled={isValidating}
                >
                  {isValidating ? 'Guardant...' : 'Validar alerta'}
                </button>
                <button
                  type="button"
                  className="button-danger"
                  onClick={() => handleValidate('DISMISS')}
                  disabled={isValidating}
                >
                  {isValidating ? 'Guardant...' : 'Descartar alerta'}
                </button>
              </div>
            </div>
          </section>
        ) : null}

        {canNotify ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Notificar contactes</p>
            </div>

            {associatedContacts.length > 0 ? (
              <>
                <ul className="patient-list">
                  {associatedContacts.map((contact) => (
                    <li key={contact.id} className="compact-list-item">
                      <label className="checkbox-row" htmlFor={`contact-${contact.id}`}>
                        <input
                          type="checkbox"
                          id={`contact-${contact.id}`}
                          checked={selectedContacts.includes(contact.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedContacts((currentContacts) => [
                                ...currentContacts,
                                contact.id,
                              ])
                            } else {
                              setSelectedContacts((currentContacts) =>
                                currentContacts.filter((id) => id !== contact.id),
                              )
                            }
                          }}
                        />
                        <span>
                          <strong>{contact.name}  </strong>
                          <span className="muted">
                            {contact.email || contact.phone}  ({formatContactRelation(contact.relation)})
                          </span>
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>

                <button
                  type="button"
                  className="button"
                  onClick={handleNotifyContacts}
                  disabled={notifyingContacts || selectedContacts.length === 0}
                >
                  {notifyingContacts
                    ? 'Enviant notificacions...'
                    : formatSelectedContactCount(selectedContacts.length)}
                </button>
              </>
            ) : (
              <p className="muted">No hi ha contactes associats.</p>
            )}
          </section>
        ) : null}

        {notifications.length > 0 ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Historial</p>
            </div>
            <ul className="patient-list">
              {notifications.map((notification) => (
                <li key={notification.id} className="compact-list-item">
                  <div className="item-heading-row">
                    <strong>{notification.contact_name}</strong>
                    <span className={`status-pill ${notificationStatusClassName(notification.status)}`}>
                      {formatNotificationStatus(notification.status)}
                    </span>
                  </div>
                  <p className="muted">
                    {notification.contact_email} · {formatAlertDateTime(notification.sent_at)}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </div>
  )
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

function riskClassName(riskLevel) {
  if (riskLevel === 'high') {
    return 'risk-pill--high'
  }

  if (riskLevel === 'moderate') {
    return 'risk-pill--moderate'
  }

  return 'risk-pill--low'
}

function notificationStatusClassName(status) {
  if (status === 'failed') {
    return 'risk-pill--high'
  }

  if (status === 'acknowledged' || status === 'sent') {
    return 'dashboard-status-pill--active'
  }

  return 'dashboard-status-pill--muted'
}

function formatAlertDate(date) {
  if (!date) {
    return 'No disponible'
  }

  return new Date(date).toLocaleDateString('ca-ES')
}

function formatAlertDateTime(date) {
  if (!date) {
    return 'No disponible'
  }

  return new Date(date).toLocaleString('ca-ES')
}
