import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { PublicRoute } from './components/PublicRoute.jsx'
import { useAuth } from './context/AuthContext.jsx'
import { ActivateAccountPage } from './pages/ActivateAccountPage.jsx'
import { ConsentPage } from './pages/ConsentPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { EntryDetailPage } from './pages/EntryDetailPage.jsx'
import { EntryEditorPage } from './pages/EntryEditorPage.jsx'
import { EntriesPage } from './pages/EntriesPage.jsx'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { PatientsPage } from './pages/PatientsPage.jsx'
import { ProfilePage } from './pages/ProfilePage.jsx'
import { ResetPasswordPage } from './pages/ResetPasswordPage.jsx'
import { TwoFactorPage } from './pages/TwoFactorPage.jsx'
import { ProtectedLayout } from './components/ProtectedLayout.jsx'
import { PatientDetailPage } from './pages/PatientDetailPage.jsx'
import { TherapistEntryDetailPage } from './pages/TherapistEntryDetailPage.jsx'
import { TherapistQuestionDetailPage } from './pages/TherapistQuestionDetailPage.jsx'

function LoadingScreen() {
  return (
    <div className="screen-shell">
      <div className="screen-card screen-card--centered">
        <p className="eyebrow">Reflexia</p>
        <h1>Preparant la teva sessió</h1>
        <p className="muted">Estem comprovant l’autenticació i carregant l’estat del compte.</p>
      </div>
    </div>
  )
}

function App() {
  const { isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return <LoadingScreen />
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route path="/activate-account" element={<ActivateAccountPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route
        path="/2fa"
        element={
          <PublicRoute>
            <TwoFactorPage />
          </PublicRoute>
        }
      />
      <Route
        path="/consent"
        element={
          <ProtectedLayout>
            <ConsentPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedLayout>
            <DashboardPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/entries"
        element={
          <ProtectedLayout>
            <EntriesPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/entries/new"
        element={
          <ProtectedLayout>
            <EntryEditorPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/entries/:entryId"
        element={
          <ProtectedLayout>
            <EntryDetailPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/entries/:entryId/edit"
        element={
          <ProtectedLayout>
            <EntryEditorPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedLayout>
            <ProfilePage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/patients"
        element={
          <ProtectedLayout>
            <PatientsPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/patients/:patientId"
        element={
          <ProtectedLayout>
            <PatientDetailPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/patients/:patientId/entries/:entryId"
        element={
          <ProtectedLayout>
            <TherapistEntryDetailPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/patients/:patientId/questions/:questionId"
        element={
          <ProtectedLayout>
            <TherapistQuestionDetailPage />
          </ProtectedLayout>
        }
      />
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
