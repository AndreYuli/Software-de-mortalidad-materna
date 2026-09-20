import type { ReactNode } from 'react'

export interface NavItemStatus {
  hasFile?: boolean
  hasError?: boolean
}

export interface NavItemProps {
  icon: ReactNode
  label: string
  active: boolean
  onClick: () => void
  status?: NavItemStatus
  ariaLabel?: string
}

export function NavItem({
  icon,
  label,
  active,
  onClick,
  status,
  ariaLabel,
}: NavItemProps) {
  const isSuccess = status?.hasFile && !status?.hasError
  const isError = Boolean(status?.hasError)

  const extraClass = isError ? 'nav-error' : isSuccess ? 'nav-success' : ''

  return (
    <button
      className={`nav-item-okd ${active ? 'active' : ''} ${extraClass}`.trim()}
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
      aria-label={ariaLabel}
    >
      {icon}
      <span className="nav-item-label-okd">{label}</span>
      {isSuccess && (
        <span className="nav-badge-okd nav-badge-success" aria-label="Archivo cargado correctamente">
          ✓
        </span>
      )}
      {isError && (
        <span className="nav-badge-okd nav-badge-error" aria-label="Error en el archivo cargado">
          !
        </span>
      )}
    </button>
  )
}
