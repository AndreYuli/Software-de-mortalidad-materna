import '../shared/Spinner.css'
import './ChartState.css'

export function DashboardLoadingState() {
  return (
    <div className="dashboard-loading-state">
      <div className="spinner"></div>
      <p>Generando panel estratégico...</p>
    </div>
  )
}
