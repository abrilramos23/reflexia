import { useEffect, useState } from 'react'
import { FaEdit, FaTrash, FaUsers } from 'react-icons/fa'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'

export function ClinicAdminDashboard() {
  const { user, isClinicAdmin, getClinicStats, updateOrganisation, deleteOrganisation, refreshProfile } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [isEditingOrganisation, setIsEditingOrganisation] = useState(false)
  const [organisationForm, setOrganisationForm] = useState({ name: '', type: 'clinic', is_active: true })
  const [organisationMessage, setOrganisationMessage] = useState('')
  const [isSubmittingOrganisation, setIsSubmittingOrganisation] = useState(false)

  const organisation = user?.organisation ?? user?.memberships?.find((membership) => membership.is_admin)?.organisation

  useEffect(() => {
    async function loadStats() {
      if (!user || !isClinicAdmin) {
        setLoading(false)
        return
      }

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
  }, [isClinicAdmin, user?.id])

  useEffect(() => {
    if (!organisation) {
      return
    }

    setOrganisationForm({
      name: organisation.name || '',
      type: organisation.type || 'clinic',
      is_active: Boolean(organisation.is_active),
    })
  }, [organisation?.id, organisation?.name, organisation?.type, organisation?.is_active])

  async function handleOrganisationSubmit(e) {
    e.preventDefault()
    setOrganisationMessage('')
    setIsSubmittingOrganisation(true)

    try {
      await updateOrganisation(organisation.id, organisationForm)
      await refreshProfile()
      setOrganisationMessage('Organització actualitzada correctament.')
      setIsEditingOrganisation(false)
    } catch (err) {
      setOrganisationMessage('Error actualitzant l\'organització.')
    } finally {
      setIsSubmittingOrganisation(false)
    }
  }

  async function handleDeleteOrganisation() {
    if (!window.confirm(`Vols eliminar ${organisation.name}? L\'organització quedarà inactiva.`)) {
      return
    }

    try {
      await deleteOrganisation(organisation.id)
      await refreshProfile()
      setOrganisationMessage('Organització eliminada correctament.')
    } catch (err) {
      setOrganisationMessage('Error eliminant l\'organització.')
    }
  }

  if (!user || !isClinicAdmin) {
    return <Navigate to="/dashboard" replace />
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
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow" style={{ marginBottom: '0' }}>Detalls de l&apos;Organització</p>
          </div>
          {organisationMessage && (
            <div className={`message ${organisationMessage.includes('Error') ? 'error-banner' : ''}`}>
              <p>{organisationMessage}</p>
            </div>
          )}
          
          <ul className="patient-list" style={{ marginTop: '1rem' }}>
            <li className="compact-list-item">
              <div style={{ display: 'flex', width: '100%', alignItems: 'center' }}>
                <div style={{ flex: 1 }}>
                  {isEditingOrganisation ? (
                    <form className="form-stack" onSubmit={handleOrganisationSubmit}>
                      <div className="field-group">
                        <label>Nom de l&apos;Organització</label>
                        <input
                          value={organisationForm.name}
                          onChange={event => setOrganisationForm({...organisationForm, name: event.target.value})}
                          required
                        />
                      </div>
                      <label className="checkbox-row">
                        <input
                          type="checkbox"
                          checked={organisationForm.is_active}
                          onChange={event => setOrganisationForm({...organisationForm, is_active: event.target.checked})}
                        />
                        <span>Organització activa</span>
                      </label>
                      <div className="button-row">
                        <button className="button" type="submit" disabled={isSubmittingOrganisation}>
                          {isSubmittingOrganisation ? 'Desant...' : 'Guardar canvis'}
                        </button>
                        <button className="button-ghost" type="button" onClick={() => setIsEditingOrganisation(false)}>
                          Cancel·lar
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <div className="item-heading-row">
                        <strong>{organisation?.name}</strong>
                        <span className={`status-pill ${organisation?.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--muted'}`}>
                          {organisation?.is_active ? 'Activa' : 'Inactiva'}
                        </span>
                      </div>
                      <p className="muted" style={{ fontWeight: 'bold', margin: '0.5rem 0' }}>
                        {organisation?.type === 'clinic' ? 'Clínica / Centre' : 'Individual / Professional'}
                      </p>
                      <p className="muted" style={{ margin: 0 }}>
                        ID: {organisation?.id}
                        <br />
                        Data de Registre: {new Date(organisation?.created_at).toLocaleDateString()}
                      </p>
                    </>
                  )}
                </div>

                {!isEditingOrganisation && (
                  <div className="list-actions" style={{ marginLeft: '1rem' }}>
                    <button
                      className="action-chip action-chip--icon"
                      type="button"
                      onClick={() => setIsEditingOrganisation(true)}
                      title="Editar Organització"
                    >
                      <FaEdit />
                    </button>
                    <button
                      className="action-chip action-chip--danger action-chip--icon"
                      type="button"
                      onClick={handleDeleteOrganisation}
                      title="Eliminar Organització"
                    >
                      <FaTrash />
                    </button>
                  </div>
                )}
              </div>
            </li>
          </ul>
        </section>
      </div>
    </div>
  )
}
