import { useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import {
  firstErrorMessage,
  formatEntryDate,
  formatEntryStatus,
  normalizeStoredContentToHtml,
} from '../lib/entries.js'

export function EntryDetailPage() {
  const { user, getEntry } = useAuth()
  const { entryId } = useParams()
  const [entry, setEntry] = useState(null)
  const [pageError, setPageError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isCancelled = false

    async function loadEntry() {
      setPageError('')

      try {
        const response = await getEntry(entryId)

        if (!isCancelled) {
          setEntry(response)
        }
      } catch (error) {
        if (!isCancelled) {
          setPageError(firstErrorMessage(error.response?.data || error))
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }

    loadEntry()

    return () => {
      isCancelled = true
    }
  }, [entryId])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'patient') {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row">
            <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/entries">
              Tornar al llistat
            </Link>
            {entry && !entry.is_deleted ? (
              <Link className="button" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}/edit`}>
                Editar entrada
              </Link>
            ) : null}
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          {pageError ? <div className="error-banner">{pageError}</div> : null}

          {isLoading ? (
            <p className="muted">Carregant detall...</p>
          ) : entry ? (
            <>
              <div className="panel-heading">
                <p className="eyebrow">Detall</p>
                <h1 className="section-title">Detall de l’entrada</h1>
                <p className="muted">
                  Creada el {formatEntryDate(entry.created_at)} i actualitzada el {formatEntryDate(entry.updated_at)}.
                </p>
              </div>

              <div className="entries-toolbar">
                <span className="status-pill">{formatEntryStatus(entry)}</span>
                {entry.last_analyzed_at ? (
                  <span className="status-pill">Analitzada {formatEntryDate(entry.last_analyzed_at)}</span>
                ) : null}
              </div>

              {entry.is_deleted ? (
                <div className="content-card section-stack">
                  <h3>Entrada eliminada</h3>
                  <p className="muted">
                    Aquesta entrada s’ha conservat només de forma anonimitzada i ja no es pot editar.
                  </p>
                </div>
              ) : null}

              {entry.therapist_question ? (
                <div className="content-card section-stack entries-question-card">
                  <h3>Pregunta activa vinculada</h3>
                  <p>{entry.therapist_question.question}</p>
                </div>
              ) : null}

              <div className="content-card section-stack">
                <h3>Contingut</h3>
                <div
                  className="entries-rendered-content"
                  dangerouslySetInnerHTML={{ __html: normalizeStoredContentToHtml(entry.content) }}
                />
              </div>

              {entry.analysis ? (
                <div className="content-card section-stack entries-analysis-card">
                  <div className="item-heading-row" style={{ marginBottom: 0 }}>
                    <h3>Lectura emocional orientativa</h3>
                    <span className="status-pill">{entry.analysis.primary_emotion}</span>
                  </div>
                  <p>{entry.analysis.summary}</p>
                  <p className="muted">
                    To detectat: {entry.analysis.tone}. {entry.analysis.disclaimer}
                  </p>
                </div>
              ) : null}
            </>
          ) : null}
        </section>
      </div>
    </div>
  )
}
