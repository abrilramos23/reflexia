import { useEffect, useState } from 'react'
import { FaArrowLeft } from 'react-icons/fa'
import { Link, Navigate, useParams } from 'react-router-dom'
import { EntryAnalysisPanel } from '../components/EntryAnalysisPanel.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { firstErrorMessage, formatEntryDate, formatEntryStatus, normalizeStoredContentToHtml } from '../lib/entries.js'

export function TherapistEntryDetailPage() {
  const { user, getPatientEntry, updatePatientEntryAnalysisCorrection, listPatientEntryNotes, createPatientEntryNote, exportPatientEntryPdf } = useAuth()
  const { patientId, entryId } = useParams()
  const [entry, setEntry] = useState(null)
  const [notes, setNotes] = useState([])
  const [newNote, setNewNote] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [correctionError, setCorrectionError] = useState('')
  const [correctionMessage, setCorrectionMessage] = useState('')
  const [isSavingCorrection, setIsSavingCorrection] = useState(false)
  const [notesError, setNotesError] = useState('')
  const [notesMessage, setNotesMessage] = useState('')
  const [isSavingNote, setIsSavingNote] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  useEffect(() => {
    let isCancelled = false
    async function loadEntry() {
      setIsLoading(true)
      try {
        const [data, noteData] = await Promise.all([
          getPatientEntry(patientId, entryId),
          listPatientEntryNotes(patientId, entryId),
        ])
        if (!isCancelled) {
          setEntry(data)
          setNotes(noteData)
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

  async function handleSaveNote(event) {
    event.preventDefault()
    setNotesError('')
    setNotesMessage('')
    setIsSavingNote(true)

    try {
      const response = await createPatientEntryNote(patientId, entryId, { content: newNote })
      setNotes((currentNotes) => [response.note, ...currentNotes])
      setNewNote('')
      setNotesMessage(response.message)
    } catch (err) {
      setNotesError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsSavingNote(false)
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

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="button-row" style={{justifyContent: 'space-between'}}>
             <Link to={`/patients/${patientId}`} className="button-ghost" style={{ textDecoration: 'none' }} title="Tornar" aria-label="Tornar">
              <FaArrowLeft />
            </Link>
            <button className="button-secondary" type="button" disabled={isExporting} onClick={handleExport}>
              {isExporting ? 'Generant PDF...' : 'Exportar PDF'}
            </button>
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

              <div className="content-card section-stack">
                <h3>Notes privades</h3>
                <form className="section-stack" onSubmit={handleSaveNote}>
                  {notesMessage ? <div className="message">{notesMessage}</div> : null}
                  {notesError ? <div className="error-banner">{notesError}</div> : null}
                  <div className="field-group">
                    <textarea
                      id="private-note"
                      value={newNote}
                      onChange={(event) => setNewNote(event.target.value)}
                      rows={4}
                      placeholder="Afegeix una observació clínica privada..."
                    />
                  </div>
                  <div className="button-row">
                    <button className="button" type="submit" disabled={isSavingNote || !newNote.trim()}>
                      {isSavingNote ? 'Guardant nota...' : 'Guardar nota privada'}
                    </button>
                  </div>
                </form>

                {notes.length ? (
                  <ul className="patient-list">
                    {notes.map((note) => (
                      <li key={note.id} className="compact-list-item">
                        <div className="item-heading-row">
                          <strong>Nota privada</strong>
                          <span className="muted" style={{ fontSize: '0.85rem' }}>{formatEntryDate(note.creation_date)}</span>
                        </div>
                        <p style={{ margin: '0.5rem 0 0' }}>{note.content}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Encara no has afegit notes privades a aquesta entrada.</p>
                )}
              </div>
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
