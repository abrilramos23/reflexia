import { createContext, useContext, useEffect, useState } from 'react'
import { api, setStoredAccessToken } from '../lib/api.js'

const AuthContext = createContext(null)

const refreshTokenStorageKey = 'reflexia.refreshToken'
const userStorageKey = 'reflexia.user'
const pendingTwoFactorStorageKey = 'reflexia.pendingTwoFactor'

function getStoredRefreshToken() {
  return localStorage.getItem(refreshTokenStorageKey)
}

function setStoredRefreshToken(token) {
  if (token) {
    localStorage.setItem(refreshTokenStorageKey, token)
    return
  }

  localStorage.removeItem(refreshTokenStorageKey)
}

function getStoredUser() {
  const rawUser = localStorage.getItem(userStorageKey)

  if (!rawUser) {
    return null
  }

  try {
    return JSON.parse(rawUser)
  } catch {
    localStorage.removeItem(userStorageKey)
    return null
  }
}

function setStoredUser(user) {
  if (user) {
    localStorage.setItem(userStorageKey, JSON.stringify(user))
    return
  }

  localStorage.removeItem(userStorageKey)
}

function getStoredPendingTwoFactor() {
  const rawValue = sessionStorage.getItem(pendingTwoFactorStorageKey)

  if (!rawValue) {
    return null
  }

  try {
    return JSON.parse(rawValue)
  } catch {
    sessionStorage.removeItem(pendingTwoFactorStorageKey)
    return null
  }
}

function setStoredPendingTwoFactor(payload) {
  if (payload) {
    sessionStorage.setItem(pendingTwoFactorStorageKey, JSON.stringify(payload))
    return
  }

  sessionStorage.removeItem(pendingTwoFactorStorageKey)
}

function persistSession({ access, refresh, user }) {
  setStoredAccessToken(access)
  setStoredRefreshToken(refresh)
  setStoredUser(user)
}

function clearSession() {
  setStoredAccessToken(null)
  setStoredRefreshToken(null)
  setStoredUser(null)
  setStoredPendingTwoFactor(null)
}

