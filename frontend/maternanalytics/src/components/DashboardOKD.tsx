import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useMemo, useCallback, useState } from 'react'
import { useDashboardData } from '../hooks/useDashboardData'
import { Sidebar, type DashboardFileStatus, type FileIndicator } from './dashboard/Sidebar'
import type { DashboardOutletContext } from './dashboard/DashboardViewRoute'
import type { ActiveView } from '../hooks/navigation/useActiveView'
import { Menu } from 'lucide-react'
import { clearSession } from '../api'

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
    if (location.pathname.includes('historial')) return 'historial'
    return 'analisis'
  }, [location.pathname])

  const handleNavigate = useCallback(
    (view: ActiveView) => {
      if (view === 'mortalidad') navigate('/cargar-mortalidad')
      else if (view === 'morbilidad') navigate('/cargar-morbilidad')
      else if (view === 'historial') navigate('/historial')
      else navigate('/dashboard')
      setIsMobileNavOpen(false)
    },
    [navigate],
  )

  const handleLogout = useCallback(() => {
    clearSession()
    if (onLogout) onLogout()
    else navigate('/login')
  }, [navigate, onLogout])

  return (
    <div className="flex min-h-screen bg-slate-50">
      {isMobileNavOpen && (
        <div
          data-testid="sidebar-overlay"
          aria-hidden="true"
          className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
          onClick={() => setIsMobileNavOpen(false)}
        />
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

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 lg:hidden">
          <button
            type="button"
            onClick={() => setIsMobileNavOpen(true)}
            title="Abrir menú"
            aria-label="Abrir menú"
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
          >
            <Menu className="size-5" aria-hidden="true" />
          </button>
          <span className="text-lg font-bold text-brand-deep">
            Vida<span className="text-brand-magenta">Materna</span>
          </span>
        </header>

        <main className="flex-1">
          <div className="mx-auto w-full max-w-7xl p-4 lg:p-8">
            <Outlet context={{ data, onNavigate: handleNavigate } satisfies DashboardOutletContext} />
          </div>
        </main>
      </div>
    </div>
  )
}
