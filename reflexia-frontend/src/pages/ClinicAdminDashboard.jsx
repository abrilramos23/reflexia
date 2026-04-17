import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function ClinicAdminDashboard() {
  const { user, getClinicStats, registerTherapist } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const [inviteForm, setInviteForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    license_number: '',
    specialty: '',
  })
  const [inviteMessage, setInviteMessage] = useState('')
  const [inviteError, setInviteError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!user || user.role !== 'clinic_admin') {
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
              {user.organisation?.name || 'La teva Clínica'}
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
              <span>Plà</span>
              <strong>{user.organisation?.plan || 'Estàndard'}</strong>
            </div>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Equip</p>
            <h2>Registrar Nou Terapeuta</h2>
            <p className="muted">Afegeix un professional al teu equip. Rebrà un correu d'activació.</p>
          </div>

          {inviteMessage && <div className="message">{inviteMessage}</div>}
          {inviteError && <div className="error-banner">{inviteError}</div>}

          <form className="form-stack" onSubmit={handleInviteSubmit}>
            <div className="inline-fields">
              <div className="field-group">
                <label>Nom</label>
                <input
                  value={inviteForm.first_name}
                  onChange={(e) => setInviteForm({...inviteForm, first_name: e.target.value})}
                  required
                />
              </div>
              <div className="field-group">
                <label>Cognoms</label>
                <input
                  value={inviteForm.last_name}
                  onChange={(e) => setInviteForm({...inviteForm, last_name: e.target.value})}
                  required
                />
              </div>
            </div>
            <div className="inline-fields">
              <div className="field-group">
                <label>Correu electrònic</label>
                <input
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({...inviteForm, email: e.target.value})}
                  required
                />
              </div>
              <div className="field-group">
                <label>Núm. Col·legiat</label>
                <input
                  value={inviteForm.license_number}
                  onChange={(e) => setInviteForm({...inviteForm, license_number: e.target.value})}
                  required
                />
              </div>
            </div>
            <div className="field-group">
              <label>Especialitat</label>
              <input
                value={inviteForm.specialty}
                onChange={(e) => setInviteForm({...inviteForm, specialty: e.target.value})}
                required
              />
            </div>
            <div className="button-row">
              <button className="button-secondary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Enviant...' : 'Registrar a la Clínica'}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}
