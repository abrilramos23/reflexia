import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { consentDocumentUrl } from '../lib/api.js'

function extractErrorMessage(error) {
  if (error?.detail) {
    return Array.isArray(error.detail) ? error.detail.join(' ') : String(error.detail)
  }

  return 'No hem pogut registrar la teva decisió sobre el consentiment.'
}

export function ConsentPage() {
  const { user, acceptConsent, rejectConsent } = useAuth()
  const navigate = useNavigate()
  const [accepted, setAccepted] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (user?.role !== 'patient') {
    return <Navigate to="/dashboard" replace />
  }

  if (user.consent_accepted === true) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleAccept() {
    if (!accepted) {
      setError('Has de marcar la casella per acceptar el consentiment informat.')
      return
    }

    setError('')
    setIsSubmitting(true)

    try {
      await acceptConsent()
      navigate('/dashboard', { replace: true })
    } catch (requestError) {
      setError(extractErrorMessage(requestError.response?.data || requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleReject() {
    setError('')
    setIsSubmitting(true)

    try {
      await rejectConsent()
      navigate('/login', {
        replace: true,
        state: {
          message: 'Has rebutjat el consentiment informat. El compte ha quedat inactiu.',
        },
      })
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
            <p className="eyebrow">Consentiment informat</p>
            <h1>Abans d’entrar, necessitem la teva decisió explícita.</h1>
            <p className="hero-lead">
              Llegeix l’abast del tractament de dades i decideix si vols
              continuar amb l’eina.
            </p>
          </div>
          <div className="hero-footer">
            <a className="text-link" href={consentDocumentUrl} target="_blank" rel="noreferrer">
              Descarregar el PDF de la política i el consentiment
            </a>
          </div>
        </aside>

        <section className="screen-card form-panel">
          <div className="panel-heading">
            <p className="eyebrow">Primer accés del pacient</p>
            <h2>Has d’acceptar o rebutjar el consentiment</h2>
          </div>

          {error ? <div className="error-banner" style={{ marginBottom: '1rem' }}>{error}</div> : null}

          <div className="content-card section-stack">
            <h3>Informació essencial</h3>
            <div className="info-list muted">
              <p><strong>Finalitat del tractament:</strong> anàlisi emocional amb IA per donar suport al seguiment terapèutic.</p>
              <p><strong>Qui tindrà accés:</strong> el teu terapeuta assignat i, en cas d’alerta, terapeutes de suport autoritzats.</p>
              <p><strong>Període de conservació:</strong> mínim 5 anys per obligació legal.</p>
              <p><strong>Drets:</strong> accés, rectificació, portabilitat i la resta de drets de la normativa aplicable.</p>
              <p><strong>Important:</strong> Reflexia no diagnostica ni substitueix el criteri clínic professional.</p>
            </div>
          </div>

          <label className="checkbox-row">
            <input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} />
            <span>He llegit la informació i accepto explícitament el tractament de les meves dades en els termes descrits.</span>
          </label>

          <div className="button-row">
            <button className="button" type="button" onClick={handleAccept} disabled={isSubmitting}>
              {isSubmitting ? 'Guardant...' : 'Acceptar i continuar'}
            </button>
            <button className="button-danger" type="button" onClick={handleReject} disabled={isSubmitting}>
              Rebutjar i tancar compte
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
