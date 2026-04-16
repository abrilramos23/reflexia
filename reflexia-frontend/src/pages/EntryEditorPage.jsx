import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { EntryEditorForm } from '../components/EntryEditorForm.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage } from '../lib/entries.js'

export function EntryEditorPage() {
  const {
    user,
    getEntriesEditorContext,
    getEntry,
    createEntryDraft,
    updateEntryDraft,
    analyzeEntry,
  } = useAuth()
  const navigate = useNavigate()
  const { entryId } = useParams()
  const [entry, setEntry] = useState(null)
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [pageError, setPageError] = useState('')
  const [pageMessage, setPageMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSavingDraft, setIsSavingDraft] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  useEffect(() => {
    let isCancelled = false

    async function loadPage() {
      setPageError('')

      try {
        const contextPromise = getEntriesEditorContext()
        const entryPromise = entryId ? getEntry(entryId) : Promise.resolve(null)
        const [contextResponse, entryResponse] = await Promise.all([contextPromise, entryPromise])

        if (!isCancelled) {
          setActiveQuestion(contextResponse.active_question || null)
          setEntry(entryResponse)
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

    loadPage()

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

  async function handleSaveDraft(content) {
    setPageError('')
    setPageMessage('')
    setIsSavingDraft(true)

    try {
      const payload = { content }

      if (!entry && activeQuestion?.id) {
        payload.therapist_question_id = activeQuestion.id
      }

      const savedEntry = entry
        ? await updateEntryDraft(entry.id, payload)
        : await createEntryDraft(payload)

      setEntry(savedEntry)
      setPageMessage('Esborrany guardat correctament.')

      if (!entry) {
        navigate(`/entries/${savedEntry.id}/edit`, { replace: true })
      }
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsSavingDraft(false)
    }
  }

  async function handleAnalyze(content) {
    setPageError('')
    setPageMessage('')
    setIsAnalyzing(true)

    try {
      const draftPayload = { content }

      if (!entry && activeQuestion?.id) {
        draftPayload.therapist_question_id = activeQuestion.id
      }

      const savedEntry = entry
        ? await updateEntryDraft(entry.id, draftPayload)
        : await createEntryDraft(draftPayload)

      const analysisResponse = await analyzeEntry(savedEntry.id, { content })
      setEntry(analysisResponse.entry)
      setPageMessage(analysisResponse.message)

      if (!entry) {
        navigate(`/entries/${analysisResponse.entry.id}/edit`, { replace: true })
      }
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row">
            <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/entries">
              Tornar al llistat
            </Link>
            {entry ? (
              <Link className="button-ghost" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}`}>
                Veure detall
              </Link>
            ) : null}
          </div>
        </section>

        {isLoading ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <p className="muted">Carregant editor...</p>
          </section>
        ) : entry?.is_deleted ? (
          <section className="screen-card dashboard-panel profile-card--wide">
            <div className="error-banner">No es poden editar les entrades eliminades.</div>
            <div className="button-row">
              <Link className="button-ghost" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}`}>
                Consultar detall
              </Link>
              <Link className="button-ghost" style={{ textDecoration: 'none' }} to="/entries">
                Tornar al llistat
              </Link>
            </div>
          </section>
        ) : (
          <EntryEditorForm
            entry={entry}
            activeQuestion={activeQuestion}
            error={pageError}
            message={pageMessage}
            isSavingDraft={isSavingDraft}
            isAnalyzing={isAnalyzing}
            onSaveDraft={handleSaveDraft}
            onAnalyze={handleAnalyze}
          />
        )}
      </div>
    </div>
  )
}
