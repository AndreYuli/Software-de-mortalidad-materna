import './ChartState.css'

export interface DashboardErrorStateProps {
  message: string
}

export function DashboardErrorState({ message }: DashboardErrorStateProps) {
  return (
    <div className="dashboard-error-state">
      <p>❌ {message}</p>
      <button onClick={() => window.location.reload()} className="primary-action-btn">
        Reintentar
      </button>
    </div>
  )
}
