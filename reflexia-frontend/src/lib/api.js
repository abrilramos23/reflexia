import axios from 'axios'

const rawBaseUrl = 'http://127.0.0.1:8000/api'

export const apiBaseUrl = rawBaseUrl.replace(/\/$/, '')
export const consentDocumentUrl = `${apiBaseUrl}/users/consent/document/`

const accessTokenStorageKey = 'reflexia.accessToken'

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

api.interceptors.request.use((config) => {
  const token = getStoredAccessToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})
