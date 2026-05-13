import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader.jsx'
import { api } from '../lib/api.js'

function extractErrorMessage(error) {
  if (error?.password) {
    return Array.isArray(error.password) ? error.password.join(' ') : String(error.password)
  }

  if (error?.token) {
    return Array.isArray(error.token) ? error.token.join(' ') : String(error.token)
  }

  if (error?.uid) {
    return Array.isArray(error.uid) ? error.uid.join(' ') : String(error.uid)
  }

  return 'No hem pogut actualitzar la contrasenya.'
}

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const uid = searchParams.get('uid') || ''
  const token = searchParams.get('token') || ''

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)

    try {
      const response = await api.post('/auth/password/reset/', {
        uid,
        token,
        password,
        password_confirm: passwordConfirm,
      })

      setMessage(response.data.message)
      setTimeout(() => {
        navigate('/login', {
          replace: true,
          state: { message: 'Contrasenya actualitzada correctament. Ja pots iniciar sessió.' },
        })
      }, 1200)
    } catch (requestError) {
      setError(extractErrorMessage(requestError.response?.data || requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="screen-shell">
      <AppHeader />
      <div className="screen-grid">
        <aside className="screen-card hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">Nova contrasenya</p>
            <h1>Tria una contrasenya nova i segura.</h1>
            <p className="hero-lead">
              L’enllaç és temporal. Un cop guardada la nova contrasenya, hauràs de tornar a iniciar sessió.
            </p>
          </div>
        </aside>

        <section className="screen-card form-panel">
          <div className="panel-heading">
            <p className="eyebrow">Restablir contrasenya</p>
            <h2>Actualitzar accés</h2>
          </div>

          {message ? <div className="message">{message}</div> : null}
          {error ? <div className="error-banner">{error}</div> : null}

          <form className="form-stack" onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="password">Nova contrasenya</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="password-confirm">Confirmar contrasenya</label>
              <input
                id="password-confirm"
                type="password"
                value={passwordConfirm}
                onChange={(event) => setPasswordConfirm(event.target.value)}
                required
              />
            </div>

            <div className="button-row">
              <button className="button" type="submit" disabled={isSubmitting || !uid || !token}>
                {isSubmitting ? 'Guardant...' : 'Guardar contrasenya'}
              </button>
              <Link style={{ textDecoration: 'none' }} className="text-link" to="/login" icon="arrow-left">
              </Link>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}
