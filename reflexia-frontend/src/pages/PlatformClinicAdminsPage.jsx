import { useEffect, useState } from 'react'
import { FaEdit, FaTrash, FaArrowLeft } from 'react-icons/fa'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function PlatformClinicAdminsPage() {
  const {
    user,
    listOrganisations,
    registerClinicAdmin,
    listAllClinicAdmins,
    listAllTherapists,
    updateClinicAdmin,
    deleteClinicAdmin,
  } = useAuth()
  const [organisations, setOrganisations] = useState([])
  const [admins, setAdmins] = useState([])
  const [therapists, setTherapists] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('list') // 'list' | 'create' | 'edit'
  const [selectedAdmin, setSelectedAdmin] = useState(null)

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
      await registerClinicAdmin({
        organisation_id: form.organisation_id,
        therapist_id: form.therapist_id,
      })
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

  function openCreateView() {
    setSelectedAdmin(null)
    setForm({ organisation_id: '', therapist_id: '' })
    setMessage('')
    setView('create')
  }

  function openEditView(admin) {
    setSelectedAdmin(admin)
    setForm({
      organisation_id: admin.organisation?.id || '',
      therapist_id: admin.id,
      first_name: admin.first_name,
      last_name: admin.last_name,
      email: admin.email,
      license_number: admin.license_number || '',
      specialty: admin.specialty || '',
      is_active: admin.is_active,
    })
    setMessage('')
    setView('edit')
  }

  async function handleUpdate(e) {
    e.preventDefault()
    setIsSubmitting(true)
    setMessage('')

    try {
      await updateClinicAdmin(selectedAdmin.id, {
        organisation_id: form.organisation_id,
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        license_number: form.license_number,
        specialty: form.specialty,
        is_active: form.is_active,
      })
      setMessage('Administrador actualitzat correctament.')
      await loadData()
      setTimeout(() => setView('list'), 1000)
    } catch (err) {
      setMessage('Error actualitzant l\'administrador.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDelete(admin) {
    if (!window.confirm(`Vols eliminar ${admin.first_name} ${admin.last_name} com a admin de clínica?`)) {
      return
    }

    try {
      await deleteClinicAdmin(admin.id)
      await loadData()
    } catch (err) {
      setError('Error eliminant l\'administrador. Pot ser l’únic admin d’una clínica amb membres.')
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

  if (view === 'create' || view === 'edit') {
    const isEdit = view === 'edit'

    return (
      <div className="screen-shell">
        <div className="full-screen-form-shell">
          <div className="form-header">
            <div>
              <h1>{isEdit ? 'Editar Admin de Clínica' : 'Assignar Admin de Clínica'}</h1>
            </div>
             <button className="button-ghost" onClick={() => setView('list')} title="Tornar">
              <FaArrowLeft />
            </button>
          </div>

          <section className="screen-card dashboard-panel">
            {message && (
              <div className={`message ${message.includes('Error') ? 'error-banner' : ''}`}>
                <p>{message}</p>
              </div>
            )}
            <form className="form-stack" onSubmit={isEdit ? handleUpdate : handleSubmit}>
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
              {isEdit ? (
                <>
                  <div className="inline-fields">
                    <div className="field-group">
                      <label>Nom</label>
                      <input value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} required />
                    </div>
                    <div className="field-group">
                      <label>Cognoms</label>
                      <input value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} required />
                    </div>
                  </div>
                  <div className="field-group">
                    <label>Email</label>
                    <input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} required />
                  </div>
                  <div className="inline-fields">
                    <div className="field-group">
                      <label>Núm. col·legiat</label>
                      <input value={form.license_number} onChange={e => setForm({...form, license_number: e.target.value})} required />
                    </div>
                    <div className="field-group">
                      <label>Especialitat</label>
                      <input value={form.specialty} onChange={e => setForm({...form, specialty: e.target.value})} required />
                    </div>
                  </div>
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={e => setForm({...form, is_active: e.target.checked})}
                    />
                    <span>Compte actiu</span>
                  </label>
                </>
              ) : (
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
              )}
              <div className="button-row" style={{ marginTop: '2rem' }}>
                <button className="button-secondary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Desant...' : isEdit ? 'Guardar canvis' : 'Assignar com a administrador'}
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
            <button className="button" onClick={openCreateView}>
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
                     <div className="button-row entity-actions">
                       <button className="button-ghost" type="button" onClick={() => openEditView(admin)} title="Editar" aria-label="Editar">
                        <FaEdit />
                      </button>
                      <button className="button-danger" type="button" onClick={() => handleDelete(admin)} title="Eliminar" aria-label="Eliminar">
                        <FaTrash />
                      </button>
                    </div>
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
