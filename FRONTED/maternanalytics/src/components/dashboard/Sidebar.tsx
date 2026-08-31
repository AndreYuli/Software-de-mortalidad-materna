import './Sidebar.css'
import type { ActiveView } from '../../hooks/navigation/useActiveView'
import { LogoIcon, DashboardIcon, UploadIcon, LogoutIcon, CloseIcon } from '../icons'
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
    <aside className={`sidebar-okd ${isMobileOpen ? 'sidebar-okd--open' : ''}`}>
      <div className="sidebar-header-okd">
        <div className="logo-icon-okd">
          <LogoIcon width="100%" height="100%" />
        </div>
        <h2 className="brand-title-okd">
          Vida<span>Materna</span>
        </h2>
        <button
          className="sidebar-close-btn"
          onClick={onMobileClose}
          title="Cerrar menú"
          aria-label="Cerrar menú"
          type="button"
        >
          <CloseIcon />
        </button>
      </div>

      <nav className="sidebar-nav-okd">
        <NavItem
          icon={<DashboardIcon />}
          label="Dashboard Analítico"
          active={activeView === 'analisis'}
          onClick={() => onNavigate('analisis')}
        />

        <h3 className="nav-section-title">Carga de Datos</h3>

        <NavItem
          icon={<UploadIcon />}
          label="Mortalidad Materna"
          active={activeView === 'mortalidad'}
          status={fileStatus.mortalidad}
          onClick={() => onNavigate('mortalidad')}
        />

        <NavItem
          icon={<UploadIcon />}
          label="Morbilidad Extrema"
          active={activeView === 'morbilidad'}
          status={fileStatus.morbilidad}
          onClick={() => onNavigate('morbilidad')}
        />
      </nav>

      <div className="sidebar-footer-okd">
        <Avatar letter={user.avatarLetter} />
        <div className="user-info-okd">
          <strong className="user-name-okd" title={user.username}>{user.username}</strong>
          <small className="user-email-okd" title={user.email || 'VidaMaterna Analytics'}>
            {user.email || 'VidaMaterna Analytics'}
          </small>
        </div>
        <button
          className="btn-logout-okd"
          onClick={onLogout}
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
        >
          <LogoutIcon />
        </button>
      </div>
    </aside>
  )
}
