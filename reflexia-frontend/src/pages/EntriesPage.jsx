import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { FaEdit, FaTrash, FaPlus } from 'react-icons/fa'
import { EmotionalEvolutionPanel } from '../components/EmotionalEvolutionPanel.jsx'
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
  const { user, listEntries, deleteEntry, exportEntriesPdf, getMyEvolution } = useAuth()
  const [entries, setEntries] = useState([])
  const [evolution, setEvolution] = useState(null)
  const [pageError, setPageError] = useState('')
  const [evolutionError, setEvolutionError] = useState('')
  const [pageMessage, setPageMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isEvolutionLoading, setIsEvolutionLoading] = useState(true)
  const [busyEntryId, setBusyEntryId] = useState('')
  const [isExporting, setIsExporting] = useState(false)

  useEffect(() => {
    let isCancelled = false

    async function loadEntries() {
      setPageError('')
      setEvolutionError('')

      const [entriesResult, evolutionResult] = await Promise.allSettled([
        listEntries(),
        getMyEvolution(),
      ])

      if (isCancelled) {
        return
      }

      if (entriesResult.status === 'fulfilled') {
        setEntries(sortEntries(entriesResult.value))
      } else {
        setPageError(firstErrorMessage(entriesResult.reason.response?.data || entriesResult.reason))
      }

      if (evolutionResult.status === 'fulfilled') {
        setEvolution(evolutionResult.value)
      } else {
        setEvolutionError('No s’ha pogut carregar l’evolució emocional.')
      }

      setIsLoading(false)
      setIsEvolutionLoading(false)
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
      `Vols eliminar aquesta entrada?\n\nEs conservarà anonimitzada durant el període legal de retenció.`,
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
          </div>

          {pageMessage ? <div className="message">{pageMessage}</div> : null}
          {pageError ? <div className="error-banner">{pageError}</div> : null}

          <div className="section-toolbar" style={{ gap: '4px' }}>
            <Link className="button" style={{ textDecoration: 'none' }} to="/entries/new">
              <FaPlus />
              Escriure nova entrada
            </Link>
            <button className="button-secondary" type="button" disabled={isExporting || isLoading || !entries.length} onClick={handleExportHistory}>
              {isExporting ? 'Generant PDF...' : 'Exportar historial PDF'}
            </button>
          </div>

          <div className="content-card section-stack entries-summary-card">
            <div className="panel-heading">
              <p className="eyebrow">Evolució emocional</p>
            </div>
            {evolutionError ? (
              <p className="muted">{evolutionError}</p>
            ) : (
              <EmotionalEvolutionPanel evolution={evolution} isLoading={isEvolutionLoading} embedded />
            )}
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
                  <li className="compact-list-item" key={entry.id}>
                    <Link className="patient-item" style={{ textDecoration: 'none' }} to={`/entries/${entry.id}`}>
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
                        {!entry.is_deleted ? (
                          <Link 
                            className="action-chip action-chip--icon" 
                            style={{ textDecoration: 'none' }} 
                            to={`/entries/${entry.id}/edit`} 
                            title="Editar" 
                            aria-label="Editar"
                          >
                            <FaEdit />
                          </Link>
                        ) : null}
                        {!entry.is_deleted ? (
                          <button
                            className="action-chip action-chip--danger action-chip--icon"
                            type="button"
                            disabled={busyEntryId === entry.id}
                            onClick={(e) => {
                              handleDeleteEntry(entry)
                            }}
                            title="Eliminar"
                            aria-label="Eliminar"
                          >
                            {busyEntryId === entry.id ? '...' : <FaTrash />}
                          </button>
                        ) : null}
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="content-card section-stack">
            <h3>Per què no s&apos;esborra del tot?</h3>
            <p className="muted">Les entrades eliminades es conserven anonimitzades per obligació legal de documentació clínica.</p>
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
