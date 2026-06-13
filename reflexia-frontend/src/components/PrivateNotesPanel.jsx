import { useState } from 'react'
import { FaEdit, FaStickyNote, FaTrash } from 'react-icons/fa'
import { firstErrorMessage, formatEntryDate } from '../lib/entries.js'

export function PrivateNotesPanel({ notes, onCreateNote, onUpdateNote, onDeleteNote }) {
  const [newNote, setNewNote] = useState('')
  const [editingNoteId, setEditingNoteId] = useState('')
  const [editingContent, setEditingContent] = useState('')
  const [isAddingNote, setIsAddingNote] = useState(false)
  const [isSavingNote, setIsSavingNote] = useState(false)
  const [activeNoteId, setActiveNoteId] = useState('')
  const [notesError, setNotesError] = useState('')
  const [notesMessage, setNotesMessage] = useState('')

  async function handleCreateNote(event) {
    event.preventDefault()
    setNotesError('')
    setNotesMessage('')
    setIsSavingNote(true)

    try {
      const response = await onCreateNote(newNote)
      setNewNote('')
      setNotesMessage(response.message)
      setIsAddingNote(false)
    } catch (err) {
      setNotesError(firstErrorMessage(err.response?.data || err))
    } finally {
      setIsSavingNote(false)
    }
  }

  async function handleUpdateNote(event, noteId) {
    event.preventDefault()
    setNotesError('')
    setNotesMessage('')
    setActiveNoteId(noteId)

    try {
      const response = await onUpdateNote(noteId, editingContent)
      setEditingNoteId('')
      setEditingContent('')
      setNotesMessage(response.message)
    } catch (err) {
      setNotesError(firstErrorMessage(err.response?.data || err))
    } finally {
      setActiveNoteId('')
    }
  }

  async function handleDeleteNote(noteId) {
    setNotesError('')
    setNotesMessage('')
    setActiveNoteId(noteId)

    try {
      const response = await onDeleteNote(noteId)
      setNotesMessage(response.message)
    } catch (err) {
      setNotesError(firstErrorMessage(err.response?.data || err))
    } finally {
      setActiveNoteId('')
    }
  }

  function startEditing(note) {
    setNotesError('')
    setNotesMessage('')
    setIsAddingNote(false)
    setEditingNoteId(note.id)
    setEditingContent(note.content)
  }

  return (
    <div className="content-card section-stack">
      <div className="item-heading-row" style={{ marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Notes privades</h3>
        {!isAddingNote ? (
          <button
            type="button"
            className="button-secondary"
            title="Afegir nota privada"
            aria-label="Afegir nota privada"
            onClick={() => { setIsAddingNote(true); setEditingNoteId(''); setNotesError(''); setNotesMessage('') }}
          >
            <FaStickyNote />
          </button>
        ) : null}
      </div>

      {notesMessage ? <div className="message">{notesMessage}</div> : null}
      {notesError ? <div className="error-banner">{notesError}</div> : null}

      {isAddingNote && (
        <form className="section-stack" onSubmit={handleCreateNote}>
          <div className="field-group">
            <textarea
              id="private-note"
              value={newNote}
              onChange={(event) => setNewNote(event.target.value)}
              rows={4}
              placeholder="Nota privada..."
              autoFocus
            />
          </div>
          <div className="button-row">
            <button className="button" type="submit" disabled={isSavingNote || !newNote.trim()}>
              {isSavingNote ? 'Guardant nota...' : 'Guardar nota privada'}
            </button>
            <button className="button-ghost" type="button" onClick={() => { setIsAddingNote(false); setNotesError(''); setNotesMessage('') }}>
              Cancel·lar
            </button>
          </div>
        </form>
      )}

      {notes.length ? (
        <ul className="patient-list">
          {notes.map((note) => {
            const isEditing = editingNoteId === note.id

            return (
              <li key={note.id} className="compact-list-item">
                {isEditing ? (
                  <form className="section-stack" onSubmit={(event) => handleUpdateNote(event, note.id)}>
                    <div className="field-group">
                      <textarea
                        value={editingContent}
                        onChange={(event) => setEditingContent(event.target.value)}
                        rows={4}
                        autoFocus
                      />
                    </div>
                    <div className="button-row">
                      <button className="button" type="submit" disabled={activeNoteId === note.id || !editingContent.trim()}>
                        {activeNoteId === note.id ? 'Guardant...' : 'Guardar canvis'}
                      </button>
                      <button className="button-ghost" type="button" onClick={() => { setEditingNoteId(''); setEditingContent('') }}>
                        Cancel·lar
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="item-heading-row">
                      <strong>Nota privada</strong>
                      <span className="muted" style={{ fontSize: '0.85rem' }}>{formatEntryDate(note.creation_date)}</span>
                    </div>
                    <p style={{ margin: '0.5rem 0' }}>{note.content}</p>
                    <div className="button-row">
                      <button
                        type="button"
                        className="button-secondary"
                        title="Modificar nota privada"
                        aria-label="Modificar nota privada"
                        onClick={() => startEditing(note)}
                      >
                        <FaEdit />
                      </button>
                      <button
                        type="button"
                        className="button-ghost"
                        title="Eliminar nota privada"
                        aria-label="Eliminar nota privada"
                        disabled={activeNoteId === note.id}
                        onClick={() => handleDeleteNote(note.id)}
                      >
                        <FaTrash />
                      </button>
                    </div>
                  </>
                )}
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="muted">Sense notes privades.</p>
      )}
    </div>
  )
}
