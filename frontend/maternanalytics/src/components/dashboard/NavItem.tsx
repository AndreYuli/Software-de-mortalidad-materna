import type { ReactNode } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'

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
  const isError = Boolean(status?.hasError)
  const isSuccess = Boolean(status?.hasFile) && !isError

  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
      aria-label={ariaLabel}
      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium transition ${
        active ? 'bg-brand-magenta/10 text-brand-magenta' : 'text-slate-600 hover:bg-slate-100'
      }`}
    >
      {icon}
      <span className="flex-1">{label}</span>
      {isSuccess && (
        <CheckCircle
          role="img"
          aria-label="Archivo cargado correctamente"
          className="size-4 shrink-0 text-green-600"
        />
      )}
      {isError && (
        <AlertCircle
          role="img"
          aria-label="Error en el archivo cargado"
          className="size-4 shrink-0 text-red-600"
        />
      )}
    </button>
  )
}
