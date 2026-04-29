import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import {
  buildEntryPreview,
  firstErrorMessage,
  formatEntryDate,
  formatEntryStatus,
  replaceEntry,
  sortEntries,
} from '../lib/entries.js'

export function EntriesPage() {
  const { user, listEntries, deleteEntry } = useAuth()
  const [entries, setEntries] = useState([])
  const [pageError, setPageError] = useState('')
  const [pageMessage, setPageMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [busyEntryId, setBusyEntryId] = useState('')

  useEffect(() => {
    let isCancelled = false

    async function loadEntries() {
      setPageError('')

      try {
        const response = await listEntries()

        if (!isCancelled) {
          setEntries(sortEntries(response))
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

    loadEntries()

    return () => {
      isCancelled = true
    }
  }, [])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'patient') {
    return <Navigate to="/dashboard" replace />
  }

  async function handleDeleteEntry(entry) {
    const confirmed = window.confirm(
      `Vols eliminar aquesta entrada? La conservarem anonimitzada a la base de dades.`,
    )

    if (!confirmed) {
      return
    }

    setPageError('')
    setPageMessage('')
    setBusyEntryId(entry.id)

    try {
      const response = await deleteEntry(entry.id)
      setEntries((currentEntries) => replaceEntry(currentEntries, response.entry))
      setPageMessage(response.message)
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setBusyEntryId('')
    }
  }

  return (
    <div className="screen-shell">
      <div className="profile-grid">
        <section className="screen-card dashboard-panel profile-card--wide">
          <div className="panel-heading">
            <p className="eyebrow">Entrades</p>
            <h1 className="section-title">Les teves entrades de journaling</h1>
            <p className="muted">
              Consulta el detall de cada entrada, edita’n el contingut o elimina-la amb anonimització.
            </p>
          </div>

          {pageMessage ? <div className="message">{pageMessage}</div> : null}
          {pageError ? <div className="error-banner">{pageError}</div> : null}

          <div className="section-toolbar">
            <Link className="button" style={{ textDecoration: 'none' }} to="/entries/new">
              Escriure nova entrada
            </Link>
          </div>

          <div className="content-card section-stack entries-list-card">
            <h3>Llista d’entrades</h3>

            {isLoading ? (
              <p className="muted">Carregant entrades...</p>
            ) : entries.length === 0 ? (
              <p className="muted">Encara no tens entrades registrades.</p>
            ) : (
              <ul className="patient-list">
                {entries.map((entry) => (
                  <li className="patient-item compact-list-item" key={entry.id}>
                    <div className="entries-list-copy">
                      <div className="item-heading-row">
                        <strong>{formatEntryStatus(entry)}</strong>
                        {entry.is_deleted ? (
                          <span className="status-pill">Anonimitzada</span>
                        ) : null}
                      </div>
                      <p className="muted">Actualitzada: {formatEntryDate(entry.updated_at)}</p>
                      <p className="muted">{buildEntryPreview(entry.content)}</p>
                    </div>

                    <div className="list-actions">
                      <Link className="action-chip action-chip--accent" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}`}>
                        Veure detall
                      </Link>
                      {!entry.is_deleted ? (
                        <Link className="action-chip" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}/edit`}>
                          Editar
                        </Link>
                      ) : null}
                      {!entry.is_deleted ? (
                        <button
                          className="action-chip action-chip--danger"
                          type="button"
                          disabled={busyEntryId === entry.id}
                          onClick={() => handleDeleteEntry(entry)}
                        >
                          {busyEntryId === entry.id ? 'Eliminant...' : 'Eliminar'}
                        </button>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
