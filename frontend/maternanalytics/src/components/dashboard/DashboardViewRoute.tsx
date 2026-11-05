import { useOutletContext } from 'react-router-dom'
import type { ActiveView } from '../../hooks/navigation/useActiveView'
import { useDocumentTitle } from '../../hooks/navigation/useDocumentTitle'
import type { DashboardData } from '../../hooks/useDashboardData'
import { ViewRouter } from './ViewRouter'

export interface DashboardOutletContext {
  data: DashboardData
  onNavigate: (view: ActiveView) => void
}

/** Ruta hija del layout DashboardOKD: recibe los datos compartidos por el Outlet. */
export function DashboardViewRoute({ view }: { view: ActiveView }) {
  const TITULOS: Record<ActiveView, string> = {
    analisis: 'Análisis',
    mortalidad: 'Cargar mortalidad',
    morbilidad: 'Cargar morbilidad',
    historial: 'Historial de cargas',
    contexto: 'Contexto del proyecto',
  }
  useDocumentTitle(TITULOS[view])
  const { data, onNavigate } = useOutletContext<DashboardOutletContext>()
  return <ViewRouter activeView={view} data={data} onNavigate={onNavigate} />
}
