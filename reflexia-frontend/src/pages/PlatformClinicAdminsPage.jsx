import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function PlatformClinicAdminsPage() {
  const { user, listOrganisations, registerClinicAdmin, listAllClinicAdmins, listAllTherapists } = useAuth()
  const [organisations, setOrganisations] = useState([])
  const [admins, setAdmins] = useState([])
  const [therapists, setTherapists] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('list') // 'list' | 'create'

  const [form, setForm] = useState({ 
    organisation_id: '', therapist_id: '',
  })
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!user || user.role !== 'platform_admin') {
    return <Navigate to="/dashboard" replace />
  }

  const loadData = async () => {
    try {
      const [oData, aData, tData] = await Promise.all([
        listOrganisations(),
        listAllClinicAdmins(),
        listAllTherapists(),
      ])
      setOrganisations(oData.filter(o => o.type === 'clinic'))
      setAdmins(aData)
      setTherapists(tData)
    } catch (err) {
      setError('Error carregant dades dels administradors.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setIsSubmitting(true)
    setMessage('')
    try {
      await registerClinicAdmin(form)
      setMessage('Administrador assignat correctament.')
      setForm({ organisation_id: '', therapist_id: '' })
      await loadData()
      setTimeout(() => setView('list'), 1500)
    } catch (err) {
      setMessage('Error registrant l\'administrador.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const availableTherapists = therapists.filter((therapist) => {
    if (!form.organisation_id) {
      return false
    }

    return (
      therapist.organisation?.id === form.organisation_id
      && !therapist.is_clinic_admin
    )
  })

  if (view === 'create') {
    return (
      <div className="screen-shell">
        <div className="full-screen-form-shell">
          <div className="form-header">
            <div>
              <h1>Assignar Admin de Clínica</h1>
            </div>
            <button className="button-ghost" onClick={() => setView('list')}>
              Tornar a la llista
            </button>
          </div>

          <section className="screen-card dashboard-panel">
            {message && (
              <div className={`message ${message.includes('Error') ? 'error-banner' : ''}`}>
                <p>{message}</p>
              </div>
            )}
            <form className="form-stack" onSubmit={handleSubmit}>
              <div className="field-group">
                <label>Clínica Assignada</label>
                <select 
                  value={form.organisation_id} 
                  onChange={e => setForm({...form, organisation_id: e.target.value, therapist_id: ''})}
                  required
                >
                  <option value="">Selecciona una clínica...</option>
                  {organisations.map(o => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
              </div>
              <div className="field-group">
                <label>Terapeuta de la clínica</label>
                <select
                  value={form.therapist_id}
                  onChange={e => setForm({...form, therapist_id: e.target.value})}
                  required 
                  disabled={!form.organisation_id}
                >
                  <option value="">
                    {form.organisation_id ? 'Selecciona un terapeuta...' : 'Selecciona primer una clínica...'}
                  </option>
                  {availableTherapists.map((therapist) => (
                    <option key={therapist.id} value={therapist.id}>
                      {therapist.first_name} {therapist.last_name} · {therapist.specialty} · {therapist.license_number}
                    </option>
                  ))}
                </select>
                <p className="tiny muted">
                  Només es mostren terapeutes d’aquesta organització que encara no siguin administradors.
                </p>
              </div>
              <div className="button-row" style={{ marginTop: '2rem' }}>
                <button className="button-secondary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Assignant...' : 'Assignar com a administrador'}
                </button>
                <button className="button-ghost" type="button" onClick={() => setView('list')}>
                  Cancel·lar
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="form-header">
            <div>
              <p className="eyebrow">Administració</p>
              <h1 className="section-title">Admins de Clínica</h1>
            </div>
            <button className="button" onClick={() => setView('create')}>
              Assignar Admin
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {loading ? (
            <p>Carregant...</p>
          ) : (
            <div className="management-grid">
              {admins.map((admin) => (
                <div key={admin.id} className="screen-card entity-card">
                  <div className="entity-card__header">
                    <h3 className="entity-card__title">{admin.first_name} {admin.last_name}</h3>
                    <span className={`status-pill ${admin.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--pending'}`}>
                      {admin.is_active ? 'Actiu' : 'Pendent'}
                    </span>
                  </div>
                  <div className="entity-card__body">
                    <section className="entity-card__section">
                      <p className="entity-card__section-label">Compte del terapeuta</p>
                      <p className="entity-card__meta">
                        <strong>Email:</strong> {admin.email}
                      </p>
                      <p className="entity-card__meta">
                        <strong>Especialitat:</strong> {admin.specialty || 'No disponible'}
                      </p>
                      <p className="entity-card__meta">
                        <strong>Núm. col·legiat:</strong> {admin.license_number || 'No disponible'}
                      </p>
                    </section>

                    <section className="entity-card__section">
                      <p className="entity-card__section-label">Organització</p>
                      <p className="entity-card__meta">
                        <strong>Nom:</strong> {admin.organisation?.name || 'No assignada'}
                      </p>
                      <p className="entity-card__meta">
                        <strong>Tipus:</strong> {admin.organisation?.type === 'clinic' ? 'Clínica / Centre' : 'Independent'}
                      </p>
                      <p className="entity-card__meta">
                        <strong>Estat org.:</strong> {admin.organisation?.is_active ? 'Activa' : 'Inactiva'}
                      </p>
                    </section>
                  </div>
                  <div className="entity-card__footer">
                    <span className="tiny muted">Alta: {new Date(admin.registration_date).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
              {admins.length === 0 && (
                <div className="screen-card dashboard-panel profile-card--wide" style={{ textAlign: 'center', padding: '4rem' }}>
                   <p className="muted">No hi ha administradors de clínica registrats encara.</p>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
