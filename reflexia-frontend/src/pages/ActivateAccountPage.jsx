import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
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

  return 'No hem pogut activar el compte.'
}

export function ActivateAccountPage() {
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
      await api.post('/auth/activate/patient/', {
        uid,
        token,
        password,
        password_confirm: passwordConfirm,
      })

      setMessage('Compte activat correctament. Ja pots iniciar sessió.')
      setTimeout(() => {
        navigate('/login', {
          replace: true,
          state: { message: 'Compte activat correctament. Ja pots iniciar sessió.' },
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
      <div className="screen-grid">
        <aside className="screen-card hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">Activació de pacient</p>
            <h1>Defineix la teva contrasenya inicial.</h1>
            <p className="hero-lead">
              Aquest pas activa el compte que t’ha creat el teu terapeuta i et permet entrar a Reflexia.
            </p>
          </div>
        </aside>

        <section className="screen-card form-panel">
          <div className="panel-heading">
            <p className="eyebrow">Primer accés</p>
            <h2>Activar compte</h2>
            <p className="muted">Escull una contrasenya segura per començar.</p>
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
                {isSubmitting ? 'Activant...' : 'Activar compte'}
              </button>
              <Link className="text-link" to="/login">
                Tornar al login
              </Link>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}
