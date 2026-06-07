import axios from 'axios'

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const apiBaseUrl = rawBaseUrl.replace(/\/$/, '')
export const consentDocumentUrl = `${apiBaseUrl}/users/consent/document/`
export function consentDocumentUrlForRole(role = 'patient') {
  return `${consentDocumentUrl}?role=${encodeURIComponent(role)}`
}

const accessTokenStorageKey = 'reflexia.accessToken'
const authExpiredListeners = new Set()

export const api = axios.create({
  baseURL: apiBaseUrl,
})

export function getStoredAccessToken() {
  return localStorage.getItem(accessTokenStorageKey)
}

export function setStoredAccessToken(token) {
  if (token) {
    localStorage.setItem(accessTokenStorageKey, token)
    return
  }

  localStorage.removeItem(accessTokenStorageKey)
}

export function onAuthExpired(listener) {
  authExpiredListeners.add(listener)
  return () => authExpiredListeners.delete(listener)
}

function notifyAuthExpired() {
  authExpiredListeners.forEach((listener) => listener())
}

function hasAuthorizationHeader(headers) {
  if (!headers) {
    return false
  }

  if (typeof headers.get === 'function') {
    return Boolean(headers.get('Authorization') || headers.get('authorization'))
  }

  return Boolean(headers.Authorization || headers.authorization)
}

api.interceptors.request.use((config) => {
  const token = getStoredAccessToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && hasAuthorizationHeader(error.config?.headers)) {
      notifyAuthExpired()
    }

    return Promise.reject(error)
  },
)
