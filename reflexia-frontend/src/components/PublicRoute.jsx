import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export function PublicRoute({ children }) {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated) {
    return children
  }

  if (user?.role === 'patient' && user.consent_accepted === false) {
    return <Navigate to="/consent" replace />
  }

  return <Navigate to="/dashboard" replace />
}
