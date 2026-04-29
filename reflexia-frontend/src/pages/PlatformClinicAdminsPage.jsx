import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function PlatformClinicAdminsPage() {
  const { user, listOrganisations, registerClinicAdmin, listAllClinicAdmins } = useAuth()
  const [organisations, setOrganisations] = useState([])
  const [admins, setAdmins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('list') // 'list' | 'create'

  const [form, setForm] = useState({ 
    first_name: '', last_name: '', email: '', organisation_id: '' 
  })
  const [message, setMessage] = useState('')
  const [devLink, setDevLink] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!user || user.role !== 'platform_admin') {
    return <Navigate to="/dashboard" replace />
  }

  const loadData = async () => {
    try {
      const [oData, aData] = await Promise.all([
        listOrganisations(),
        listAllClinicAdmins()
      ])
      setOrganisations(oData.filter(o => o.type === 'clinic'))
      setAdmins(aData)
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
      const result = await registerClinicAdmin(form)
      setMessage('Administrador registrat correctament.')
      if (result.activation_url) {
        setDevLink(result.activation_url)
      }
      setForm({ first_name: '', last_name: '', email: '', organisation_id: '' })
      await loadData()
      // Don't auto-redirect if there's a dev link, so the user can copy it
      if (!result.activation_url) {
        setTimeout(() => setView('list'), 1500)
      }
    } catch (err) {
      setMessage('Error registrant l\'administrador.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (view === 'create') {
    return (
      <div className="screen-shell">
        <div className="full-screen-form-shell">
          <div className="form-header">
            <div>
              <h1>Registrar Admin de Clínica</h1>
            </div>
            <button className="button-ghost" onClick={() => setView('list')}>
              Tornar a la llista
            </button>
          </div>

          <section className="screen-card dashboard-panel">
            {message && (
              <div className={`message ${message.includes('Error') ? 'error-banner' : ''}`}>
                <p>{message}</p>
                {devLink && (
                  <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.05)', borderRadius: '8px', border: '1px dashed var(--accent)' }}>
                    <p className="tiny" style={{ marginBottom: '0.5rem', fontWeight: 'bold', color: 'var(--accent)' }}>Sincronització de Desenvolupament (Email a la consola):</p>
                    <a href={devLink} className="text-link" style={{ wordBreak: 'break-all' }}>{devLink}</a>
                  </div>
                )}
              </div>
            )}
            <form className="form-stack" onSubmit={handleSubmit}>
              <div className="field-group">
                <label>Clínica Assignada</label>
                <select 
                  value={form.organisation_id} 
                  onChange={e => setForm({...form, organisation_id: e.target.value})}
                  required
                >
                  <option value="">Selecciona una clínica...</option>
                  {organisations.map(o => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
              </div>
              <div className="inline-fields">
                <div className="field-group">
                  <label>Nom</label>
                  <input 
                    value={form.first_name} 
                    onChange={e => setForm({...form, first_name: e.target.value})} 
                    placeholder="Nom de pila"
                    required 
                  />
                </div>
                <div className="field-group">
                  <label>Cognoms</label>
                  <input 
                    value={form.last_name} 
                    onChange={e => setForm({...form, last_name: e.target.value})} 
                    placeholder="Cognoms complets"
                    required 
                  />
                </div>
              </div>
              <div className="field-group">
                <label>Correu Electrònic</label>
                <input 
                  type="email" 
                  value={form.email} 
                  onChange={e => setForm({...form, email: e.target.value})} 
                  placeholder="admin@clinica.com"
                  required 
                />
              </div>
              <div className="button-row" style={{ marginTop: '2rem' }}>
                <button className="button-secondary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Registrant...' : 'Registrar Administrador'}
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
              Registrar Admin
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
                    <p className="entity-card__meta">
                      <strong>Email:</strong> {admin.email}
                    </p>
                    <p className="entity-card__meta">
                      <strong>Clínica:</strong> {admin.organisation?.name || 'No assignada'}
                    </p>
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
