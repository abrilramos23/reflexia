import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function extractErrorMessage(error) {
  if (typeof error === 'string') {
    return error
  }

  if (error?.code) {
    return Array.isArray(error.code) ? error.code.join(' ') : String(error.code)
  }

  if (error?.detail) {
    return Array.isArray(error.detail) ? error.detail.join(' ') : String(error.detail)
  }

  return 'No hem pogut verificar el codi 2FA.'
}

export function TwoFactorPage() {
  const { pendingTwoFactor, verifyTwoFactor } = useAuth()
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!pendingTwoFactor) {
    return <Navigate to="/login" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const result = await verifyTwoFactor(code)

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
      <div className="screen-grid">
        <aside className="screen-card hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">Segon factor</p>
            <h1>Verifica que ets tu.</h1>
            <p className="hero-lead">
              Introdueix el codi temporal de l’aplicació autenticadora per completar l’accés al teu compte.
            </p>
          </div>
        </aside>

        <section className="screen-card form-panel">
          <div className="panel-heading">
            <p className="eyebrow">2FA</p>
            <h2>Codi de verificació</h2>
            <p className="muted">Compte: {pendingTwoFactor.email}</p>
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          <form className="form-stack" onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="code">Codi de 6 dígits</label>
              <input
                id="code"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(event) => setCode(event.target.value)}
                placeholder="123456"
                required
              />
            </div>

            <div className="button-row">
              <button className="button-secondary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Verificant...' : 'Validar 2FA'}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}
