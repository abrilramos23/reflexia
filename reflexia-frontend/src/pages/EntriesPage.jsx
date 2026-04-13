import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function firstErrorMessage(error) {
  if (!error) {
    return 'S’ha produït un error inesperat.'
  }

  if (typeof error === 'string') {
    return error
  }

  const firstEntry = Object.values(error)[0]

  if (Array.isArray(firstEntry)) {
    return String(firstEntry[0])
  }

  if (typeof firstEntry === 'string') {
    return firstEntry
  }

  return 'S’ha produït un error inesperat.'
}

function sortEntries(entries) {
  return [...entries].sort(
    (left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
  )
}

function formatEntryDate(value) {
  if (!value) {
    return 'Sense data'
  }

  try {
    return new Intl.DateTimeFormat('ca-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function formatEntryStatus(entry) {
  if (entry.is_deleted) {
    return 'Eliminada'
  }

  if (entry.status === 'analyzed') {
    return 'Analitzada'
  }

  return 'Esborrany'
}

function buildEntryPreview(content) {
  const normalized = (content || '').trim()

  if (!normalized) {
    return 'Sense contingut'
  }

  if (normalized.length <= 96) {
    return normalized
  }

  return `${normalized.slice(0, 96)}...`
}

function replaceEntry(entries, nextEntry) {
  const remainingEntries = entries.filter((entry) => entry.id !== nextEntry.id)
  return sortEntries([nextEntry, ...remainingEntries])
}

function buildEntryLabel(entry, index) {
  const status = formatEntryStatus(entry)
  return `Entrada ${index + 1} · ${status} · ${formatEntryDate(entry.updated_at)}`
}

export function EntriesPage() {
  const {
    user,
    getEntriesEditorContext,
    createEntryDraft,
    updateEntryDraft,
    analyzeEntry,
  } = useAuth()
  const [entries, setEntries] = useState([])
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [selectedEntryId, setSelectedEntryId] = useState('')
  const [content, setContent] = useState('')
  const [persistedContent, setPersistedContent] = useState('')
  const [pageError, setPageError] = useState('')
  const [editorMessage, setEditorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isAutosaving, setIsAutosaving] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const selectedEntry = useMemo(
    () => entries.find((entry) => entry.id === selectedEntryId) || null,
    [entries, selectedEntryId],
  )
  const isDeletedEntry = Boolean(selectedEntry?.is_deleted)

  useEffect(() => {
    let isCancelled = false

    async function loadEditor() {
      setPageError('')

      try {
        const response = await getEntriesEditorContext()
        const nextEntries = sortEntries(response.entries || [])

        if (!isCancelled) {
          setEntries(nextEntries)
          setActiveQuestion(response.active_question || null)
          if (nextEntries[0]) {
            setSelectedEntryId(nextEntries[0].id)
          }
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

    loadEditor()

    return () => {
      isCancelled = true
    }
  }, [])

  useEffect(() => {
    if (selectedEntry) {
      setContent(selectedEntry.content)
      setPersistedContent(selectedEntry.content)
      return
    }

    setContent('')
    setPersistedContent('')
  }, [selectedEntry])

  useEffect(() => {
    if (isLoading || isAnalyzing || isAutosaving || isDeletedEntry) {
      return undefined
    }

    const trimmedContent = content.trim()
    if (!trimmedContent || trimmedContent === persistedContent.trim()) {
      return undefined
    }

    const timerId = window.setTimeout(() => {
      void persistDraft(trimmedContent)
    }, 1200)

    return () => {
      window.clearTimeout(timerId)
    }
  }, [content, isAnalyzing, isAutosaving, isDeletedEntry, isLoading, persistedContent, selectedEntryId])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'patient') {
    return <Navigate to="/dashboard" replace />
  }

  async function persistDraft(nextContent) {
    setPageError('')
    setIsAutosaving(true)

    try {
      const payload = {
        content: nextContent,
      }

      if (!selectedEntryId && activeQuestion?.id) {
        payload.therapist_question_id = activeQuestion.id
      }

      const savedEntry = selectedEntryId
        ? await updateEntryDraft(selectedEntryId, payload)
        : await createEntryDraft(payload)

      setEntries((currentEntries) => replaceEntry(currentEntries, savedEntry))
      setSelectedEntryId(savedEntry.id)
      setPersistedContent(savedEntry.content)
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsAutosaving(false)
    }
  }

  async function handleAnalyze() {
    const trimmedContent = content.trim()

    setEditorMessage('')
    setPageError('')

    if (!trimmedContent) {
      setPageError('L’entrada no pot estar buida.')
      return
    }

    if (isDeletedEntry) {
      setPageError('No es poden editar les entrades eliminades.')
      return
    }

    setIsAnalyzing(true)

    try {
      const draftPayload = {
        content: trimmedContent,
      }

      if (!selectedEntryId && activeQuestion?.id) {
        draftPayload.therapist_question_id = activeQuestion.id
      }

      const savedEntry = selectedEntryId
        ? await updateEntryDraft(selectedEntryId, draftPayload)
        : await createEntryDraft(draftPayload)

      const analysisResponse = await analyzeEntry(savedEntry.id, { content: trimmedContent })
      const analyzedEntry = analysisResponse.entry

      setEntries((currentEntries) => replaceEntry(currentEntries, analyzedEntry))
      setSelectedEntryId(analyzedEntry.id)
      setContent(analyzedEntry.content)
      setPersistedContent(analyzedEntry.content)
      setEditorMessage(analysisResponse.message)
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsAnalyzing(false)
    }
  }

  function handleCreateNewEntry() {
    setSelectedEntryId('')
    setContent('')
    setPersistedContent('')
    setEditorMessage('')
    setPageError('')
  }

  return (
    <div className="screen-shell">
      <AppHeader />

      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide entries-editor-shell">
          <div className="panel-heading">
            <p className="eyebrow">Entrades</p>
            <h1 className="section-title">Editor de journaling</h1>
            <p className="muted">
              Escriu una reflexió nova o reprèn una entrada existent. Els canvis amb contingut es desen automàticament com a esborrany.
            </p>
          </div>

          {pageError ? <div className="error-banner">{pageError}</div> : null}
          {editorMessage ? <div className="message">{editorMessage}</div> : null}

          <div className="content-card section-stack entries-question-card">
            <div className="item-heading-row" style={{ marginBottom: 0 }}>
              <h3>Pregunta activa del terapeuta</h3>
              <span className="status-pill">{activeQuestion ? 'Disponible' : 'Sense pregunta'}</span>
            </div>
            {activeQuestion ? (
              <>
                <p>{activeQuestion.question}</p>
                <p className="muted">Disponible des del {formatEntryDate(activeQuestion.created_at)}.</p>
              </>
            ) : (
              <p className="muted">
                Quan el teu terapeuta publiqui una nova pregunta de seguiment, la veuràs aquí.
              </p>
            )}
          </div>

          <div className="content-card section-stack entries-note-card">
            <div className="item-heading-row" style={{ marginBottom: 0 }}>
              <h3>Avís clínic</h3>
              <span className="status-pill">Orientatiu</span>
            </div>
            <p className="muted">
              L’anàlisi emocional és orientativa, es genera automàticament i serà revisada pel teu terapeuta.
            </p>
          </div>

          <div className="entries-controls-grid">
            <div className="field-group">
              <label htmlFor="entry-selector">Entrada a editar</label>
              <select
                id="entry-selector"
                value={selectedEntryId}
                onChange={(event) => setSelectedEntryId(event.target.value)}
                disabled={isLoading}
              >
                <option value="">Nova entrada</option>
                {entries.map((entry, index) => (
                  <option key={entry.id} value={entry.id}>
                    {buildEntryLabel(entry, index)}
                  </option>
                ))}
              </select>
            </div>

            <div className="entries-toolbar">
              <span className="status-pill">
                {isLoading
                  ? 'Carregant'
                  : isAnalyzing
                    ? 'Analitzant'
                    : isAutosaving
                      ? 'Desant esborrany...'
                      : selectedEntry
                        ? formatEntryStatus(selectedEntry)
                        : 'Esborrany nou'}
              </span>

              {selectedEntry?.updated_at ? (
                <span className="status-pill">Modificada {formatEntryDate(selectedEntry.updated_at)}</span>
              ) : null}

              {selectedEntry?.analysis ? (
                <span className="status-pill">Analitzada {formatEntryDate(selectedEntry.last_analyzed_at)}</span>
              ) : null}
            </div>
          </div>

          <div className="field-group">
            <label htmlFor="entry-content">La teva entrada</label>
            <textarea
              id="entry-content"
              className="entries-textarea"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Explica com t’has sentit avui, què t’ha afectat o què voldries compartir amb el teu terapeuta..."
              disabled={isLoading || isDeletedEntry}
            />
          </div>

          <div className="button-row">
            <button
              className="button"
              type="button"
              onClick={handleAnalyze}
              disabled={isLoading || isAnalyzing || isDeletedEntry || !content.trim()}
            >
              {isAnalyzing ? 'Guardant i analitzant...' : 'Guardar i analitzar'}
            </button>
            <button className="button-secondary" type="button" onClick={handleCreateNewEntry}>
              Nova entrada
            </button>
            <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/dashboard">
              Tornar al tauler
            </Link>
          </div>

          {selectedEntry?.analysis ? (
            <div className="content-card section-stack entries-analysis-card">
              <div className="item-heading-row" style={{ marginBottom: 0 }}>
                <h3>Lectura emocional orientativa</h3>
                <span className="status-pill">{selectedEntry.analysis.primary_emotion}</span>
              </div>
              <p>{selectedEntry.analysis.summary}</p>
              <p className="muted">
                To detectat: {selectedEntry.analysis.tone}. {selectedEntry.analysis.disclaimer}
              </p>
            </div>
          ) : (
            <div className="content-card section-stack entries-analysis-card">
              <h3>Sense anàlisi encara</h3>
              <p className="muted">
                Quan premis “Guardar i analitzar”, generarem una lectura emocional inicial a partir del text anonimitzat.
              </p>
            </div>
          )}

          {entries.length > 0 ? (
            <div className="content-card section-stack entries-summary-card">
              <div className="item-heading-row" style={{ marginBottom: 0 }}>
                <h3>Entrades disponibles</h3>
                <span className="status-pill">{entries.length}</span>
              </div>
              <p className="muted">
                {selectedEntry
                  ? `Ara estàs editant: ${buildEntryPreview(selectedEntry.content)}`
                  : 'Pots seleccionar una entrada existent des del desplegable superior per editar-la.'}
              </p>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  )
}
