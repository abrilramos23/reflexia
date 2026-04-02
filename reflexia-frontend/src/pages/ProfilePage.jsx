import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import QRCode from 'qrcode'
import { AppHeader } from '../components/AppHeader.jsx'
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

export function ProfilePage() {
  const {
    user,
    updateProfile,
    changePassword,
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
  const [passwordState, setPasswordState] = useState({
    current_password: '',
    new_password: '',
    new_password_confirm: '',
  })
  const [passwordMessage, setPasswordMessage] = useState('')
  const [passwordError, setPasswordError] = useState('')
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
      <AppHeader />

      <div className="profile-grid">
        <section className="screen-card profile-card">
          <div className="panel-heading">
            <p className="eyebrow">Dades personals</p>
            <h3>Editar perfil</h3>
          </div>

          {profileMessage ? <div className="message">{profileMessage}</div> : null}
          {profileError ? <div className="error-banner">{profileError}</div> : null}

          <form className="form-stack" onSubmit={handleProfileSubmit}>
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
        </section>

        <section className="screen-card profile-card">
          <div className="panel-heading">
            <p className="eyebrow">Contrasenya</p>
            <h3>Canviar contrasenya</h3>
          </div>

          {passwordMessage ? <div className="message">{passwordMessage}</div> : null}
          {passwordError ? <div className="error-banner">{passwordError}</div> : null}

          <form className="form-stack" onSubmit={handlePasswordSubmit}>
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
        </section>

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

        <section className="screen-card dashboard-panel">
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
                      <strong>{patient.first_name} {patient.last_name}</strong>
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
