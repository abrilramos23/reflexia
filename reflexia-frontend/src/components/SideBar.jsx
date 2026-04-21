import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { sidebarConfig } from '../lib/sidebarConfig'
import { FaBars, FaSignOutAlt } from 'react-icons/fa'
import '../App.css'

export function Sidebar() {
  const { user, isClinicAdmin, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('sidebarCollapsed') === 'true'
  })

  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', collapsed)
  }, [collapsed])

  if (!user) return null

  const filteredItems = sidebarConfig.filter((item) => {
    const roleMatch = item.roles.includes(user.role)
    if (!roleMatch) return false

    // If it's an admin path and user is a therapist, they must be a clinic admin
    if (item.path.startsWith('/admin/') && user.role === 'therapist' && !isClinicAdmin) {
      return false
    }

    return true
  })

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      
      <button
        className="sidebar-toggle"
        onClick={() => setCollapsed(prev => !prev)}
      >
        <FaBars />
      </button>

      <nav className="sidebar-nav">
        {filteredItems.map(item => {
          const Icon = item.icon
          const isActive = location.pathname.startsWith(item.path)

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-link ${isActive ? 'active' : ''}`}
              title={collapsed ? item.label : ''}
            >
              <Icon />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}

        <button
          onClick={handleLogout}
          className="sidebar-link logout"
          title={collapsed ? 'Tancar sessió' : ''}
        >
          <FaSignOutAlt />
          {!collapsed && <span>Tancar sessió</span>}
        </button>
      </nav>
    </aside>
  )
}