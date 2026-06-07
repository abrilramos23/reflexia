import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader.jsx'
import { api } from '../lib/api.js'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)

    try {
      const response = await api.post('/users/password/forgot/', { email })
      setMessage(response.data.message)
    } catch {
      setError('No hem pogut tramitar la recuperació de contrasenya.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="screen-shell">
      <AppHeader />
      <div className="login-screen">
        <div className="auth-form-stack">
            <section className="screen-card form-panel">
              <div className="panel-heading">
                <p className="eyebrow">Recuperar contrasenya</p>
              </div>

              {message ? <div className="message">{message}</div> : null}
              {error ? <div className="error-banner">{error}</div> : null}

              <form className="form-stack" onSubmit={handleSubmit}>
                <div className="field-group">
                  <label htmlFor="email">Correu electrònic</label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                  <p className="form-hint">
                    T’enviarem un enllaç per restablir la teva contrasenya.
                  </p>
                </div>

                <div className="button-row">
                  <button className="button-secondary" type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Enviant...' : 'Enviar enllaç'}
                  </button>
                  <Link style={{ textDecoration: 'none' }} className="text-link" to="/login" icon="arrow-left">
                  </Link>
                </div>
              </form>
            </section>
        </div>
      </div>
    </div>
  )
}
