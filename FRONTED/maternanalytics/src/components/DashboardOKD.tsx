import './dashboard/DashboardShell.css'
import { useLocation, useNavigate } from 'react-router-dom'
import { useMemo, useCallback, useState } from 'react'
import { useDashboardData } from '../hooks/useDashboardData'
import { Sidebar, type DashboardFileStatus, type FileIndicator } from './dashboard/Sidebar'
import { ViewRouter } from './dashboard/ViewRouter'
import type { ActiveView } from '../hooks/navigation/useActiveView'
import { MenuIcon } from './icons'

export type { DashboardFileStatus, FileIndicator }

export interface DashboardOKDProps {
  onLogout?: () => void
}

export default function DashboardOKD({ onLogout }: DashboardOKDProps = {}) {
  const data = useDashboardData()
  const location = useLocation()
  const navigate = useNavigate()
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false)

  // Sincronizar la vista activa con la ruta URL actual
  const activeView: ActiveView = useMemo(() => {
    if (location.pathname.includes('mortalidad')) return 'mortalidad'
    if (location.pathname.includes('morbilidad')) return 'morbilidad'
    return 'analisis'
  }, [location.pathname])

  const handleNavigate = useCallback(
    (view: ActiveView) => {
      data.setActiveView(view)
      if (view === 'mortalidad') navigate('/cargar-mortalidad')
      else if (view === 'morbilidad') navigate('/cargar-morbilidad')
      else navigate('/dashboard')
      setIsMobileNavOpen(false)
    },
    [data, navigate],
  )

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_email')
    if (onLogout) onLogout()
    else navigate('/login')
  }, [navigate, onLogout])

  return (
    <div className="dashboard-okd-container">
      <button
        className="mobile-topbar-menu-btn"
        onClick={() => setIsMobileNavOpen(true)}
        title="Abrir menú"
        aria-label="Abrir menú"
        type="button"
      >
        <MenuIcon />
      </button>

      {isMobileNavOpen && (
        <div className="sidebar-overlay" onClick={() => setIsMobileNavOpen(false)} />
      )}

      <Sidebar
        user={{ username: data.username, email: data.email, avatarLetter: data.avatarLetter }}
        activeView={activeView}
        onNavigate={handleNavigate}
        fileStatus={{
          mortalidad: {
            hasFile: Boolean(data.mortalidadFile),
            hasError: Boolean(data.mortalidadError),
          },
          morbilidad: {
            hasFile: Boolean(data.morbilidadFile),
            hasError: Boolean(data.morbilidadError),
          },
        }}
        onLogout={handleLogout}
        isMobileOpen={isMobileNavOpen}
        onMobileClose={() => setIsMobileNavOpen(false)}
      />

      <main className="main-content-okd">
        <div className="content-area-okd">
          <ViewRouter
            activeView={activeView}
            data={data}
            onNavigate={handleNavigate}
          />
        </div>
      </main>
    </div>
  )
}

