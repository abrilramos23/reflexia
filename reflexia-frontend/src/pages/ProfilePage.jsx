import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import QRCode from 'qrcode'
import { useAuth } from '../context/AuthContext.jsx'
import { consentDocumentUrl } from '../lib/api.js'

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

function sortContacts(contacts) {
  return [...contacts].sort((left, right) => {
    if (left.is_default !== right.is_default) {
      return left.is_default ? -1 : 1
    }

    return left.name.localeCompare(right.name)
  })
}

export function ProfilePage() {
  const {
    user,
    updateProfile,
    changePassword,
    listAssociatedContacts,
    createAssociatedContact,
    updateAssociatedContact,
    deleteAssociatedContact,
    listSupportTherapists,
    listAvailableSupportTherapists,
    createSupportTherapist,
    deleteSupportTherapist,
    setupTwoFactor,
    enableTwoFactor,
    disableTwoFactor,
    deleteAccount,
    deactivatePatient,
    logout,
  } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState(user?.email || '')
  const [specialty, setSpecialty] = useState(user?.role === 'therapist' ? (user.specialty || '') : '')
  const [profileMessage, setProfileMessage] = useState('')
  const [profileError, setProfileError] = useState('')
  const [isProfileSectionOpen, setIsProfileSectionOpen] = useState(false)
  const [passwordState, setPasswordState] = useState({
    current_password: '',
    new_password: '',
    new_password_confirm: '',
  })
  const [passwordMessage, setPasswordMessage] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [isPasswordSectionOpen, setIsPasswordSectionOpen] = useState(false)
  const [twoFactorSetup, setTwoFactorSetup] = useState(null)
  const [twoFactorQr, setTwoFactorQr] = useState('')
  const [twoFactorCode, setTwoFactorCode] = useState('')
  const [twoFactorDisableState, setTwoFactorDisableState] = useState({ password: '', code: '' })
  const [twoFactorMessage, setTwoFactorMessage] = useState('')
  const [twoFactorError, setTwoFactorError] = useState('')
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [assignedPatients, setAssignedPatients] = useState([])
  const [deleteMessage, setDeleteMessage] = useState('')
  const [busyPatientId, setBusyPatientId] = useState('')
  const [associatedContacts, setAssociatedContacts] = useState([])
  const [contactForm, setContactForm] = useState({
    name: '',
    relation: '',
    email: '',
    phone: '',
    is_default: false,
  })
  const [showContactForm, setShowContactForm] = useState(false)
  const [editingContactId, setEditingContactId] = useState('')
  const [contactMessage, setContactMessage] = useState('')
  const [contactError, setContactError] = useState('')
  const [supportTherapists, setSupportTherapists] = useState([])
  const [availableSupportTherapists, setAvailableSupportTherapists] = useState([])
  const [selectedSupportId, setSelectedSupportId] = useState('')
  const [showSupportForm, setShowSupportForm] = useState(false)
  const [supportMessage, setSupportMessage] = useState('')
  const [supportError, setSupportError] = useState('')

  if (!user) {
    return <Navigate to="/login" replace />
  }

  useEffect(() => {
    let isCancelled = false

    async function generateQrCode() {
      if (!twoFactorSetup?.otpauth_url) {
        setTwoFactorQr('')
        return
      }

      try {
        const qrDataUrl = await QRCode.toDataURL(twoFactorSetup.otpauth_url, {
          margin: 1,
          width: 220,
          color: {
            dark: '#1f342f',
            light: '#f6fbf7',
          },
        })

        if (!isCancelled) {
          setTwoFactorQr(qrDataUrl)
        }
      } catch {
        if (!isCancelled) {
          setTwoFactorQr('')
        }
      }
    }

    generateQrCode()

    return () => {
      isCancelled = true
    }
  }, [twoFactorSetup])

  useEffect(() => {
    setEmail(user?.email || '')
    setSpecialty(user?.role === 'therapist' ? (user.specialty || '') : '')
  }, [user?.email, user?.role, user?.specialty])

  useEffect(() => {
    let isCancelled = false

    async function loadRoleData() {
      try {
        if (user.role === 'patient') {
          const contacts = await listAssociatedContacts()
          if (!isCancelled) {
            setAssociatedContacts(sortContacts(contacts))
          }
        }

        if (user.role === 'therapist') {
          const [currentSupportTherapists, availableTherapists] = await Promise.all([
            listSupportTherapists(),
            listAvailableSupportTherapists(),
          ])

          if (!isCancelled) {
            setSupportTherapists(currentSupportTherapists)
            setAvailableSupportTherapists(availableTherapists)
          }
        }
      } catch {
        if (!isCancelled) {
          setContactError(user.role === 'patient' ? 'No s’han pogut carregar els contactes associats.' : '')
          setSupportError(user.role === 'therapist' ? 'No s’han pogut carregar els terapeutes de suport.' : '')
        }
      }
    }

    loadRoleData()

    return () => {
      isCancelled = true
    }
  }, [user.role])

  function resetContactForm() {
    setContactForm({
      name: '',
      relation: '',
      email: '',
      phone: '',
      is_default: false,
    })
    setEditingContactId('')
    setShowContactForm(false)
  }

  async function handleProfileSubmit(event) {
    event.preventDefault()
    setProfileError('')
    setProfileMessage('')

    try {
      const payload = { email }

      if (user.role === 'therapist' && specialty) {
        payload.specialty = specialty
      }

      const response = await updateProfile(payload)
      setEmail(response.user.email)
      if (typeof response.user.specialty === 'string') {
        setSpecialty(response.user.specialty)
      }
      setProfileMessage(response.message)
    } catch (error) {
      setProfileError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handlePasswordSubmit(event) {
    event.preventDefault()
    setPasswordError('')
    setPasswordMessage('')

    try {
      const response = await changePassword(passwordState)
      setPasswordMessage(response.message)
      setPasswordState({
        current_password: '',
        new_password: '',
        new_password_confirm: '',
      })
    } catch (error) {
      setPasswordError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleTwoFactorSetup() {
    setTwoFactorError('')
    setTwoFactorMessage('')

    try {
      const response = await setupTwoFactor()
      setTwoFactorSetup(response)
      setTwoFactorMessage('Configuració generada. Copia el secret o obre l’enllaç a l’aplicació autenticadora.')
    } catch (error) {
      setTwoFactorError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleTwoFactorEnable(event) {
    event.preventDefault()
    setTwoFactorError('')
    setTwoFactorMessage('')

    try {
      const response = await enableTwoFactor(twoFactorCode)
      setTwoFactorMessage(response.message)
      setTwoFactorSetup(null)
      setTwoFactorQr('')
      setTwoFactorCode('')
    } catch (error) {
      setTwoFactorError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleTwoFactorDisable(event) {
    event.preventDefault()
    setTwoFactorError('')
    setTwoFactorMessage('')

    try {
      const response = await disableTwoFactor(twoFactorDisableState)
      setTwoFactorMessage(response.message)
      setTwoFactorDisableState({ password: '', code: '' })
    } catch (error) {
      setTwoFactorError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleDeleteAccount(event) {
    event.preventDefault()
    setDeleteError('')
    setDeleteMessage('')

    try {
      await deleteAccount(deletePassword)
      navigate('/login', {
        replace: true,
        state: { message: 'Compte eliminat correctament.' },
      })
    } catch (error) {
      const normalizedError = error.response?.data || error
      if (normalizedError?.patients) {
        setAssignedPatients(normalizedError.patients)
      }
      setDeleteError(firstErrorMessage(normalizedError))
    }
  }

  async function handleContactSubmit(event) {
    event.preventDefault()
    setContactError('')
    setContactMessage('')

    try {
      const payload = {
        name: contactForm.name,
        relation: contactForm.relation,
        email: contactForm.email || null,
        phone: contactForm.phone || null,
        is_default: contactForm.is_default,
      }

      if (editingContactId) {
        const updatedContact = await updateAssociatedContact(editingContactId, payload)
        setAssociatedContacts((currentContacts) =>
          sortContacts(
            currentContacts.map((contact) =>
              contact.id === editingContactId ? updatedContact : contact,
            ),
          ),
        )
        setContactMessage('Contacte actualitzat correctament.')
      } else {
        const createdContact = await createAssociatedContact(payload)
        setAssociatedContacts((currentContacts) => sortContacts([...currentContacts, createdContact]))
        setContactMessage('Contacte afegit correctament.')
      }

      resetContactForm()
    } catch (error) {
      setContactError(firstErrorMessage(error.response?.data || error))
    }
  }

  function handleEditContact(contact) {
    setShowContactForm(true)
    setEditingContactId(contact.id)
    setContactForm({
      name: contact.name,
      relation: contact.relation,
      email: contact.email || '',
      phone: contact.phone || '',
      is_default: Boolean(contact.is_default),
    })
    setContactMessage('')
    setContactError('')
  }

  async function handleDeleteContact(contact) {
    const confirmed = window.confirm(`Vols eliminar el contacte ${contact.name}?`)

    if (!confirmed) {
      return
    }

    setContactError('')
    setContactMessage('')

    try {
      await deleteAssociatedContact(contact.id)
      setAssociatedContacts((currentContacts) =>
        currentContacts.filter((currentContact) => currentContact.id !== contact.id),
      )

      if (editingContactId === contact.id) {
        resetContactForm()
      }

      setContactMessage('Contacte eliminat correctament.')
    } catch (error) {
      setContactError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleToggleDefaultContact(contact) {
    setContactError('')
    setContactMessage('')

    try {
      const updatedContact = await updateAssociatedContact(contact.id, {
        is_default: !contact.is_default,
      })

      setAssociatedContacts((currentContacts) =>
        sortContacts(
          currentContacts.map((currentContact) =>
            currentContact.id === contact.id ? updatedContact : currentContact,
          ),
        ),
      )
      setContactMessage('Contacte actualitzat correctament.')
    } catch (error) {
      setContactError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleSupportTherapistSubmit(event) {
    event.preventDefault()
    setSupportError('')
    setSupportMessage('')

    try {
      const createdSupportTherapist = await createSupportTherapist({
        support_id: selectedSupportId,
      })

      setSupportTherapists((currentTherapists) => [...currentTherapists, createdSupportTherapist])
      setAvailableSupportTherapists((currentTherapists) =>
        currentTherapists.filter((therapist) => therapist.id !== selectedSupportId),
      )
      setSelectedSupportId('')
      setShowSupportForm(false)
      setSupportMessage('Terapeuta de suport afegit correctament.')
    } catch (error) {
      setSupportError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleDeleteSupportTherapist(supportTherapist) {
    const confirmed = window.confirm(
      `Vols eliminar ${supportTherapist.first_name} ${supportTherapist.last_name} com a terapeuta de suport?`,
    )

    if (!confirmed) {
      return
    }

    setSupportError('')
    setSupportMessage('')

    try {
      await deleteSupportTherapist(supportTherapist.support_id)
      setSupportTherapists((currentTherapists) =>
        currentTherapists.filter(
          (currentTherapist) => currentTherapist.support_id !== supportTherapist.support_id,
        ),
      )
      setAvailableSupportTherapists((currentTherapists) =>
        [...currentTherapists, {
          id: supportTherapist.support_id,
          first_name: supportTherapist.first_name,
          last_name: supportTherapist.last_name,
          email: supportTherapist.email,
          license_number: supportTherapist.license_number,
          specialty: supportTherapist.specialty,
        }].sort((left, right) =>
          `${left.first_name} ${left.last_name}`.localeCompare(`${right.first_name} ${right.last_name}`),
        ),
      )
      setSupportMessage('Terapeuta de suport eliminat correctament.')
    } catch (error) {
      setSupportError(firstErrorMessage(error.response?.data || error))
    }
  }

  async function handleDeactivatePatient(patientId) {
    setDeleteError('')
    setDeleteMessage('')
    setBusyPatientId(patientId)

    try {
      await deactivatePatient(patientId)
      setAssignedPatients((currentPatients) =>
        currentPatients.filter((patient) => patient.id !== patientId),
      )
      setDeleteMessage('Pacient donat de baixa correctament. Ja pots tornar a provar l’eliminació del compte.')
    } catch (error) {
      setDeleteError(firstErrorMessage(error.response?.data || error))
    } finally {
      setBusyPatientId('')
    }
  }

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true, state: { message: 'Sessió tancada correctament.' } })
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card profile-card">
          <button
            className="section-toggle"
            type="button"
            onClick={() => setIsProfileSectionOpen((currentState) => !currentState)}
          >
            <div className="panel-heading">
              <p className="eyebrow">Dades personals</p>
              <h3>Editar perfil</h3>
            </div>
            <span className={`section-toggle-indicator ${isProfileSectionOpen ? 'section-toggle-indicator--open' : ''}`}>
              <span aria-hidden="true">▾</span>
            </span>
          </button>

          {isProfileSectionOpen ? (
            <>
              {profileMessage ? <div className="message">{profileMessage}</div> : null}
              {profileError ? <div className="error-banner">{profileError}</div> : null}

              <form className="form-stack collapsible-section-body" onSubmit={handleProfileSubmit}>
                <div className="field-group">
                  <label htmlFor="profile-name">Nom</label>
                  <input className="input-disabled" id="profile-name" type="text" value={user.first_name} disabled />
                  <label htmlFor="profile-last-name">Cognoms</label>
                  <input className="input-disabled" id="profile-last-name" type="text" value={user.last_name} disabled />
                  <label htmlFor="profile-email">Correu electrònic</label>
                  <input id="profile-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
                  <label htmlFor="profile-status">Estat</label>
                  <input className="input-disabled" id="profile-status" type="text" value={user.is_active ? 'Actiu' : 'Inactiu'} disabled />
                </div>

                {user.role === 'therapist' ? (
                  <div className="field-group">
                    <label htmlFor="profile-specialty">Especialitat</label>
                    <input
                      id="profile-specialty"
                      type="text"
                      value={specialty}
                      onChange={(event) => setSpecialty(event.target.value)}
                      placeholder="Trauma Therapy"
                    />
                  </div>
                ) : null}

                <div className="button-row">
                  <button className="button" type="submit">Guardar canvis</button>
                </div>
              </form>
            </>
          ) : null}
        </section>

        <section className="screen-card profile-card">
          <button
            className="section-toggle"
            type="button"
            onClick={() => setIsPasswordSectionOpen((currentState) => !currentState)}
          >
            <div className="panel-heading">
              <p className="eyebrow">Contrasenya</p>
              <h3>Canviar contrasenya</h3>
            </div>
            <span className={`section-toggle-indicator ${isPasswordSectionOpen ? 'section-toggle-indicator--open' : ''}`}>
              <span aria-hidden="true">▾</span>
            </span>
          </button>

          {isPasswordSectionOpen ? (
            <>
              {passwordMessage ? <div className="message">{passwordMessage}</div> : null}
              {passwordError ? <div className="error-banner">{passwordError}</div> : null}

              <form className="form-stack collapsible-section-body" onSubmit={handlePasswordSubmit}>
                <div className="field-group">
                  <label htmlFor="current-password">Contrasenya actual</label>
                  <input
                    id="current-password"
                    type="password"
                    value={passwordState.current_password}
                    onChange={(event) =>
                      setPasswordState((currentState) => ({
                        ...currentState,
                        current_password: event.target.value,
                      }))
                    }
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="new-password">Nova contrasenya</label>
                  <input
                    id="new-password"
                    type="password"
                    value={passwordState.new_password}
                    onChange={(event) =>
                      setPasswordState((currentState) => ({
                        ...currentState,
                        new_password: event.target.value,
                      }))
                    }
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="new-password-confirm">Confirmar nova contrasenya</label>
                  <input
                    id="new-password-confirm"
                    type="password"
                    value={passwordState.new_password_confirm}
                    onChange={(event) =>
                      setPasswordState((currentState) => ({
                        ...currentState,
                        new_password_confirm: event.target.value,
                      }))
                    }
                  />
                </div>

                <div className="button-row">
                  <button className="button-secondary" type="submit">Actualitzar contrasenya</button>
                </div>
              </form>
            </>
          ) : null}
        </section>

        {user.role === 'patient' ? (
          <section className="screen-card profile-card profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Contactes associats</p>
              {contactMessage ? <div className="message" style={{ marginBottom: '1rem' }}>{contactMessage}</div> : null}
              {contactError ? <div className="error-banner" style={{ marginBottom: '1rem' }}>{contactError}</div> : null}
              <h3>Gestionar persones de confiança</h3>
            </div>

            {!showContactForm ? (
              <div className="section-toolbar">
                <button
                  className="button"
                  type="button"
                  onClick={() => {
                    setShowContactForm(true)
                    setEditingContactId('')
                  }}
                >
                  Afegir contacte
                </button>
              </div>
            ) : null}

            {showContactForm ? (
              <form className="form-stack collapsible-form-card" onSubmit={handleContactSubmit}>
                <div className="inline-fields">
                  <div className="field-group">
                    <label htmlFor="contact-name">Nom</label>
                    <input
                      id="contact-name"
                      type="text"
                      value={contactForm.name}
                      onChange={(event) =>
                        setContactForm((currentForm) => ({
                          ...currentForm,
                          name: event.target.value,
                        }))
                      }
                    />
                  </div>

                  <div className="field-group">
                    <label htmlFor="contact-relation">Relació</label>
                    <input
                      id="contact-relation"
                      type="text"
                      value={contactForm.relation}
                      onChange={(event) =>
                        setContactForm((currentForm) => ({
                          ...currentForm,
                          relation: event.target.value,
                        }))
                      }
                    />
                  </div>
                </div>

                <div className="inline-fields">
                  <div className="field-group">
                    <label htmlFor="contact-email">Correu electrònic</label>
                    <input
                      id="contact-email"
                      type="email"
                      value={contactForm.email}
                      onChange={(event) =>
                        setContactForm((currentForm) => ({
                          ...currentForm,
                          email: event.target.value,
                        }))
                      }
                    />
                  </div>

                  <div className="field-group">
                    <label htmlFor="contact-phone">Telèfon</label>
                    <input
                      id="contact-phone"
                      type="text"
                      value={contactForm.phone}
                      onChange={(event) =>
                        setContactForm((currentForm) => ({
                          ...currentForm,
                          phone: event.target.value,
                        }))
                      }
                    />
                  </div>
                </div>

                <div className="button-row">
                  <button className="button" type="submit">
                    {editingContactId ? 'Guardar contacte' : 'Crear contacte'}
                  </button>
                  <button className="button-ghost" type="button" onClick={resetContactForm}>
                    Cancel·lar
                  </button>
                </div>
              </form>
            ) : null}

            <div className="content-card section-stack" style={{ marginTop: '2rem' }}>
              <h3>Llista de contactes</h3>

              {associatedContacts.length === 0 ? (
                <p className="muted">Encara no tens contactes associats registrats.</p>
              ) : (
                <ul className="patient-list">
                  {associatedContacts.map((contact) => (
                    <li className="patient-item compact-list-item" key={contact.id}>
                      <div>
                        <div className="item-heading-row">
                          <strong>{contact.name}</strong>
                          {contact.is_default ? (
                            <span className="status-pill">Contacte per defecte</span>
                          ) : null}
                        </div>
                        <p className="muted">{contact.relation}</p>
                        <p className="muted">
                          {[contact.email, contact.phone].filter(Boolean).join(' · ')}
                        </p>
                      </div>

                      <div className="list-actions">
                        <button className="action-chip" type="button" onClick={() => handleEditContact(contact)}>
                          Editar
                        </button>
                        <button className="action-chip action-chip--accent" type="button" onClick={() => handleToggleDefaultContact(contact)}>
                          {contact.is_default ? 'Treure per defecte' : 'Marcar per defecte'}
                        </button>
                        <button className="action-chip action-chip--danger" type="button" onClick={() => handleDeleteContact(contact)}>
                          Eliminar
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        ) : null}

        {user.role === 'therapist' ? (
          <section className="screen-card profile-card profile-card--wide">
            <div className="panel-heading">
              <p className="eyebrow">Terapeutes de suport</p>
              {supportMessage ? <div className="message" style={{ marginBottom: '1rem' }}>{supportMessage}</div> : null}
              {supportError ? <div className="error-banner" style={{ marginBottom: '1rem' }}>{supportError}</div> : null}
              <h3>Gestionar cobertura d’alertes</h3>
            </div>

            {!showSupportForm ? (
              <div className="section-toolbar">
                <button
                  className="button"
                  type="button"
                  onClick={() => {
                    setShowSupportForm(true)
                  }}
                >
                  Afegir terapeuta de suport
                </button>
              </div>
            ) : null}

            {showSupportForm ? (
              <form className="form-stack collapsible-form-card" onSubmit={handleSupportTherapistSubmit}>
                <div className="field-group">
                  <label htmlFor="support-therapist">Selecciona un terapeuta</label>
                  <select
                    id="support-therapist"
                    value={selectedSupportId}
                    onChange={(event) => setSelectedSupportId(event.target.value)}
                  >
                    <option value="">Selecciona un terapeuta del sistema</option>
                    {availableSupportTherapists.map((therapist) => (
                      <option key={therapist.id} value={therapist.id}>
                        {therapist.first_name} {therapist.last_name} · {therapist.specialty}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="button-row">
                  <button className="button" type="submit" disabled={!selectedSupportId}>
                    Afegir terapeuta
                  </button>
                  <button
                    className="button-ghost"
                    type="button"
                    onClick={() => {
                      setShowSupportForm(false)
                      setSelectedSupportId('')
                    }}
                  >
                    Cancel·lar
                  </button>
                </div>
              </form>
            ) : null}

            <div className="content-card section-stack">
              <h3>Llista actual</h3>

              {supportTherapists.length === 0 ? (
                <p className="muted">Encara no tens terapeutes de suport assignats.</p>
              ) : (
                <ul className="patient-list">
                  {supportTherapists.map((supportTherapist) => (
                    <li className="patient-item compact-list-item" key={supportTherapist.support_id}>
                      <div>
                        <div className="item-heading-row">
                          <strong>
                            {supportTherapist.first_name} {supportTherapist.last_name}
                          </strong>
                          <span className="status-pill">Suport actiu</span>
                        </div>
                        <p className="muted">{supportTherapist.specialty}</p>
                        <p className="muted">{supportTherapist.email}</p>
                      </div>

                      <div className="list-actions">
                        <button
                          className="action-chip action-chip--danger"
                          type="button"
                          onClick={() => handleDeleteSupportTherapist(supportTherapist)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        ) : null}

        <section className="screen-card profile-card">
          <div className="panel-heading">
            <p className="eyebrow">Doble factor</p>
            <h3>Configurar 2FA</h3>
          </div>

          {twoFactorMessage ? <div className="message">{twoFactorMessage}</div> : null}
          {twoFactorError ? <div className="error-banner">{twoFactorError}</div> : null}

          {!user.two_factor_enabled ? (
            <>
              <div className="button-row" style={{padding: '20px 0'}}>
                <button className="button-secondary" type="button" onClick={handleTwoFactorSetup}>
                  Generar configuració 2FA
                </button>
              </div>

              {twoFactorSetup ? (
                <form className="form-stack" onSubmit={handleTwoFactorEnable}>
                  <div className="content-card section-stack">
                    {twoFactorQr ? (
                      <div className="qr-card">
                        <img className="qr-image" src={twoFactorQr} alt="QR per configurar el 2FA" />
                      </div>
                    ) : null}
                    <p><strong>Secret TOTP:</strong> {twoFactorSetup.secret}</p>
                    <p className="qr-link">
                      <strong>Enllaç otpauth:</strong> {twoFactorSetup.otpauth_url}
                    </p>
                  </div>

                  <div className="field-group">
                    <label htmlFor="enable-2fa-code">Codi de verificació</label>
                    <input
                      id="enable-2fa-code"
                      value={twoFactorCode}
                      onChange={(event) => setTwoFactorCode(event.target.value)}
                      placeholder="123456"
                    />
                  </div>

                  <div className="button-row">
                    <button className="button" type="submit">Activar 2FA</button>
                  </div>
                </form>
              ) : null}
            </>
          ) : (
            <form className="form-stack" onSubmit={handleTwoFactorDisable}>
              <p className="muted">El doble factor està activat. Introdueix la contrasenya i un codi vàlid per desactivar-lo.</p>

              <div className="field-group">
                <label htmlFor="disable-2fa-password">Contrasenya</label>
                <input
                  id="disable-2fa-password"
                  type="password"
                  value={twoFactorDisableState.password}
                  onChange={(event) =>
                    setTwoFactorDisableState((currentState) => ({
                      ...currentState,
                      password: event.target.value,
                    }))
                  }
                />
              </div>

              <div className="field-group">
                <label htmlFor="disable-2fa-code">Codi actual</label>
                <input
                  id="disable-2fa-code"
                  value={twoFactorDisableState.code}
                  onChange={(event) =>
                    setTwoFactorDisableState((currentState) => ({
                      ...currentState,
                      code: event.target.value,
                    }))
                  }
                />
              </div>

              <div className="button-row">
                <button className="button-ghost" type="submit">Desactivar 2FA</button>
              </div>
            </form>
          )}
        </section>

        <section className="screen-card dashboard-panel" style={{ height: 'fit-content' }}>
          <div className="panel-heading">
            <p className="eyebrow">Accions ràpides</p>
            <h2>Seguretat i legal</h2>
          </div>

          <div className="button-row">
            <a style={{ textDecoration: 'none' }} className="button-ghost" href={consentDocumentUrl} target="_blank" rel="noreferrer">
              Veure consentiment PDF
            </a>
          </div>
        </section>

        <section className="screen-card profile-card">
          <div className="panel-heading">
            <p className="eyebrow">Sessió</p>
            <h3>Tancar sessió</h3>
          </div>

          <div className="content-card section-stack" style={{ textDecoration: 'none', backgroundColor: 'transparent', border: 'none', padding: '0',  }}>
            <p className="muted" style={{ textDecoration: 'none', backgroundColor: 'transparent', border: 'none' }}>
              Si estàs en un ordinador compartit o simplement vols acabar l’activitat, pots tancar la sessió des d’aquí.
              El sistema invalidarà el token actiu i et retornarà a la pantalla d’inici de sessió.
            </p>
          </div>

          <div className="button-row" style={{paddingTop: '10px'}}>
            <button className="button-ghost" type="button" onClick={handleLogout}>
              Tancar sessió
            </button>
          </div>
        </section>

        <section className="screen-card profile-card">
          <div className="panel-heading">
            <p className="eyebrow">Eliminar perfil</p>
            <h3>Tancar compte</h3>
          </div>

          {deleteMessage ? <div className="message">{deleteMessage}</div> : null}
          {deleteError ? <div className="error-banner">{deleteError}</div> : null}

          <div className="content-card section-stack" style={{ textDecoration: 'none', backgroundColor: 'transparent', border: 'none', padding: '0',  }}>
            <p className="muted" style={{ textDecoration: 'none', backgroundColor: 'transparent', border: 'none', paddingBottom: '10px' }}>
              Les dades no clíniques s’eliminaran immediatament. Les dades clíniques es conservaran internament durant
              el període legal mínim i ja no seran accessibles un cop el compte quedi tancat.
            </p>
          </div>

          {assignedPatients.length > 0 ? (
            <div className="content-card section-stack">
              <h3>Pacients actius assignats</h3>
              <ul className="patient-list">
                {assignedPatients.map((patient) => (
                  <li className="patient-item" key={patient.id}>
                    <div>
                      <div className="item-heading-row">
                        <strong>{patient.first_name} {patient.last_name}</strong>
                        <span className="status-pill">Pacient assignat</span>
                      </div>
                      <p className="muted">{patient.email}</p>
                    </div>
                    <button
                      className="button-danger"
                      type="button"
                      disabled={busyPatientId === patient.id}
                      onClick={() => handleDeactivatePatient(patient.id)}
                    >
                      {busyPatientId === patient.id ? 'Donant de baixa...' : 'Donar de baixa'}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <form className="form-stack" onSubmit={handleDeleteAccount}>
            <div className="field-group">
              <label htmlFor="delete-password">Confirma la teva contrasenya</label>
              <input
                id="delete-password"
                type="password"
                value={deletePassword}
                onChange={(event) => setDeletePassword(event.target.value)}
              />
            </div>

            <div className="button-row">
              <button className="button-danger" type="submit">Eliminar compte</button>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}
