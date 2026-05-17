import { useEffect, useState } from 'react'
import { FaArrowLeft, FaCopy, FaEdit, FaPlus, FaTrash } from 'react-icons/fa'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function firstErrorMessage(error) {
  if (!error) {
    return 'S’ha produït un error inesperat.'
  }

  if (typeof error === 'string') {
    return error
  }

  const firstEntry = Object.values(error)[0]

  if (Array.isArray(firstEntry)) {
    return String(firstEntry[0])
  }

  if (typeof firstEntry === 'string') {
    return firstEntry
  }

  return 'S’ha produït un error inesperat.'
}

function buildRegistrationLink(token, email) {
  if (!token) {
    return ''
  }

  const params = new URLSearchParams({ token })
  if (email) {
    params.set('email', email)
  }
  return `${window.location.origin}/register/therapist?${params.toString()}`
}

export function ClinicTherapistsPage() {
  const {
    user,
    isClinicAdmin,
    listClinicTherapists,
    createOrganisationInvitation,
    updateTherapist,
    deleteTherapist,
  } = useAuth()
  const [therapists, setTherapists] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('list')
  const [selectedTherapist, setSelectedTherapist] = useState(null)
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    license_number: '',
    specialty: '',
    is_admin: false,
    is_active: false,
  })
  const [invitationForm, setInvitationForm] = useState({ email: '', dataCaducitat: '' })
  const [invitation, setInvitation] = useState(null)
  const [message, setMessage] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const organisation = user?.organisation

  if (!user || !isClinicAdmin) {
    return <Navigate to="/dashboard" replace />
  }

  const loadData = async () => {
    try {
      const data = await listClinicTherapists()
      setTherapists(data)
    } catch {
      setError('Error carregant els teus terapeutes.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  function openInviteView() {
    setSelectedTherapist(null)
    setInvitation(null)
    setInvitationForm({ email: '', dataCaducitat: '' })
    setMessage('')
    setSubmitError('')
    setView('invite')
  }

  function openEditView(therapist) {
    setSelectedTherapist(therapist)
    setForm({
      first_name: therapist.first_name,
      last_name: therapist.last_name,
      email: therapist.email,
      license_number: therapist.license_number || '',
      specialty: therapist.specialty || '',
      is_admin: therapist.is_clinic_admin,
      is_active: therapist.is_active,
    })
    setMessage('')
    setSubmitError('')
    setView('edit')
  }

  async function handleInviteSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    setMessage('')
    setSubmitError('')
    setInvitation(null)

    try {
      const payload = invitationForm.dataCaducitat
        ? { email: invitationForm.email, dataCaducitat: new Date(invitationForm.dataCaducitat).toISOString() }
        : { email: invitationForm.email }
      const result = await createOrganisationInvitation(payload)
      setInvitation(result)
      setMessage(`Invitació enviada correctament a ${result.email}.`)
      setInvitationForm({ email: '', dataCaducitat: '' })
    } catch (err) {
      setSubmitError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function copyInvitationLink() {
    if (!invitation?.token) {
      return
    }

    try {
      await navigator.clipboard.writeText(buildRegistrationLink(invitation.token, invitation.email))
      setMessage('Enllaç copiat al porta-retalls.')
    } catch {
      setSubmitError('No hem pogut copiar l’enllaç automàticament.')
    }
  }

  async function handleUpdate(event) {
    event.preventDefault()
    setIsSubmitting(true)
    setMessage('')
    setSubmitError('')

    try {
      await updateTherapist(selectedTherapist.id, form)
      setMessage('Terapeuta actualitzat correctament.')
      await loadData()
      setTimeout(() => setView('list'), 1000)
    } catch (err) {
      setSubmitError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDelete(therapist) {
    if (!window.confirm(`Vols eliminar ${therapist.first_name} ${therapist.last_name}?`)) {
      return
    }

    try {
      await deleteTherapist(therapist.id)
      await loadData()
    } catch {
      setError('Error eliminant el terapeuta. Revisa si té pacients actius o si és l\'únic administrador de la clínica.')
    }
  }

  if (view === 'invite') {
    const registrationLink = buildRegistrationLink(invitation?.token, invitation?.email)

    return (
      <div className="screen-shell">
        <div className="full-screen-form-shell">
          <div className="form-header">
            <div>
              <p className="eyebrow">{organisation?.name || 'La teva clínica'}</p>
              <h1>Nova invitació</h1>
            </div>
            <button className="button-ghost button--icon" onClick={() => setView('list')} title="Tornar" aria-label="Tornar">
              <FaArrowLeft />
            </button>
          </div>

          <section className="screen-card dashboard-panel">
            {message ? <div className="message">{message}</div> : null}
            {submitError ? <div className="error-banner">{submitError}</div> : null}

            <form className="form-stack" onSubmit={handleInviteSubmit}>
              <div className="field-group">
                <label htmlFor="invitationEmail">Correu electrònic del terapeuta</label>
                <input
                  id="invitationEmail"
                  type="email"
                  value={invitationForm.email}
                  onChange={(event) => setInvitationForm({ ...invitationForm, email: event.target.value })}
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="dataCaducitat">Caducitat</label>
                <input
                  id="dataCaducitat"
                  type="datetime-local"
                  value={invitationForm.dataCaducitat}
                  onChange={(event) => setInvitationForm({ ...invitationForm, dataCaducitat: event.target.value })}
                />
              </div>

              <div className="button-row">
                <button className="button-secondary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Generant...' : 'Generar invitació'}
                </button>
                <button className="button-ghost" type="button" onClick={() => setView('list')}>
                  Cancel·lar
                </button>
              </div>
            </form>

            {invitation ? (
              <div className="invitation-result">
                <div className="field-group">
                  <label htmlFor="invitationLink">Enllaç de registre</label>
                  <div className="copy-field">
                    <input id="invitationLink" value={registrationLink} readOnly />
                    <button className="button-ghost button--icon" type="button" onClick={copyInvitationLink} title="Copiar" aria-label="Copiar">
                      <FaCopy />
                    </button>
                  </div>
                </div>
                <p className="muted">Destinatari: {invitation.email}</p>
                <p className="muted">Token: {invitation.token}</p>
              </div>
            ) : null}
          </section>
        </div>
      </div>
    )
  }

  if (view === 'edit') {
    return (
      <div className="screen-shell">
        <div className="full-screen-form-shell">
          <div className="form-header">
            <div>
              <p className="eyebrow">{organisation?.name || 'La teva clínica'}</p>
              <h1>Editar Professional</h1>
            </div>
            <button className="button-ghost button--icon" onClick={() => setView('list')} title="Tornar" aria-label="Tornar">
              <FaArrowLeft />
            </button>
          </div>

          <section className="screen-card dashboard-panel">
            {message ? <div className="message">{message}</div> : null}
            {submitError ? <div className="error-banner">{submitError}</div> : null}

            <form className="form-stack" onSubmit={handleUpdate}>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={form.is_admin}
                  onChange={(event) => setForm({ ...form, is_admin: event.target.checked })}
                />
                <span>Assignar també com a administrador de l&apos;organització</span>
              </label>
              <div className="inline-fields">
                <div className="field-group">
                  <label>Nom</label>
                  <input
                    value={form.first_name}
                    onChange={(event) => setForm({ ...form, first_name: event.target.value })}
                    required
                  />
                </div>
                <div className="field-group">
                  <label>Cognoms</label>
                  <input
                    value={form.last_name}
                    onChange={(event) => setForm({ ...form, last_name: event.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="field-group">
                <label>Email de Professional</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(event) => setForm({ ...form, email: event.target.value })}
                  required
                />
              </div>
              <div className="inline-fields">
                <div className="field-group">
                  <label>Núm. Col·legiat</label>
                  <input
                    value={form.license_number}
                    onChange={(event) => setForm({ ...form, license_number: event.target.value })}
                    required
                  />
                </div>
                <div className="field-group">
                  <label>Especialitat</label>
                  <input
                    value={form.specialty}
                    onChange={(event) => setForm({ ...form, specialty: event.target.value })}
                    required
                  />
                </div>
              </div>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                />
                <span>Compte actiu</span>
              </label>
              <div className="button-row" style={{ marginTop: '2rem' }}>
                <button className="button-secondary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Desant...' : 'Guardar canvis'}
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
              <p className="eyebrow">{organisation?.name || 'La teva clínica'}</p>
              <h1 className="section-title">Terapeutes</h1>
            </div>
            <button className="button button--icon" onClick={openInviteView} title="Generar invitació" aria-label="Generar invitació">
              <FaPlus />
            </button>
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          {loading ? (
            <p>Carregant equip...</p>
          ) : (
            <div className="management-grid">
              {therapists.map((therapist) => (
                <div key={therapist.id} className="screen-card entity-card">
                  <div className="entity-card__header">
                    <h3 className="entity-card__title">{therapist.first_name} {therapist.last_name}</h3>
                    <div className="item-heading-row">
                      <span className={`status-pill ${therapist.is_active ? 'dashboard-status-pill--active' : 'dashboard-status-pill--pending'}`}>
                        {therapist.is_active ? 'Actiu' : 'Pendent'}
                      </span>
                      {therapist.is_clinic_admin ? (
                        <span className="status-pill dashboard-status-pill--active">Admin</span>
                      ) : null}
                    </div>
                  </div>
                  <div className="entity-card__body">
                    <p className="entity-card__meta">
                      <strong>Especialitat:</strong> {therapist.specialty}
                    </p>
                    <p className="entity-card__meta">
                      <strong>Col·legiat:</strong> {therapist.license_number}
                    </p>
                    <p className="entity-card__meta">
                      <strong>Email:</strong> {therapist.email}
                    </p>
                  </div>
                  <div className="entity-card__footer">
                    <span className="tiny muted">Alta: {new Date(therapist.registration_date).toLocaleDateString()}</span>
                    <div className="button-row entity-actions">
                      <button className="button-ghost button--icon action-chip--icon" type="button" onClick={() => openEditView(therapist)} title="Editar" aria-label="Editar">
                        <FaEdit />
                      </button>
                      <button className="button-danger button--icon action-chip--icon" type="button" onClick={() => handleDelete(therapist)} title="Eliminar" aria-label="Eliminar">
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {therapists.length === 0 ? (
                <div className="screen-card dashboard-panel profile-card--wide" style={{ textAlign: 'center', padding: '4rem' }}>
                  <p className="muted">Encara no hi ha cap terapeuta registrat a la teva clínica.</p>
                </div>
              ) : null}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
