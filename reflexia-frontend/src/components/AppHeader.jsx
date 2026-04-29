import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function formatRole(role) {
  if (role === 'therapist') return 'Terapeuta'
  if (role === 'patient') return 'Pacient'
  if (role === 'admin') return 'Administrador'
  return 'Usuari'
}

export function AppHeader() {
  const { user } = useAuth()

  return (
    <header className="app-header-wrap">
      <div className="app-header">
        <Link className="brand-lockup" to={user ? '/dashboard' : '/login'}>
          <img src="/leaves.svg" alt="Logo" style={{ width: '50px', height: '50px' }} />
          <span className="brand-copy">
            <strong>Reflexia</strong>
            <span>Plataforma segura de seguiment emocional</span>
          </span>
        </Link>

        {user && (
          <span className="status-pill">{formatRole(user.role)}</span>
        )}
      </div>
    </header>
  )
}
