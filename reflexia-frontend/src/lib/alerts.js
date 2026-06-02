const alertStatusLabels = {
  pending: 'Pendent',
  validated: 'Validada',
  dismissed: 'Descartada',
}

const riskLevelLabels = {
  none: 'Sense risc',
  low: 'Risc baix',
  moderate: 'Risc moderat',
  high: 'Risc alt',
}

const notificationStatusLabels = {
  sent: 'Enviada',
  failed: 'Fallida',
  acknowledged: 'Confirmada',
}

const emotionLabels = {
  anger: 'Ràbia',
  anxiety: 'Ansietat',
  calm: 'Calma',
  confusion: 'Confusió',
  disgust: 'Fàstic',
  fear: 'Por',
  guilt: 'Culpa',
  happiness: 'Felicitat',
  hope: 'Esperança',
  joy: 'Alegria',
  loneliness: 'Soledat',
  neutral: 'Neutral',
  sadness: 'Tristesa',
  shame: 'Vergonya',
  stress: 'Estrès',
  surprise: 'Sorpresa',
}

const relationLabels = {
  brother: 'Germà',
  child: 'Fill/a',
  daughter: 'Filla',
  family: 'Família',
  father: 'Pare',
  friend: 'Amistat',
  mother: 'Mare',
  parent: 'Progenitor/a',
  partner: 'Parella',
  sibling: 'Germà/ana',
  sister: 'Germana',
  son: 'Fill',
  spouse: 'Cònjuge',
}

const knownErrorMessages = {
  'At least one contact must be selected.': 'Selecciona almenys un contacte.',
  'Invalid action. Use \'VALIDATE\' or \'DISMISS\'.': 'Acció no vàlida.',
}

export function formatAlertStatus(status) {
  return alertStatusLabels[normalizeKey(status)] || status || 'Sense estat'
}

export function formatRiskLevel(riskLevel) {
  return riskLevelLabels[normalizeKey(riskLevel)] || riskLevel || 'Sense risc'
}

export function formatNotificationStatus(status) {
  return notificationStatusLabels[normalizeKey(status)] || status || 'Sense estat'
}

export function formatEmotion(emotion) {
  return emotionLabels[normalizeKey(emotion)] || emotion || 'No disponible'
}

export function formatContactRelation(relation) {
  return relationLabels[normalizeKey(relation)] || relation || 'Relació no indicada'
}

export function formatSelectedContactCount(count) {
  return count === 1 ? 'Notificar 1 contacte' : `Notificar ${count} contactes`
}

export function translateKnownAlertMessage(message) {
  return knownErrorMessages[message] || message
}

function normalizeKey(value) {
  return String(value || '').trim().toLowerCase()
}
