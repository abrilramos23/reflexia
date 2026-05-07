import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { FaEdit, FaTrash, FaEye } from 'react-icons/fa'
import { useAuth } from '../context/AuthContext.jsx'
import {
  buildEntryPreview,
  firstErrorMessage,
  formatEntryDate,
  formatRiskLevel,
  formatEntryStatus,
  sortEntries,
} from '../lib/entries.js'

export function EntriesPage() {
  const { user, listEntries, deleteEntry, exportEntriesPdf } = useAuth()
  const [entries, setEntries] = useState([])
  const [pageError, setPageError] = useState('')
  const [pageMessage, setPageMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [busyEntryId, setBusyEntryId] = useState('')
  const [isExporting, setIsExporting] = useState(false)

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
      `Vols eliminar aquesta entrada?\n\nPer obligació legal (Llei 41/2002), el contingut es conservarà anonimitzat durant el període de retenció, però desapareixerà del teu historial visible.`,
    )

    if (!confirmed) {
      return
    }

    setPageError('')
    setPageMessage('')
    setBusyEntryId(entry.id)

    try {
      const response = await deleteEntry(entry.id)
      setEntries((currentEntries) => currentEntries.filter((currentEntry) => currentEntry.id !== entry.id))
      setPageMessage(response.message)
    } catch (error) {
      setPageError(firstErrorMessage(error.response?.data || error))
    } finally {
      setBusyEntryId('')
    }
  }

  async function handleExportHistory() {
    setPageError('')
    setPageMessage('')
    setIsExporting(true)

    try {
      const { blob, filename } = await exportEntriesPdf()
      triggerBrowserDownload(blob, filename)
      setPageMessage('S\'ha generat el PDF de l\'historial.')
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
          <div className="panel-heading">
            <p className="eyebrow">Entrades</p>
            <h1 className="section-title">Les teves entrades de journaling</h1>
            <p className="muted">
              Consulta el detall de cada entrada, edita&apos;n el contingut o elimina-la amb anonimització.
            </p>
          </div>

          {pageMessage ? <div className="message">{pageMessage}</div> : null}
          {pageError ? <div className="error-banner">{pageError}</div> : null}

          <div className="section-toolbar" style={{ gap: '4px' }}>
            <Link className="button" style={{ textDecoration: 'none' }} to="/entries/new">
              Escriure nova entrada
            </Link>
            <button className="button-secondary" type="button" disabled={isExporting || isLoading || !entries.length} onClick={handleExportHistory}>
              {isExporting ? 'Generant PDF...' : 'Exportar historial PDF'}
            </button>
          </div>

          <div className="content-card section-stack entries-list-card">
            <h3>Llista d&apos;entrades</h3>

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
                      <p className="muted">
                        Risc: {formatRiskLevel(entry.analysis?.risk_level)}
                      </p>
                    </div>

                     <div className="list-actions">
                      <Link className="action-chip action-chip--accent" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}`} title="Veure detall" aria-label="Veure detall">
                        <FaEye />
                      </Link>
                       {!entry.is_deleted ? (
                        <Link className="action-chip" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}/edit`} title="Editar" aria-label="Editar">
                          <FaEdit />
                        </Link>
                      ) : null}
                       {!entry.is_deleted ? (
                        <button
                          className="action-chip action-chip--danger"
                          type="button"
                          disabled={busyEntryId === entry.id}
                          onClick={() => handleDeleteEntry(entry)}
                          title="Eliminar"
                          aria-label="Eliminar"
                        >
                          {busyEntryId === entry.id ? '...' : <FaTrash />}
                        </button>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="content-card section-stack">
            <h3>Per què no s&apos;esborra del tot?</h3>
            <p className="muted">
              Quan elimines una entrada, deixa d&apos;aparèixer al teu historial visible, però la conservem anonimitzada per obligació legal de documentació clínica segons la Llei 41/2002. Si vols ampliar informació, pots exercir el teu dret d&apos;accés.
            </p>
          </div>
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