function normalizePatientsPayload(payload) {
  if (!payload) {
    return []
  }

  if (Array.isArray(payload)) {
    return payload
  }

  if (typeof payload === 'object') {
    return [payload]
  }

  return []
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser)
  const [pendingTwoFactor, setPendingTwoFactor] = useState(getStoredPendingTwoFactor)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function bootstrap() {
      const access = localStorage.getItem('reflexia.accessToken')

      if (!access) {
        if (isMounted) {
          setIsBootstrapping(false)
        }
        return
      }

      try {
        const response = await api.get('/auth/me/')

        if (!isMounted) {
          return
        }

        setUser(response.data)
        setStoredUser(response.data)
      } catch {
        clearSession()
        if (isMounted) {
          setUser(null)
          setPendingTwoFactor(null)
        }
      } finally {
        if (isMounted) {
          setIsBootstrapping(false)
        }
      }
    }

    bootstrap()

    return () => {
      isMounted = false
    }
  }, [])

  async function login(email, password) {
    const response = await api.post('/auth/login/', { email, password })
    const data = response.data

    if (data.login_status === 'two_factor_required') {
      const pendingPayload = { email, password, user: data.user }
      setPendingTwoFactor(pendingPayload)
      setStoredPendingTwoFactor(pendingPayload)
      return data
    }

    persistSession(data)
    setPendingTwoFactor(null)
    setUser(data.user)
    return data
  }

  async function verifyTwoFactor(code) {
    const pendingPayload = getStoredPendingTwoFactor()

    if (!pendingPayload) {
      throw new Error('La sessio pendent de 2FA ha caducat. Torna a iniciar sessio.')
    }

    const response = await api.post('/auth/2fa/verify/', {
      email: pendingPayload.email,
      password: pendingPayload.password,
      code,
    })

    const data = response.data
    persistSession(data)
    setUser(data.user)
    setPendingTwoFactor(null)
    setStoredPendingTwoFactor(null)
    return data
  }

  async function logout() {
    const refresh = getStoredRefreshToken()

    try {
      if (refresh) {
        await api.post('/auth/logout/', { refresh })
      }
    } finally {
      clearSession()
      setUser(null)
      setPendingTwoFactor(null)
    }
  }

  async function refreshProfile() {
    const response = await api.get('/auth/me/')
    setUser(response.data)
    setStoredUser(response.data)
    return response.data
  }

  async function acceptConsent() {
    const response = await api.post('/auth/consent/accept/')
    setUser(response.data.user)
    setStoredUser(response.data.user)
    return response.data
  }

  async function rejectConsent() {
    const refresh = getStoredRefreshToken()
    const response = await api.post('/auth/consent/reject/', { refresh })
    clearSession()
    setUser(null)
    setPendingTwoFactor(null)
    return response.data
  }

  async function updateProfile(payload) {
    const response = await api.patch('/auth/me/', payload)
    setUser(response.data.user)
    setStoredUser(response.data.user)
    return response.data
  }

  async function changePassword(payload) {
    const response = await api.post('/auth/change-password/', payload)
    return response.data
  }

  async function listAssociatedContacts() {
    const response = await api.get('/contacts/associated/')
    return response.data
  }

  async function createAssociatedContact(payload) {
    const response = await api.post('/contacts/associated/', payload)
    return response.data
  }

  async function updateAssociatedContact(contactId, payload) {
    const response = await api.patch(`/contacts/associated/${contactId}/`, payload)
    return response.data
  }

  async function deleteAssociatedContact(contactId) {
    const response = await api.delete(`/contacts/associated/${contactId}/`)
    return response.data
  }

  async function listSupportTherapists() {
    const response = await api.get('/contacts/support-therapists/')
    return response.data
  }

  async function listAvailableSupportTherapists() {
    const response = await api.get('/contacts/support-therapists/available/')
    return response.data
  }

  async function createSupportTherapist(payload) {
    const response = await api.post('/contacts/support-therapists/', payload)
    return response.data
  }

  async function deleteSupportTherapist(supportTherapistId) {
    const response = await api.delete(`/contacts/support-therapists/${supportTherapistId}/`)
    return response.data
  }

  async function registerTherapist(payload) {
    const response = await api.post('/auth/register/therapist/', payload)
    return response.data
  }

  async function registerPatient(payload) {
    const response = await api.post('/auth/register/patient/', payload)
    return response.data
  }

  async function listTherapistPatients() {
    const response = await api.get('/auth/patients/')
    return response.data
  }

  async function setupTwoFactor() {
    const response = await api.post('/auth/2fa/setup/')
    return response.data
  }

  async function enableTwoFactor(code) {
    const response = await api.post('/auth/2fa/enable/', { code })
    setUser(response.data.user)
    setStoredUser(response.data.user)
    return response.data
  }

  async function disableTwoFactor(payload) {
    const response = await api.post('/auth/2fa/disable/', payload)
    setUser(response.data.user)
    setStoredUser(response.data.user)
    return response.data
  }

  async function deleteAccount(password) {
    const refresh = getStoredRefreshToken()

    try {
      const response = await api.post('/auth/delete-account/', {
        password,
        refresh,
      })

      clearSession()
      setUser(null)
      setPendingTwoFactor(null)
      return response.data
    } catch (error) {
      const responseData = error.response?.data

      if (responseData?.patients) {
        responseData.patients = normalizePatientsPayload(responseData.patients)
      }

      throw responseData || error
    }
  }

  async function deactivatePatient(patientId) {
    const response = await api.post('/auth/patients/deactivate/', {
      patient_id: patientId,
    })

    return response.data
  }

  const value = {
    user,
    pendingTwoFactor,
    isAuthenticated: Boolean(user),
    isBootstrapping,
    login,
    verifyTwoFactor,
    logout,
    refreshProfile,
    acceptConsent,
    rejectConsent,
    updateProfile,
    changePassword,
    listAssociatedContacts,
    createAssociatedContact,
    updateAssociatedContact,
    deleteAssociatedContact,
    listSupportTherapists,
    listAvailableSupportTherapists,
    createSupportTherapist,
    deleteSupportTherapist,
    registerTherapist,
    registerPatient,
    listTherapistPatients,
    setupTwoFactor,
    enableTwoFactor,
    disableTwoFactor,
    deleteAccount,
    deactivatePatient,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }

  return context
}
