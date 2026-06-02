import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { consentDocumentUrlForRole } from '../lib/api.js'

function extractErrorMessage(error) {
  if (error?.detail) {
    return Array.isArray(error.detail) ? error.detail.join(' ') : String(error.detail)
  }

  return 'No hem pogut registrar la teva decisió sobre el consentiment.'
}

const consentCopyByRole = {
  patient: {
    eyebrow: 'Consentiment informat',
    title: 'Abans d’entrar, necessitem la teva decisió explícita.',
    lead: 'Llegeix el document de consentiment informat i decideix si vols continuar amb l’eina.',
    panelEyebrow: 'Primer accés del pacient',
    panelTitle: 'Has d’acceptar o rebutjar el consentiment',
    checkbox:
      'He llegit la informació i accepto explícitament el tractament de les meves dades en els termes descrits.',
    rejectMessage: 'Has rebutjat el consentiment informat. El compte ha quedat inactiu.',
    details: [
      ['Finalitat del tractament', 'anàlisi emocional amb IA per donar suport al seguiment terapèutic.'],
      ['Qui tindrà accés', 'el teu terapeuta assignat i, en cas d’alerta, terapeutes de suport autoritzats.'],
      ['Període de conservació', 'mínim 5 anys per obligació legal.'],
      ['Drets', 'accés, rectificació i la resta de drets de la normativa aplicable.'],
      ['Important', 'Reflexia no diagnostica ni substitueix el criteri clínic professional.'],
    ],
  },
  therapist: {
    eyebrow: 'Consentiment professional',
    title: 'Abans d’entrar, cal acceptar les condicions professionals.',
    lead: 'Llegeix el document de consentiment professional, confidencialitat i protecció de dades.',
    panelEyebrow: 'Primer accés del terapeuta',
    panelTitle: 'Has d’acceptar o rebutjar les condicions professionals',
    checkbox:
      'He llegit la informació i accepto la confidencialitat, l’accés mínim necessari i les obligacions de protecció de dades.',
    rejectMessage: 'Has rebutjat les condicions professionals. El compte ha quedat inactiu.',
    details: [
      ['Finalitat del tractament', 'seguiment terapèutic i gestió de pacients assignats.'],
      ['Accés permès', 'només pacients assignats i informació necessària per a la intervenció professional.'],
      ['Confidencialitat', 'obligació de protegir les dades de salut i evitar accessos indeguts.'],
      ['Normativa aplicable', 'RGPD, LOPDGDD i normativa sanitària vinculada a dades de salut.'],
      ['Important', 'l’ús de Reflexia no substitueix el criteri clínic ni les obligacions professionals pròpies.'],
    ],
  },
}

export function ConsentPage() {
  const { user, acceptConsent, rejectConsent } = useAuth()
  const navigate = useNavigate()
  const [accepted, setAccepted] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.legal_terms_accepted === true) {
    return <Navigate to="/dashboard" replace />
  }

  const copy = consentCopyByRole[user.role] || consentCopyByRole.patient

  async function handleAccept() {
    if (!accepted) {
      setError('Has de marcar la casella per acceptar el document legal.')
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
          message: copy.rejectMessage,
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
            <p className="eyebrow">{copy.eyebrow}</p>
            <h1>{copy.title}</h1>
            <p className="hero-lead">{copy.lead}</p>
          </div>
          <div className="hero-footer">
            <a className="text-link" href={consentDocumentUrlForRole(user.role)} target="_blank" rel="noreferrer">
              Descarregar el PDF
            </a>
          </div>
        </aside>

        <section className="screen-card form-panel">
          <div className="panel-heading">
            <p className="eyebrow">{copy.panelEyebrow}</p>
            <h2>{copy.panelTitle}</h2>
          </div>

          {error ? <div className="error-banner" style={{ marginBottom: '1rem' }}>{error}</div> : null}

          <div className="content-card section-stack">
            <h3>Informació essencial</h3>
            <div className="info-list muted">
              {copy.details.map(([label, description]) => (
                <p key={label}><strong>{label}:</strong> {description}</p>
              ))}
            </div>
          </div>

          <label className="checkbox-row">
            <input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} />
            <span>{copy.checkbox}</span>
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
