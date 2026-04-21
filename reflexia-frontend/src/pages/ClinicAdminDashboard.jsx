import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function ClinicAdminDashboard() {
  const { user, isClinicAdmin, getClinicStats, registerTherapist } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // Use the first admin membership for the dashboard info
  const adminMembership = user?.memberships?.find(m => m.is_admin)
  const organisation = adminMembership?.organisation

  if (!user || !isClinicAdmin) {
    return <Navigate to="/dashboard" replace />
  }

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await getClinicStats()
        setStats(data)
      } catch (err) {
        setError('Error carregant les estadístiques de la clínica.')
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [])

  async function handleInviteSubmit(e) {
    e.preventDefault()
    setInviteError('')
    setInviteMessage('')
    setIsSubmitting(true)

    try {
      // Logic in backend will automatically assign therapist to this ClinicAdmin's organisation
      const response = await registerTherapist(inviteForm)
      setInviteMessage(`Invitació enviada correctament a ${response.email}. El terapeuta ha estat assignat a la teva clínica.`)
      setInviteForm({
        first_name: '',
        last_name: '',
        email: '',
        license_number: '',
        specialty: '',
      })
    } catch (err) {
      setInviteError('Error al registrar el terapeuta.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Administració de Clínica</p>
            <h1 className="section-title">
              {organisation?.name || 'La teva Clínica'}
            </h1>
          </div>

          {error && <div className="error-banner">{error}</div>}

          <div className="stat-list">
            <div className="stat-card">
              <span>Terapeutes assignats</span>
              <strong>{loading ? '...' : stats?.total_therapists || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Pacients totals</span>
              <strong>{loading ? '...' : stats?.total_patients || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Pla</span>
              <strong>{organisation?.plan?.toUpperCase() || 'FREE'}</strong>
            </div>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Detalls de l&apos;Entitat</p>
            <h2>Informació de l&apos;Organització</h2>
          </div>
          
          <div className="management-grid" style={{ marginTop: '1.5rem' }}>
            <div className="screen-card entity-card" style={{ padding: '1.5rem' }}>
                <p className="entity-card__meta"><strong>ID de l&apos;Organització:</strong> {organisation?.id}</p>
                <p className="entity-card__meta"><strong>Tipus:</strong> {organisation?.type === 'clinic' ? 'Clínica / Centre' : 'Individual / Professional'}</p>
                <p className="entity-card__meta"><strong>Data de Registre:</strong> {new Date(organisation?.created_at).toLocaleDateString()}</p>
                <p className="entity-card__meta">
                  <strong>Estat:</strong> 
                  <span className={`status-pill ${organisation?.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--muted'}`} style={{ marginLeft: '0.5rem' }}>
                    {organisation?.is_active ? 'Activa' : 'Inactiva'}
                  </span>
                </p>
            </div>
          </div>

          <div className="button-row" style={{ marginTop: '2rem' }}>
            <button className="button-ghost" onClick={() => window.location.href = '/admin/therapists'}>
              Gestionar Equip de Terapeutes
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
