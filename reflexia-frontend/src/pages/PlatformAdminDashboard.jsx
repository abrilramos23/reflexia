import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function PlatformAdminDashboard() {
  const { user, getPlatformStats } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  if (!user || user.role !== 'platform_admin') {
    return <Navigate to="/dashboard" replace />
  }

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await getPlatformStats()
        setStats(data)
      } catch (err) {
        setError('Error carregant les estadístiques de la plataforma.')
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [])

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Administració de Plataforma</p>
            <h1 className="section-title">Tauler de Control Global</h1>
            <p className="muted">Benvingut al panell de control central de Reflexia. Aquí pots supervisar el creixement de la plataforma.</p>
          </div>

          {error && <div className="error-banner">{error}</div>}

          <div className="stat-list">
            <div className="stat-card">
              <span>Organitzacions</span>
              <strong>{loading ? '...' : stats?.total_organisations || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Usuaris Totals</span>
              <strong>{loading ? '...' : stats?.total_users || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Terapeutes</span>
              <strong>{loading ? '...' : stats?.users_by_role?.therapist || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Pacients</span>
              <strong>{loading ? '...' : stats?.users_by_role?.patient || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Admins de Clínica</span>
              <strong>{loading ? '...' : stats?.total_clinic_admins || 0}</strong>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
