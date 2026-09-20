import { useOutletContext } from 'react-router-dom'
import type { ActiveView } from '../../hooks/navigation/useActiveView'
import type { DashboardData } from '../../hooks/useDashboardData'
import { ViewRouter } from './ViewRouter'

export interface DashboardOutletContext {
  data: DashboardData
  onNavigate: (view: ActiveView) => void
}

/** Ruta hija del layout DashboardOKD: recibe los datos compartidos por el Outlet. */
export function DashboardViewRoute({ view }: { view: ActiveView }) {
  const { data, onNavigate } = useOutletContext<DashboardOutletContext>()
  return <ViewRouter activeView={view} data={data} onNavigate={onNavigate} />
}
