import { Heart, History, LayoutDashboard, LogOut, Upload, X } from 'lucide-react'
import type { ActiveView } from '../../hooks/navigation/useActiveView'
import { NavItem } from './NavItem'
import { Avatar } from './Avatar'

export interface FileIndicator {
  hasFile?: boolean
  hasError?: boolean
}

export interface DashboardFileStatus {
  mortalidad?: FileIndicator
  morbilidad?: FileIndicator
}

export interface SidebarProps {
  user: {
    username: string
    email?: string
    avatarLetter: string
  }
  activeView: ActiveView
  onNavigate: (view: ActiveView) => void
  fileStatus: DashboardFileStatus
  onLogout: () => void
  isMobileOpen?: boolean
  onMobileClose?: () => void
}

const ICON_CLASS = 'size-5 shrink-0'
const SECTION_TITLE_CLASS =
  'px-3 pb-1 pt-5 text-xs font-semibold uppercase tracking-wider text-slate-400'

export function Sidebar({
  user,
  activeView,
  onNavigate,
  fileStatus,
  onLogout,
  isMobileOpen = false,
  onMobileClose,
}: SidebarProps) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
        isMobileOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-magenta text-white">
          <Heart className="size-5" aria-hidden="true" />
        </div>
        <h2 className="flex-1 text-lg font-bold text-brand-deep">
          Vida<span className="text-brand-magenta">Materna</span>
        </h2>
        <button
          type="button"
          onClick={onMobileClose}
          title="Cerrar menú"
          aria-label="Cerrar menú"
          className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 lg:hidden"
        >
          <X className="size-5" aria-hidden="true" />
        </button>
      </div>

      <nav aria-label="Navegación principal" className="flex-1 space-y-1 overflow-y-auto px-3">
        <NavItem
          icon={<LayoutDashboard className={ICON_CLASS} aria-hidden="true" />}
          label="Dashboard Analítico"
          active={activeView === 'analisis'}
          onClick={() => onNavigate('analisis')}
        />

        <h3 className={SECTION_TITLE_CLASS}>Carga de Datos</h3>

        <NavItem
          icon={<Upload className={ICON_CLASS} aria-hidden="true" />}
          label="Mortalidad Materna"
          active={activeView === 'mortalidad'}
          status={fileStatus.mortalidad}
          onClick={() => onNavigate('mortalidad')}
        />

        <NavItem
          icon={<Upload className={ICON_CLASS} aria-hidden="true" />}
          label="Morbilidad Extrema"
          active={activeView === 'morbilidad'}
          status={fileStatus.morbilidad}
          onClick={() => onNavigate('morbilidad')}
        />

        <h3 className={SECTION_TITLE_CLASS}>Administración</h3>

        <NavItem
          icon={<History className={ICON_CLASS} aria-hidden="true" />}
          label="Historial de Cargas"
          active={activeView === 'historial'}
          onClick={() => onNavigate('historial')}
        />
      </nav>

      <div className="flex items-center gap-3 border-t border-slate-200 p-4">
        <Avatar letter={user.avatarLetter} />
        <div className="min-w-0 flex-1">
          <strong className="block truncate text-sm text-slate-900" title={user.username}>
            {user.username}
          </strong>
          <small className="block truncate text-xs text-slate-500" title={user.email || 'VidaMaterna Analytics'}>
            {user.email || 'VidaMaterna Analytics'}
          </small>
        </div>
        <button
          type="button"
          onClick={onLogout}
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-brand-magenta"
        >
          <LogOut className="size-5" aria-hidden="true" />
        </button>
      </div>
    </aside>
  )
}
