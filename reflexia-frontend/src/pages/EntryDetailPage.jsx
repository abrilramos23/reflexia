import { useEffect, useState } from 'react'
import { FaEdit, FaArrowLeft } from 'react-icons/fa'
import { Link, Navigate, useParams } from 'react-router-dom'
import { EntryAnalysisPanel } from '../components/EntryAnalysisPanel.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import {
  firstErrorMessage,
  formatEntryDate,
  formatEntryStatus,
  normalizeStoredContentToHtml,
} from '../lib/entries.js'

export function EntryDetailPage() {
  const { user, getEntry, analyzeEntry, exportEntryPdf } = useAuth()
  const { entryId } = useParams()
  const [entry, setEntry] = useState(null)
  const [pageError, setPageError] = useState('')
  const [pageMessage, setPageMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

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

  async function handleAnalyzeEntry() {
    setPageError('')
    setPageMessage('')
    setIsAnalyzing(true)

    try {
      const response = await analyzeEntry(entry.id)
      setEntry(response.entry)
      setPageMessage(response.message)
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsAnalyzing(false)
    }
  }

  async function handleExport() {
    setPageError('')
    setPageMessage('')
    setIsExporting(true)

    try {
      const { blob, filename } = await exportEntryPdf(entry.id)
      triggerBrowserDownload(blob, filename)
      setPageMessage('S’ha generat el PDF de l’entrada.')
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row" style={{ flexDirection: 'row', justifyContent: 'space-between', width: '100%' }}>
             <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/entries" title="Tornar">
              <FaArrowLeft />
            </Link>
            {entry && !entry.is_deleted ? (
              <div style={{ display: 'flex', flexDirection: 'row', gap: '10px' }}>
                <Link className="button" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}/edit`} title="Editar entrada">
                  <FaEdit />
                  Editar
                </Link>
                <button className="button-secondary" type="button" disabled={isExporting} onClick={handleExport}>
                  {isExporting ? 'Generant PDF...' : 'Exportar PDF'}
                </button>
              </div>
            ) : null}
          </div>
        </section>

        <section className="screen-card dashboard-panel profile-card--wide">
          {pageError ? <div className="error-banner">{pageError}</div> : null}
          {pageMessage ? <div className="message">{pageMessage}</div> : null}

          {isLoading ? (
            <p className="muted">Carregant detall...</p>
          ) : entry ? (
            <>
              <div className="panel-heading">
                <p className="eyebrow">Detall</p>
                <h1 className="section-title">Detall de l’entrada</h1>
                <p className="muted">
                  Creada el {formatEntryDate(entry.creation_date || entry.created_at)}
                  {entry.modification_date ? ` i modificada el ${formatEntryDate(entry.modification_date)}.` : '.'}
                </p>
              </div>

              <div className="entries-toolbar">
                <span className="status-pill">{formatEntryStatus(entry)}</span>
                {entry.analysis ? (
                  <span className="status-pill">Analitzada {formatEntryDate(entry.analysis.analyzed_at)}</span>
                ) : null}
              </div>

              {entry.is_deleted ? (
                <div className="content-card section-stack">
                  <h3>Entrada eliminada</h3>
                  <p className="muted">Conservada de forma anonimitzada.</p>
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
                <EntryAnalysisPanel analysis={entry.analysis} />
              ) : (
                <div className="content-card section-stack entries-analysis-card">
                  <h3>Anàlisi emocional</h3>
                  <p className="muted">Anàlisi pendent.</p>
                  <button className="button" type="button" disabled={isAnalyzing} onClick={handleAnalyzeEntry}>
                    {isAnalyzing ? 'Generant anàlisi...' : 'Generar anàlisi'}
                  </button>
                </div>
              )}
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
