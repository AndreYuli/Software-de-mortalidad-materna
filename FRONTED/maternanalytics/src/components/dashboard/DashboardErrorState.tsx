import './ChartState.css'

export interface DashboardErrorStateProps {
  message: string
  /** Si se omite, «Reintentar» recarga la página completa. */
  onRetry?: () => void
}

export function DashboardErrorState({ message, onRetry }: DashboardErrorStateProps) {
  return (
    <div className="dashboard-error-state">
      <p role="alert">❌ {message}</p>
      <button type="button" onClick={onRetry ?? (() => window.location.reload())} className="primary-action-btn">
        Reintentar
      </button>
    </div>
  )
}
