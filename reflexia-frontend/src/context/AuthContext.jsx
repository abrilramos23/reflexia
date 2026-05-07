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

  async function getPatient(patientId) {
    const response = await api.get(`/auth/patients/${patientId}/`)
    return response.data
  }

  async function getEntriesEditorContext() {
    const response = await api.get('/entries/editor/')
    return response.data
  }

  async function listEntries() {
    const response = await api.get('/entries/')
    return response.data
  }

  async function getEntry(entryId) {
    const response = await api.get(`/entries/${entryId}/`)
    return response.data
  }

  async function createEntryDraft(payload) {
    const response = await api.post('/entries/', payload)
    return response.data
  }

  async function updateEntryDraft(entryId, payload) {
    const response = await api.patch(`/entries/${entryId}/`, payload)
    return response.data
  }

  async function analyzeEntry(entryId, payload = {}) {
    const response = await api.post(`/entries/${entryId}/analyze/`, payload)
    return response.data
  }

  async function exportEntryPdf(entryId) {
    const response = await api.get(`/entries/${entryId}/export/`, { responseType: 'blob' })
    return {
      blob: response.data,
      filename: readDownloadFilename(response.headers['content-disposition']) || `entry-${entryId}.pdf`,
    }
  }

  async function exportEntriesPdf() {
    const response = await api.get('/entries/export/', { responseType: 'blob' })
    return {
      blob: response.data,
      filename: readDownloadFilename(response.headers['content-disposition']) || 'entries-history.pdf',
    }
  }

  async function getMyEvolution() {
    const response = await api.get('/analysis/evolution/')
    return response.data
  }

  async function deleteEntry(entryId) {
    const response = await api.delete(`/entries/${entryId}/`)
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

  async function getPlatformStats() {
    const response = await api.get('/admin/stats/platform/')
    return response.data
  }

  async function getClinicStats() {
    const response = await api.get('/admin/stats/clinic/')
    return response.data
  }

  async function getTherapistDashboardData() {
    const response = await api.get('/auth/dashboard/therapist/')
    return response.data
  }

  async function listOrganisations() {
    const response = await api.get('/admin/organisations/')
    return response.data
  }

  async function createOrganisation(payload) {
    const response = await api.post('/admin/organisations/', payload)
    return response.data
  }

  async function updateOrganisation(organisationId, payload) {
    const response = await api.patch(`/admin/organisations/${organisationId}/`, payload)
    return response.data
  }

  async function deleteOrganisation(organisationId) {
    const response = await api.delete(`/admin/organisations/${organisationId}/`)
    return response.data
  }

  async function registerClinicAdmin(payload) {
    const response = await api.post('/admin/register/clinic-admin/', payload)
    return response.data
  }

  async function listAllClinicAdmins() {
    const response = await api.get('/admin/users/clinic-admins/')
    return response.data
  }

  async function updateClinicAdmin(adminId, payload) {
    const response = await api.patch(`/admin/users/clinic-admins/${adminId}/`, payload)
    return response.data
  }

  async function deleteClinicAdmin(adminId) {
    const response = await api.delete(`/admin/users/clinic-admins/${adminId}/`)
    return response.data
  }

  async function listAllTherapists() {
    const response = await api.get('/admin/users/therapists/')
    return response.data
  }

  async function listClinicTherapists() {
    const response = await api.get('/admin/users/clinic/therapists/')
    return response.data
  }

  async function updateTherapist(therapistId, payload) {
    const response = await api.patch(`/admin/users/therapists/${therapistId}/`, payload)
    return response.data
  }

  async function deleteTherapist(therapistId) {
    const response = await api.delete(`/admin/users/therapists/${therapistId}/`)
    return response.data
  }

  async function listPatientEntries(patientId) {
    const response = await api.get(`/auth/patients/${patientId}/entries/`)
    return response.data
  }

  async function getPatientEntry(patientId, entryId) {
    const response = await api.get(`/auth/patients/${patientId}/entries/${entryId}/`)
    return response.data
  }

  async function exportPatientEntryPdf(patientId, entryId) {
    const response = await api.get(`/auth/patients/${patientId}/entries/${entryId}/export/`, { responseType: 'blob' })
    return {
      blob: response.data,
      filename: readDownloadFilename(response.headers['content-disposition']) || `patient-entry-${entryId}.pdf`,
    }
  }

  async function exportPatientEntriesPdf(patientId) {
    const response = await api.get(`/auth/patients/${patientId}/entries/export/`, { responseType: 'blob' })
    return {
      blob: response.data,
      filename: readDownloadFilename(response.headers['content-disposition']) || `patient-history-${patientId}.pdf`,
    }
  }

  async function getPatientEvolution(patientId) {
    const response = await api.get(`/auth/patients/${patientId}/analysis/evolution/`)
    return response.data
  }

  async function updatePatientEntryAnalysisCorrection(patientId, entryId, payload) {
    const response = await api.patch(`/auth/patients/${patientId}/entries/${entryId}/analysis/`, payload)
    return response.data
  }

  async function listPatientQuestions(patientId) {
    const response = await api.get(`/auth/patients/${patientId}/questions/`)
    return response.data
  }

  async function createPatientQuestion(patientId, payload) {
    const response = await api.post(`/auth/patients/${patientId}/questions/`, payload)
    return response.data
  }

  async function getPatientQuestion(patientId, questionId) {
    const response = await api.get(`/auth/patients/${patientId}/questions/${questionId}/`)
    return response.data
  }

  async function listPatientEntryNotes(patientId, entryId) {
    const response = await api.get(`/auth/patients/${patientId}/entries/${entryId}/notes/`)
    return response.data
  }

  async function createPatientEntryNote(patientId, entryId, payload) {
    const response = await api.post(`/auth/patients/${patientId}/entries/${entryId}/notes/`, payload)
    return response.data
  }

  const isClinicAdmin = user?.is_clinic_admin ?? user?.memberships?.some((m) => m.is_admin) ?? false

  const value = {
    user,
    role: user?.role,
    isClinicAdmin,
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
    getPatient,
    getEntriesEditorContext,
    listEntries,
    getEntry,
    createEntryDraft,
    updateEntryDraft,
    analyzeEntry,
    exportEntryPdf,
    exportEntriesPdf,
    getMyEvolution,
    deleteEntry,
    setupTwoFactor,
    enableTwoFactor,
    disableTwoFactor,
    deleteAccount,
    deactivatePatient,
    listPatientEntries,
    getPatientEntry,
    exportPatientEntryPdf,
    exportPatientEntriesPdf,
    getPatientEvolution,
    updatePatientEntryAnalysisCorrection,
    listPatientQuestions,
    createPatientQuestion,
    getPatientQuestion,
    listPatientEntryNotes,
    createPatientEntryNote,
    getPlatformStats,
    getClinicStats,
    getTherapistDashboardData,
    listOrganisations,
    createOrganisation,
    updateOrganisation,
    deleteOrganisation,
    registerClinicAdmin,
    listAllClinicAdmins,
    updateClinicAdmin,
    deleteClinicAdmin,
    listAllTherapists,
    listClinicTherapists,
    updateTherapist,
    deleteTherapist,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function readDownloadFilename(contentDisposition) {
  if (!contentDisposition) {
    return ''
  }

  const match = /filename=\"?([^\";]+)\"?/i.exec(contentDisposition)
  return match ? match[1] : ''
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }

  return context
}
