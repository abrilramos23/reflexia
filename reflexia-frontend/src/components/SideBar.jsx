import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { sidebarConfig } from '../lib/sidebarConfig'
import { FaBars, FaSignOutAlt } from 'react-icons/fa'
import '../App.css'

function hasClinicMembership(user) {
  return user?.organisation?.type === 'clinic'
    || user?.memberships?.some((membership) => membership?.organisation?.type === 'clinic')
    || false
}

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

    if ((item.path === '/clinic' || item.path.startsWith('/admin/')) && user.role === 'therapist' && !isClinicAdmin) {
      return false
    }

    if (item.path === '/support' && user.role === 'therapist' && !hasClinicMembership(user)) {
      return false
    }

    return true
  })

  const groupedItems = filteredItems.reduce((groups, item) => {
    const section = item.section || 'General'
    if (!groups[section]) {
      groups[section] = []
    }
    groups[section].push(item)
    return groups
  }, {})

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
        {Object.entries(groupedItems).map(([section, items]) => (
          <div className="sidebar-section" key={section}>
            {!collapsed ? <p className="sidebar-section-title">{section}</p> : null}
            {items.map(item => {
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
          </div>
        ))}

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
