import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function extractErrorMessage(error) {
  if (typeof error === 'string') {
    return error
  }

  if (error?.detail) {
    return Array.isArray(error.detail) ? error.detail.join(' ') : String(error.detail)
  }

  return 'No hem pogut iniciar la sessió. Torna-ho a provar.'
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const successMessage = location.state?.message

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const result = await login(email, password)

      if (result.login_status === 'two_factor_required') {
        navigate('/2fa', { replace: true })
        return
      }

      if (result.login_status === 'consent_required') {
        navigate('/consent', { replace: true })
        return
      }

      navigate('/dashboard', { replace: true })
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
            <p className="eyebrow">Reflexia</p>
            <h1>Un únic accés per a terapeutes i pacients.</h1>
            <p className="hero-lead">Inicia sessió per continuar el seguiment terapèutic.</p>
          </div>
          <div className="hero-footer">
            <p className="muted">Si ets pacient, el teu terapeuta és qui t’ha creat el compte dins de la plataforma.</p>
          </div>
        </aside>

        <section className="screen-card form-panel">
          <div className="panel-heading">
            <p className="eyebrow">Iniciar sessió</p>
            <h2>Benvingut/da de nou</h2>
            <p className="muted">Accedeix amb el teu correu electrònic i la teva contrasenya.</p>
          </div>

          {successMessage ? <div className="message">{successMessage}</div> : null}
          {error ? <div className="error-banner">{error}</div> : null}

          <form className="form-stack" onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="email">Correu electrònic</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="nom@exemple.com"
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="password">Contrasenya</label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            <div className="button-row">
              <button className="button" type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Entrant...' : 'Entrar'}
              </button>
              <Link className="text-link" to="/forgot-password">
                He oblidat la contrasenya
              </Link>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}
