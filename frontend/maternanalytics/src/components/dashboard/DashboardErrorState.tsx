import { AlertCircle } from 'lucide-react'

export interface DashboardErrorStateProps {
  message: string
  /** Si se omite, «Reintentar» recarga la página completa. */
  onRetry?: () => void
}

export function DashboardErrorState({ message, onRetry }: DashboardErrorStateProps) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
      <AlertCircle className="size-8 text-red-600" aria-hidden="true" />
      <p role="alert" className="text-sm text-red-700">
        {message}
      </p>
      <button
        type="button"
        onClick={onRetry ?? (() => window.location.reload())}
        className="inline-flex items-center justify-center rounded-lg bg-brand-magenta px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
      >
        Reintentar
      </button>
    </div>
  )
}
