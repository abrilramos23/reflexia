import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function formatRole(role) {
  if (role === 'therapist') return 'Terapeuta'
  if (role === 'patient') return 'Pacient'
  if (role === 'admin') return 'Administrador'
  return 'Usuari'
}

export function AppHeader() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', {
      replace: true,
      state: { message: 'Sessió tancada correctament.' },
    })
  }

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

        {user ? (
          <nav className="app-header-nav">
            <span className="status-pill" style={{ textDecoration: 'none', backgroundColor: 'transparent' }}>{formatRole(user.role)}</span>
            <Link style={{ textDecoration: 'none' }} className="button-ghost" to="/profile">
              Perfil
            </Link>
          </nav>
        ) : (
          <nav className="app-header-nav">
            <Link style={{ textDecoration: 'none' }} className="button-ghost" to="/forgot-password">
              Recuperar accés
            </Link>
          </nav>
        )}
      </div>
    </header>
  )
}
