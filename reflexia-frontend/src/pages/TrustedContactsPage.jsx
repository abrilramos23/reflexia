import { useEffect, useState } from 'react'
import { FaEdit, FaTrash } from 'react-icons/fa'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function firstErrorMessage(error) {
  if (!error) return 'S’ha produït un error inesperat.'
  if (typeof error === 'string') return error
  const firstEntry = Object.values(error)[0]
  if (Array.isArray(firstEntry)) return String(firstEntry[0])
  if (typeof firstEntry === 'string') return firstEntry
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

export function TrustedContactsPage() {
  const {
    user,
    listAssociatedContacts,
    createAssociatedContact,
    updateAssociatedContact,
    deleteAssociatedContact,
  } = useAuth()

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

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'patient') {
    return <Navigate to="/dashboard" replace />
  }

  useEffect(() => {
    let isCancelled = false

    async function loadContacts() {
      try {
        const contacts = await listAssociatedContacts()
        if (!isCancelled) {
          setAssociatedContacts(sortContacts(contacts))
        }
      } catch {
        if (!isCancelled) {
          setContactError('No s’han pogut carregar els contactes associats.')
        }
      }
    }

    loadContacts()

    return () => {
      isCancelled = true
    }
  }, [listAssociatedContacts])

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

  async function handleContactSubmit(event) {
    event.preventDefault()
    setContactError('')
    setContactMessage('')

    try {
      const payload = {
        name: contactForm.name,
        relation: contactForm.relation,
        email: contactForm.email,
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

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Contactes associats</p>
            <h1 className="section-title">Persones de confiança</h1>
            <p className="muted">Contactes per a situacions de necessitat.</p>
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <button
            className="section-toggle"
            type="button"
            onClick={() => {
              if (showContactForm) {
                resetContactForm()
              } else {
                setShowContactForm(true)
                setEditingContactId('')
              }
            }}
          >
            <div className="panel-heading">
              <p className="eyebrow">{editingContactId ? 'Editar' : 'Nou contacte'}</p>
              <h2>{editingContactId ? 'Editar contacte' : 'Afegir contacte'}</h2>
            </div>
            <span
              className={`section-toggle-indicator ${showContactForm ? 'section-toggle-indicator--open' : ''}`}
            >
              <span aria-hidden="true">▾</span>
            </span>
          </button>

          {showContactForm ? (
            <div className="collapsible-section-body">
              {contactMessage ? <div className="message">{contactMessage}</div> : null}
              {contactError ? <div className="error-banner">{contactError}</div> : null}

              <form className="form-stack" onSubmit={handleContactSubmit}>
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
                      required
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
                      required
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
                      required
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

                <div className="button-row" style={{ marginBlockStart: '1rem' }}>
                  <button className="button-secondary" type="submit">
                    {editingContactId ? 'Guardar canvis' : 'Crear contacte'}
                  </button>
                  <button className="button-ghost" type="button" onClick={resetContactForm}>
                    Cancel·lar
                  </button>
                </div>
              </form>
            </div>
          ) : null}
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow" style={{ marginBottom: '0rem' }}>
              Llista de contactes
            </p>
          </div>

          {associatedContacts.length === 0 ? (
            <p className="muted">Encara no tens contactes associats registrats.</p>
          ) : (
            <ul className="patient-list">
              {associatedContacts.map((contact) => (
                <li
                  className="patient-item compact-list-item"
                  key={contact.id}
                  style={{ padding: 0, overflow: 'hidden' }}
                >
                  <div
                    style={{
                      display: 'flex',
                      padding: '14px 16px',
                      width: '100%',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div className="item-heading-row">
                        <strong>{contact.name}</strong>
                        {contact.is_default ? (
                          <span className="status-pill">Contacte per defecte</span>
                        ) : null}
                      </div>
                      <p className="muted" style={{ fontWeight: 'bold', margin: '0.5rem 0' }}>
                        {contact.relation}
                      </p>
                      <p className="muted" style={{ margin: 0 }}>
                        {[contact.email, contact.phone].filter(Boolean).join(' · ')}
                      </p>
                    </div>

                     <div className="list-actions" style={{ marginLeft: '1rem' }}>
                      <button className="action-chip" type="button" onClick={() => handleEditContact(contact)} title="Editar" aria-label="Editar">
                        <FaEdit />
                      </button>
                      <button className="action-chip action-chip--accent" type="button" onClick={() => handleToggleDefaultContact(contact)}>
                        {contact.is_default ? 'Treure per defecte' : 'Marcar per defecte'}
                      </button>
                      <button className="action-chip action-chip--danger" type="button" onClick={() => handleDeleteContact(contact)} title="Eliminar" aria-label="Eliminar">
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
