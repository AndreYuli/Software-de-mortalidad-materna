import { PageSkeleton } from './PageSkeleton'

/** Estado de carga del panel: el mismo esqueleto que usa el resto de la app (una sola apariencia). */
export function DashboardLoadingState() {
  return <PageSkeleton />
}
