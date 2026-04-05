import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { ProtectedRoute } from './components/ProtectedRoute.jsx'
import { PublicRoute } from './components/PublicRoute.jsx'
import { useAuth } from './context/AuthContext.jsx'
import { ActivateAccountPage } from './pages/ActivateAccountPage.jsx'
import { ConsentPage } from './pages/ConsentPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { PatientsPage } from './pages/PatientsPage.jsx'
import { ProfilePage } from './pages/ProfilePage.jsx'
import { ResetPasswordPage } from './pages/ResetPasswordPage.jsx'
import { TwoFactorPage } from './pages/TwoFactorPage.jsx'

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
          <ProtectedRoute>
            <ConsentPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/patients"
        element={
          <ProtectedRoute>
            <PatientsPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
