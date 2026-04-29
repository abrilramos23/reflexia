function createDocumentFromHtml(html) {
  if (typeof DOMParser === 'undefined') {
    return null
  }

  return new DOMParser().parseFromString(html, 'text/html')
}

function escapeHtml(text) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function sanitizeNode(node, targetDocument, allowedTags) {
  if (node.nodeType === Node.TEXT_NODE) {
    return targetDocument.createTextNode(node.textContent || '')
  }

  if (node.nodeType !== Node.ELEMENT_NODE) {
    return targetDocument.createTextNode('')
  }

  const tagName = node.tagName.toUpperCase()

  if (!allowedTags.has(tagName)) {
    const fragment = targetDocument.createDocumentFragment()
    Array.from(node.childNodes).forEach((childNode) => {
      fragment.appendChild(sanitizeNode(childNode, targetDocument, allowedTags))
    })
    return fragment
  }

  const cleanElement = targetDocument.createElement(tagName.toLowerCase())
  Array.from(node.childNodes).forEach((childNode) => {
    cleanElement.appendChild(sanitizeNode(childNode, targetDocument, allowedTags))
  })
  return cleanElement
}

export function firstErrorMessage(error) {
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

export function sortEntries(entries) {
  return [...entries].sort(
    (left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
  )
}

export function replaceEntry(entries, nextEntry) {
  const remainingEntries = entries.filter((entry) => entry.id !== nextEntry.id)
  return sortEntries([nextEntry, ...remainingEntries])
}

export function formatEntryDate(value) {
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

export function formatEntryStatus(entry) {
  if (entry.is_deleted) {
    return 'Eliminada'
  }

  if (entry.status === 'analyzed') {
    return 'Analitzada'
  }

  return 'Esborrany'
}

export function extractPlainTextFromHtml(content) {
  if (!content) {
    return ''
  }

  const parsedDocument = createDocumentFromHtml(content)
  if (!parsedDocument) {
    return content.replace(/<[^>]+>/g, ' ').trim()
  }

  return (parsedDocument.body.textContent || '').replace(/\s+/g, ' ').trim()
}

export function buildEntryPreview(content) {
  const plainText = extractPlainTextFromHtml(content)

  if (!plainText) {
    return 'Sense contingut'
  }

  if (plainText.length <= 120) {
    return plainText
  }

  return `${plainText.slice(0, 120)}...`
}

export function sanitizeEntryHtml(content) {
  if (!content) {
    return ''
  }

  const parsedDocument = createDocumentFromHtml(content)
  if (!parsedDocument) {
    return escapeHtml(content).replaceAll('\n', '<br>')
  }

  const cleanDocument = document.implementation.createHTMLDocument('')
  const wrapper = cleanDocument.createElement('div')
  const allowedTags = new Set(['B', 'BR', 'DIV', 'EM', 'I', 'LI', 'OL', 'P', 'STRONG', 'U', 'UL'])

  Array.from(parsedDocument.body.childNodes).forEach((childNode) => {
    wrapper.appendChild(sanitizeNode(childNode, cleanDocument, allowedTags))
  })

  return wrapper.innerHTML
}

export function normalizeStoredContentToHtml(content) {
  if (!content) {
    return ''
  }

  const looksLikeHtml = /<\/?[a-z][\s\S]*>/i.test(content)

  if (looksLikeHtml) {
    return sanitizeEntryHtml(content)
  }

  return escapeHtml(content).replaceAll('\n', '<br>')
}
