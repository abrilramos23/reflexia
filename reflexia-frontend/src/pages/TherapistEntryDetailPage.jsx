import { useEffect, useState } from 'react'
import { FaArrowLeft, FaCheckCircle } from 'react-icons/fa'
import { Link, Navigate, useParams } from 'react-router-dom'
import { EntryAnalysisPanel } from '../components/EntryAnalysisPanel.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage, formatEntryDate, formatEntryStatus, normalizeStoredContentToHtml } from '../lib/entries.js'

export function TherapistEntryDetailPage() {
  const {
    user,
    getPatientEntry,
    updatePatientEntryAnalysisCorrection,
    exportPatientEntryPdf,
  } = useAuth()
  const { patientId, entryId } = useParams()
  const [entry, setEntry] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [correctionError, setCorrectionError] = useState('')
  const [correctionMessage, setCorrectionMessage] = useState('')
  const [isSavingCorrection, setIsSavingCorrection] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [isMarkingReviewed, setIsMarkingReviewed] = useState(false)

  useEffect(() => {
    let isCancelled = false
    async function loadEntry() {
      setIsLoading(true)
      try {
        const data = await getPatientEntry(patientId, entryId)
        if (!isCancelled) {
          setEntry(data)
        }
      } catch (err) {
        if (!isCancelled) {
          setError(firstErrorMessage(err.response?.data || err))
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }
    loadEntry()
    return () => { isCancelled = true }
  }, [patientId, entryId, getPatientEntry])

  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'therapist') return <Navigate to="/dashboard" replace />

  async function handleSaveCorrection(therapistCorrection) {
    setCorrectionError('')
    setCorrectionMessage('')
    setIsSavingCorrection(true)

    try {
      const analysis = await updatePatientEntryAnalysisCorrection(patientId, entryId, {
        therapist_correction: therapistCorrection,
      })
      setEntry((currentEntry) => ({ ...currentEntry, analysis }))
      setCorrectionMessage('Correccio guardada correctament.')
    } catch (err) {
      setCorrectionError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsSavingCorrection(false)
    }
  }

  async function handleExport() {
    setError('')
    setIsExporting(true)

    try {
      const { blob, filename } = await exportPatientEntryPdf(patientId, entryId)
      triggerBrowserDownload(blob, filename)
    } catch (err) {
      setError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsExporting(false)
    }
  }

  async function handleMarkAsReviewed() {
    setIsMarkingReviewed(true)
    try {
      const analysis = await updatePatientEntryAnalysisCorrection(patientId, entryId, {
        therapist_correction: entry.analysis?.therapist_correction ?? '',
      })
      setEntry((current) => ({ ...current, analysis }))
    } catch (err) {
      setError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsMarkingReviewed(false)
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row" style={{justifyContent: 'space-between'}}>
             <Link to={`/patients/${patientId}`} className="button-ghost" style={{ textDecoration: 'none' }} title="Tornar" aria-label="Tornar">
              <FaArrowLeft />
            </Link>
            <div style={{ display: 'flex', gap: '10px'}}>
                <button className="button-secondary" type="button" disabled={isExporting} onClick={handleExport}>
                  {isExporting ? 'Generant PDF...' : 'Exportar PDF'}
                </button>
                {entry?.analysis && !entry.analysis.reviewed_by_therapist && (
                  <button
                    type="button"
                    className="button"
                    disabled={isMarkingReviewed}
                    onClick={handleMarkAsReviewed}
                  >
                    <FaCheckCircle /> {isMarkingReviewed ? 'Marcant...' : 'Marcar com revisada'}
                  </button>
                )}
            </div>
            
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          {isLoading ? (
            <p className="muted">Carregant entrada...</p>
          ) : error ? (
            <div className="error-banner">{error}</div>
          ) : entry ? (
            <>
              <div className="panel-heading">
                <p className="eyebrow">Entrada de Journaling</p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h1 className="section-title">Detall de l&apos;entrada</h1>
                  <span className="status-pill" style={{ justifySelf: 'flex-end' }}>{formatEntryStatus(entry)}</span>
                </div>
                <p className="muted">
                  Creada el {formatEntryDate(entry.created_at)}. Actualitzada el {formatEntryDate(entry.updated_at)}.
                </p>
              </div>

              {entry.therapist_question && (
                <div className="content-card section-stack entries-question-card" style={{ marginBottom: '2rem' }}>
                  <h3>Pregunta vinculada</h3>
                  <p>{entry.therapist_question.question}</p>
                </div>
              )}

              <div className="content-card section-stack">
                <h3>Contingut</h3>
                <div 
                  className="entries-rendered-content"
                  dangerouslySetInnerHTML={{ __html: normalizeStoredContentToHtml(entry.content) }}
                />
              </div>

              <EntryAnalysisPanel
                analysis={entry.analysis}
                canCorrect={Boolean(entry.analysis)}
                correctionError={correctionError}
                correctionMessage={correctionMessage}
                isSavingCorrection={isSavingCorrection}
                onSaveCorrection={handleSaveCorrection}
              />
            </>
          ) : null}
        </section>
      </div>
    </div>
  )
}

function triggerBrowserDownload(blob, filename) {
  const fileUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = fileUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(fileUrl)
}
