import { useEffect, useState } from 'react'
import { FaEdit, FaTrash, FaArrowLeft } from 'react-icons/fa'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function PlatformOrganisationsPage() {
  const { user, listOrganisations, createOrganisation, updateOrganisation, deleteOrganisation } = useAuth()
  const [organisations, setOrganisations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('list') // 'list' | 'create' | 'edit'
  const [selectedOrganisation, setSelectedOrganisation] = useState(null)

  const [orgForm, setOrgForm] = useState({ name: '', type: 'clinic', is_active: true })
  const [orgMessage, setOrgMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!user || user.role !== 'platform_admin') {
    return <Navigate to="/dashboard" replace />
  }

  const loadOrganisations = async () => {
    try {
      const data = await listOrganisations()
      setOrganisations(data)
    } catch (err) {
      setError('Error carregant les organitzacions.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOrganisations()
  }, [])

  async function handleOrgSubmit(e) {
    e.preventDefault()
    setIsSubmitting(true)
    setOrgMessage('')
    try {
      const { is_active, ...createPayload } = orgForm
      await createOrganisation(createPayload)
      setOrgMessage('Organització creada correctament.')
      setOrgForm({ name: '', type: 'clinic', is_active: true })
      await loadOrganisations()
      setTimeout(() => setView('list'), 1500)
    } catch (err) {
      setOrgMessage('Error creant l\'organització.')
    } finally {
      setIsSubmitting(false)
    }
  }

  function openCreateView() {
    setSelectedOrganisation(null)
    setOrgForm({ name: '', type: 'clinic', is_active: true })
    setOrgMessage('')
    setView('create')
  }

  function openEditView(organisation) {
    setSelectedOrganisation(organisation)
    setOrgForm({
      name: organisation.name,
      type: organisation.type,
      is_active: organisation.is_active,
    })
    setOrgMessage('')
    setView('edit')
  }

  async function handleOrgUpdate(e) {
    e.preventDefault()
    setIsSubmitting(true)
    setOrgMessage('')

    try {
      await updateOrganisation(selectedOrganisation.id, orgForm)
      setOrgMessage('Organització actualitzada correctament.')
      await loadOrganisations()
      setTimeout(() => setView('list'), 1000)
    } catch (err) {
      setOrgMessage('Error actualitzant l\'organització.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDeleteOrganisation(organisation) {
    if (!window.confirm(`Vols eliminar ${organisation.name}? L'organització quedarà inactiva.`)) {
      return
    }

    try {
      await deleteOrganisation(organisation.id)
      await loadOrganisations()
    } catch (err) {
      setError('Error eliminant l\'organització.')
    }
  }

  if (view === 'create' || view === 'edit') {
    const isEdit = view === 'edit'

    return (
      <div className="screen-shell">
        <div className="full-screen-form-shell">
          <div className="form-header">
            <div>
              <h1>{isEdit ? 'Editar Organització' : 'Registrar Organització'}</h1>
            </div>
             <button className="button-ghost" onClick={() => setView('list')} title="Tornar">
              <FaArrowLeft />
            </button>
          </div>

          <section className="screen-card dashboard-panel">
            {orgMessage && (
              <div className={`message ${orgMessage.includes('Error') ? 'error-banner' : ''}`}>
                {orgMessage}
              </div>
            )}
            <form className="form-stack" onSubmit={isEdit ? handleOrgUpdate : handleOrgSubmit}>
              <div className="field-group">
                <label>Nom de l&apos;Organització</label>
                <input 
                  value={orgForm.name} 
                  onChange={e => setOrgForm({...orgForm, name: e.target.value})} 
                  placeholder="Ex: Clínica Nexus"
                  required 
                />
              </div>
                <div className="field-group">
                  <label>Tipus</label>
                  <select 
                    value={orgForm.type} 
                    onChange={e => setOrgForm({...orgForm, type: e.target.value})}
                  >
                    <option value="clinic">Clínica / Centre</option>
                  </select>
                </div>
              {isEdit ? (
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={orgForm.is_active}
                    onChange={e => setOrgForm({...orgForm, is_active: e.target.checked})}
                  />
                  <span>Organització activa</span>
                </label>
              ) : null}
              <div className="button-row" style={{ marginTop: '2rem' }}>
                <button className="button" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Desant...' : isEdit ? 'Guardar canvis' : 'Confirmar i Crear'}
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
              <h1 className="section-title">Organitzacions</h1>
            </div>
            <button className="button" onClick={openCreateView}>
              Nova Organització
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {loading ? (
            <p>Carregant...</p>
          ) : (
            <div className="management-grid">
              {organisations.map((org) => (
                <div key={org.id} className="screen-card entity-card">
                  <div className="entity-card__header">
                    <h3 className="entity-card__title">{org.name}</h3>
                    <span className={`status-pill ${org.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--muted'}`}>
                      {org.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                  </div>
                  <div className="entity-card__body">
                    <p className="entity-card__meta">
                      <strong>Tipus:</strong> Clínica / Centre
                    </p>
                  </div>
                  <div className="entity-card__footer">
                    <span className="tiny muted">ID: {org.id}</span>
                     <div className="button-row entity-actions">
                       <button className="button-ghost" type="button" onClick={() => openEditView(org)} title="Editar" aria-label="Editar">
                        <FaEdit />
                      </button>
                      <button className="button-danger" type="button" onClick={() => handleDeleteOrganisation(org)} title="Eliminar" aria-label="Eliminar">
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {organisations.length === 0 && (
                <div className="screen-card dashboard-panel profile-card--wide" style={{ textAlign: 'center', padding: '4rem' }}>
                   <p className="muted">No hi ha organitzacions registrades encara.</p>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
