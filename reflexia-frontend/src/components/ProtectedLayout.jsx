import { Sidebar } from './SideBar'
import { AppHeader } from './AppHeader'
import '../App.css'
import { ProtectedRoute } from './ProtectedRoute'

export function ProtectedLayout({ children, hideSidebar = false }) {
  return (
    <ProtectedRoute>
      <div className="app-shell">
        <AppHeader />
        <div className="app-body">
          {!hideSidebar && <Sidebar />}
          <main className="app-content">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}