import { useEffect, useMemo, useRef, useState } from 'react'
import {
  extractPlainTextFromHtml,
  formatEntryDate,
  formatEntryStatus,
  normalizeStoredContentToHtml,
  sanitizeEntryHtml,
} from '../lib/entries.js'

const toolbarButtons = [
  { command: 'bold', label: 'B', title: 'Negreta' },
  { command: 'italic', label: 'I', title: 'Cursiva' },
  { command: 'underline', label: 'U', title: 'Subratllat' },
  { command: 'insertUnorderedList', label: '•', title: 'Llista' },
]

function insertPlainText(text) {
  if (document.queryCommandSupported?.('insertText')) {
    document.execCommand('insertText', false, text)
    return
  }

  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) {
    return
  }

  selection.deleteFromDocument()
  selection.getRangeAt(0).insertNode(document.createTextNode(text))
}

export function EntryEditorForm({
  entry,
  activeQuestion,
  error,
  message,
  isSavingDraft,
  isAnalyzing,
  onSaveDraft,
  onAnalyze,
}) {
  const editorRef = useRef(null)
  const [contentHtml, setContentHtml] = useState(normalizeStoredContentToHtml(entry?.content || ''))
  const isDeletedEntry = Boolean(entry?.is_deleted)

  useEffect(() => {
    const normalizedContent = normalizeStoredContentToHtml(entry?.content || '')
    setContentHtml(normalizedContent)

    if (editorRef.current && editorRef.current.innerHTML !== normalizedContent) {
      editorRef.current.innerHTML = normalizedContent
    }
  }, [entry?.content, entry?.id])

  const plainTextContent = useMemo(
    () => extractPlainTextFromHtml(contentHtml),
    [contentHtml],
  )

  function syncEditorContent(nextHtml) {
    const sanitizedContent = sanitizeEntryHtml(nextHtml)
    setContentHtml(sanitizedContent)

    if (editorRef.current && editorRef.current.innerHTML !== sanitizedContent) {
      editorRef.current.innerHTML = sanitizedContent
    }
  }

  function handleEditorInput(event) {
    syncEditorContent(event.currentTarget.innerHTML)
  }

  function handlePaste(event) {
    event.preventDefault()
    const pastedText = event.clipboardData.getData('text/plain')
    insertPlainText(pastedText)
    syncEditorContent(editorRef.current?.innerHTML || '')
  }

  function applyToolbarCommand(command) {
    if (isDeletedEntry) {
      return
    }

    editorRef.current?.focus()
    document.execCommand(command, false)
    syncEditorContent(editorRef.current?.innerHTML || '')
  }

  return (
    <section className="screen-card dashboard-panel profile-card--wide entries-editor-shell">
      <div className="panel-heading">
        <p className="eyebrow">{entry ? 'Editar entrada' : 'Nova entrada'}</p>
        <h1 className="section-title">{entry ? 'Actualitza el contingut de l’entrada' : 'Escriu una nova entrada'}</h1>
        <p className="muted">
          {entry
            ? `Última modificació: ${formatEntryDate(entry.updated_at)}`
            : 'Pots guardar l’entrada com a esborrany o enviar-la a anàlisi quan estigui llesta.'}
        </p>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {message ? <div className="message">{message}</div> : null}

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

      <div className="entries-toolbar">
        <span className="status-pill">
          {isAnalyzing
            ? 'Analitzant'
            : isSavingDraft
              ? 'Guardant'
              : entry
                ? formatEntryStatus(entry)
                : 'Nova entrada'}
        </span>
        {entry?.last_analyzed_at ? (
          <span className="status-pill">Analitzada {formatEntryDate(entry.last_analyzed_at)}</span>
        ) : null}
        {isDeletedEntry ? <span className="status-pill">Només lectura</span> : null}
      </div>

      <div className="content-card section-stack">
        <div className="entries-toolbar" role="toolbar" aria-label="Format del text">
          {toolbarButtons.map((button) => (
            <button
              key={button.command}
              className="action-chip"
              type="button"
              title={button.title}
              disabled={isDeletedEntry}
              onClick={() => applyToolbarCommand(button.command)}
            >
              {button.label}
            </button>
          ))}
        </div>

        <div
          ref={editorRef}
          className={`entries-rich-editor${isDeletedEntry ? ' entries-rich-editor--disabled' : ''}`}
          contentEditable={!isDeletedEntry}
          suppressContentEditableWarning
          onInput={handleEditorInput}
          onPaste={handlePaste}
          dangerouslySetInnerHTML={{ __html: normalizeStoredContentToHtml(entry?.content || '') }}
        />

        <p className="muted entries-editor-hint">
          {plainTextContent
            ? `${plainTextContent.length} caràcters de contingut.`
            : 'L’entrada no pot quedar buida.'}
        </p>
      </div>

      <div className="button-row">
        <button
          className="button-secondary"
          type="button"
          disabled={isDeletedEntry || isSavingDraft || isAnalyzing || !plainTextContent.trim()}
          onClick={() => onSaveDraft(contentHtml)}
        >
          {isSavingDraft ? 'Guardant esborrany...' : 'Guardar esborrany'}
        </button>
        <button
          className="button"
          type="button"
          disabled={isDeletedEntry || isSavingDraft || isAnalyzing || !plainTextContent.trim()}
          onClick={() => onAnalyze(contentHtml)}
        >
          {isAnalyzing ? 'Guardant i analitzant...' : 'Guardar i analitzar'}
        </button>
      </div>

      {entry?.analysis ? (
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
    </section>
  )
}
