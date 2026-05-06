import { useEffect, useState } from 'react'
import { firstErrorMessage } from '../lib/entries.js'

const riskLabels = {
  none: 'Sense risc',
  low: 'Risc baix',
  moderate: 'Risc moderat',
  high: 'Risc alt',
}

export function EntryAnalysisPanel({
  analysis,
  canCorrect = false,
  isSavingCorrection = false,
  correctionError = '',
  correctionMessage = '',
  onSaveCorrection,
}) {
  const [correction, setCorrection] = useState(analysis?.therapist_correction || '')

  useEffect(() => {
    setCorrection(analysis?.therapist_correction || '')
  }, [analysis?.entry_id, analysis?.therapist_correction])

  if (!analysis) {
    return (
      <div className="content-card section-stack entries-analysis-card">
        <h3>Analisi emocional</h3>
        <p className="muted">
          L&apos;analisi encara no s&apos;ha generat. Quan estigui disponible, es mostraran les emocions detectades i el nivell de risc associat.
        </p>
      </div>
    )
  }

  async function handleSubmit(event) {
    event.preventDefault()
    await onSaveCorrection(correction)
  }

  return (
    <div className="content-card section-stack entries-analysis-card">
      <div className="item-heading-row" style={{ marginBottom: 0 }}>
        <h3>Lectura emocional orientativa</h3>
        <span className={`status-pill risk-pill risk-pill--${analysis.risk_level}`}>
          {riskLabels[analysis.risk_level] || analysis.risk_level}
        </span>
      </div>

      <p>{analysis.summary}</p>

      <div className="emotion-score-list">
        {analysis.emotions.map((item) => (
          <div className="emotion-score-row" key={item.emotion}>
            <div className="emotion-score-label">
              <strong>{item.emotion}</strong>
              <span>{Math.round(item.percentage)}%</span>
            </div>
            <div className="emotion-score-track" aria-hidden="true">
              <span style={{ width: `${Math.max(4, Math.min(100, item.percentage))}%` }} />
            </div>
          </div>
        ))}
      </div>

      {analysis.recommendations?.length ? (
        <div className="analysis-inline-list">
          {analysis.recommendations.map((recommendation) => (
            <span className="status-pill" key={recommendation}>{recommendation}</span>
          ))}
        </div>
      ) : null}

      <p className="muted">{analysis.disclaimer}</p>

      {analysis.reviewed_by_therapist ? (
        <span className="status-pill dashboard-status-pill--active">Revisada pel terapeuta</span>
      ) : (
        <span className="status-pill dashboard-status-pill--pending">Pendent de revisio</span>
      )}

      {analysis.therapist_correction ? (
        <div className="analysis-correction-note">
          <strong>Correccio del terapeuta</strong>
          <p>{analysis.therapist_correction}</p>
        </div>
      ) : null}

      {canCorrect ? (
        <form className="section-stack" onSubmit={handleSubmit}>
          {correctionMessage ? <div className="message">{correctionMessage}</div> : null}
          {correctionError ? <div className="error-banner">{firstErrorMessage(correctionError)}</div> : null}
          <div className="field-group">
            <label htmlFor="analysis-correction">Correccio clinica</label>
            <textarea
              id="analysis-correction"
              value={correction}
              onChange={(event) => setCorrection(event.target.value)}
              rows={4}
              placeholder="Afegeix una lectura alternativa o una matisacio clinica..."
            />
          </div>
          <button className="button-secondary" type="submit" disabled={isSavingCorrection || !correction.trim()}>
            {isSavingCorrection ? 'Guardant correccio...' : 'Guardar correccio'}
          </button>
        </form>
      ) : null}
    </div>
  )
}
