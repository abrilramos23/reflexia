import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function PlatformTherapistsPage() {
  const { user, listOrganisations, registerTherapist, listAllTherapists } = useAuth()
  const [organisations, setOrganisations] = useState([])
  const [therapists, setTherapists] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('list') // 'list' | 'create'

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    license_number: '',
    specialty: '',
    organisation_id: '',
    is_admin: false,
  })
  const [message, setMessage] = useState('')
  const [devLink, setDevLink] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!user || user.role !== 'platform_admin') {
    return <Navigate to="/dashboard" replace />
  }

  const loadData = async () => {
    try {
      const [oData, tData] = await Promise.all([
        listOrganisations(),
        listAllTherapists()
      ])
      setOrganisations(oData)
      setTherapists(tData)
    } catch (err) {
      setError('Error carregant dades dels terapeutes.')
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
    setSubmitError('')
    try {
      const result = await registerTherapist(form)
      setMessage('Terapeuta registrat correctament.')
      if (result.activation_url) {
        setDevLink(result.activation_url)
      }
      setForm({
        first_name: '', last_name: '', email: '',
        license_number: '', specialty: '', organisation_id: '', is_admin: false,
      })
      await loadData()
      // Don't auto-redirect if there's a dev link
      if (!result.activation_url) {
        setTimeout(() => setView('list'), 1500)
      }
    } catch (err) {
      setSubmitError('Error registrant el terapeuta.')
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
              <p className="eyebrow">Nou Terapeuta</p>
              <h1>Registrar Professional</h1>
            </div>
            <button className="button-ghost" onClick={() => setView('list')}>
              Tornar a la llista
            </button>
          </div>

          <section className="screen-card dashboard-panel">
            {message && (
              <div className="message">
                <p>{message}</p>
                {devLink && (
                  <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.05)', borderRadius: '8px', border: '1px dashed var(--accent)' }}>
                    <p className="tiny" style={{ marginBottom: '0.5rem', fontWeight: 'bold', color: 'var(--accent)' }}>Sincronització de Desenvolupament (Email a la consola):</p>
                    <a href={devLink} className="text-link" style={{ wordBreak: 'break-all' }}>{devLink}</a>
                  </div>
                )}
              </div>
            )}
            {submitError && <div className="error-banner">{submitError}</div>}
            <form className="form-stack" onSubmit={handleSubmit}>
              <div className="field-group">
                <label>Organització (Opcional)</label>
                <select 
                  value={form.organisation_id} 
                  onChange={e => setForm({...form, organisation_id: e.target.value, is_admin: e.target.value ? form.is_admin : false})}
                >
                  <option value="">Cap (Independent)</option>
                  {organisations.map(o => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
                <p className="tiny muted">Si no se selecciona cap, es considerarà un terapeuta autònom.</p>
              </div>
              {form.organisation_id ? (
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={form.is_admin}
                    onChange={(e) => setForm({...form, is_admin: e.target.checked})}
                  />
                  <span>Assignar també com a administrador de l&apos;organització</span>
                </label>
              ) : null}
              <div className="inline-fields">
                <div className="field-group">
                  <label>Nom</label>
                  <input
                    value={form.first_name}
                    onChange={(e) => setForm({...form, first_name: e.target.value})}
                    placeholder="Nom"
                    required
                  />
                </div>
                <div className="field-group">
                  <label>Cognoms</label>
                  <input
                    value={form.last_name}
                    onChange={(event) => setForm({...form, last_name: event.target.value})}
                    placeholder="Cognoms"
                    required
                  />
                </div>
              </div>
              <div className="field-group">
                <label>Email de Professional</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({...form, email: e.target.value})}
                  placeholder="professional@email.com"
                  required
                />
              </div>
              <div className="inline-fields">
                <div className="field-group">
                  <label>Núm. Col·legiat</label>
                  <input
                    value={form.license_number}
                    onChange={(e) => setForm({...form, license_number: e.target.value})}
                    placeholder="Ex: 12345-C"
                    required
                  />
                </div>
                <div className="field-group">
                  <label>Especialitat</label>
                  <input
                    value={form.specialty}
                    onChange={(e) => setForm({...form, specialty: e.target.value})}
                    placeholder="Ex: Psicologia Clínica"
                    required
                  />
                </div>
              </div>
              <div className="button-row" style={{ marginTop: '2rem' }}>
                <button className="button" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Registrant...' : 'Registrar Terapeuta'}
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
              <h1 className="section-title">Terapeutes</h1>
            </div>
            <button className="button" onClick={() => setView('create')}>
              Nou Terapeuta
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {loading ? (
            <p>Carregant...</p>
          ) : (
            <div className="management-grid">
              {therapists.map((t) => (
                <div key={t.id} className="screen-card entity-card">
                  <div className="entity-card__header">
                    <h3 className="entity-card__title">{t.first_name} {t.last_name}</h3>
                    <div className="item-heading-row">
                      <span className={`status-pill ${t.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--pending'}`}>
                        {t.is_active ? 'Actiu' : 'Pendent'}
                      </span>
                      {t.is_clinic_admin ? (
                        <span className="status-pill dashboard-status-pill--active">
                          Admin
                        </span>
                      ) : null}
                    </div>
                  </div>
                  <div className="entity-card__body">
                    <p className="entity-card__meta">
                      <strong>Especialitat:</strong> {t.specialty}
                    </p>
                    <p className="entity-card__meta">
                      <strong>Col·legiat:</strong> {t.license_number}
                    </p>
                    <p className="entity-card__meta">
                      <strong>Organització:</strong> {t.organisation?.name || 'Independent'}
                    </p>
                    <p className="entity-card__meta">
                      <strong>Email:</strong> {t.email}
                    </p>
                  </div>
                  <div className="entity-card__footer">
                    <span className="tiny muted">Registrat: {new Date(t.registration_date).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
              {therapists.length === 0 && (
                <div className="screen-card dashboard-panel profile-card--wide" style={{ textAlign: 'center', padding: '4rem' }}>
                   <p className="muted">No hi ha terapeutes registrats encara.</p>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
