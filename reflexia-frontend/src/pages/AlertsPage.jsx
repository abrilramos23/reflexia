import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { FaBell } from 'react-icons/fa'
import { useAuth } from '../context/AuthContext.jsx'
import {
  formatAlertStatus,
  formatRiskLevel,
  translateKnownAlertMessage,
} from '../lib/alerts.js'

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

export function AlertsPage() {
  const { user, api } = useAuth()
  const userRole = user?.role
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [riskFilter, setRiskFilter] = useState('')

  useEffect(() => {
    let isCancelled = false

    async function loadAlerts() {
      if (userRole !== 'therapist') {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError('')
        const response = await api.get('/alerts/', {
          params: {
            status: statusFilter || undefined,
            risk_level: riskFilter || undefined,
          },
        })
        if (!isCancelled) {
          setAlerts(response.data)
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

    loadAlerts()

    return () => {
      isCancelled = true
    }
  }, [api, userRole, statusFilter, riskFilter])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'therapist') {
    return <Navigate to="/dashboard" replace />
  }

  let filteredAlerts = alerts

  if (statusFilter) {
    filteredAlerts = filteredAlerts.filter((alert) => alert.status === statusFilter)
  }

  if (riskFilter) {
    filteredAlerts = filteredAlerts.filter((alert) => alert.risk_level === riskFilter)
  }

  const pendingCount = alerts.filter((alert) => alert.status === 'pending').length
  const highRiskCount = alerts.filter((alert) => alert.risk_level === 'high').length

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Sistema d&apos;alertes</p>
            <h1 className="section-title">Alertes rebudes</h1>
            <div className="entries-toolbar">
              <span className="status-pill dashboard-status-pill--pending">
                {pendingCount} pendents
              </span>
              <span className="status-pill risk-pill--high">
                {highRiskCount} risc alt
              </span>
              <span className="status-pill dashboard-status-pill--muted">
                {alerts.length} totals
              </span>
            </div>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          {error ? <div className="error-banner">{error}</div> : null}
          <div className="inline-fields">
            <div className="field-group">
              <label htmlFor="status-filter">Estat</label>
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">Tots els estats</option>
                <option value="pending">Pendent</option>
                <option value="validated">Validada</option>
                <option value="dismissed">Descartada</option>
              </select>
            </div>

            <div className="field-group">
              <label htmlFor="risk-filter">Nivell de risc</label>
              <select
                id="risk-filter"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
              >
                <option value="">Tots els nivells</option>
                <option value="high">Alt</option>
                <option value="moderate">Moderat</option>
                <option value="low">Baix</option>
                <option value="none">Cap</option>
              </select>
            </div>
          </div>

          {statusFilter || riskFilter ? (
            <div className="button-row">
              <button
                type="button"
                className="action-chip"
                onClick={() => {
                  setStatusFilter('')
                  setRiskFilter('')
                }}
              >
                Netejar filtres
              </button>
            </div>
          ) : null}
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow eyebrow--flush">Llista d&apos;alertes</p>
          </div>
          {loading ? (
            <p className="muted">Carregant alertes...</p>
          ) : filteredAlerts.length === 0 ? (
            <p className="muted">No hi ha alertes disponibles.</p>
          ) : (
            <ul className="patient-list">
              {filteredAlerts.map((alert) => (
                <li key={alert.id}>
                  <Link
                    to={`/alerts/${alert.id}`}
                    className="compact-list-item"
                    style={{ display: 'block', color: 'inherit', textDecoration: 'none' }}
                  >
                    <div className="item-heading-row">
                      <strong>{alert.patient_name}</strong>
                      <span className={`status-pill ${alertStatusClassName(alert.status)}`}>
                        {formatAlertStatus(alert.status)}
                      </span>
                      <span className={`status-pill ${riskClassName(alert.risk_level)}`}>
                        {formatRiskLevel(alert.risk_level)}
                      </span>
                    </div>
                    <p className="muted" style={{ margin: '0.5rem 0 0' }}>
                      Data: {formatAlertDate(alert.created_at)}
                    </p>
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

function formatAlertDate(date) {
  if (!date) {
    return 'No disponible'
  }

  return new Date(date).toLocaleDateString('ca-ES')
}
