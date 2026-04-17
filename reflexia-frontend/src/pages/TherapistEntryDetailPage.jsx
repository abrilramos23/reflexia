import { useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage, formatEntryDate, formatEntryStatus, normalizeStoredContentToHtml } from '../lib/entries.js'

export function TherapistEntryDetailPage() {
  const { user, getPatientEntry } = useAuth()
  const { patientId, entryId } = useParams()
  const [entry, setEntry] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

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

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row">
            <Link to={`/patients/${patientId}`} className="button-ghost" style={{ textDecoration: 'none' }}>
              ← Tornar al detall
            </Link>
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
                <h1 className="section-title">Detall de l'entrada</h1>
                <p className="muted">
                  Creada el {formatEntryDate(entry.created_at)} i actualitzada el {formatEntryDate(entry.updated_at)}.
                </p>
              </div>

              <div className="entries-toolbar" style={{ margin: '1.5rem 0' }}>
                <span className="status-pill">{formatEntryStatus(entry)}</span>
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
            </>
          ) : null}
        </section>
      </div>
    </div>
  )
}
