import NarrativaIA from '../NarrativaIA'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'

export interface NarrativasResumenProps {
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  segmento: Segmento
  filterYear: string
  filterMonth: string
}

/** Resumen ejecutivo generado por IA local, uno por evento incluido en el segmento activo. */
export function NarrativasResumen({
  latestMortalidad,
  latestMorbilidad,
  segmento,
  filterYear,
  filterMonth,
}: NarrativasResumenProps) {
  const eventos = [
    ...(segmento !== 'morbilidad' && latestMortalidad
      ? [{ id: latestMortalidad.id, nombre: 'Mortalidad' }]
      : []),
    ...(segmento !== 'mortalidad' && latestMorbilidad
      ? [{ id: latestMorbilidad.id, nombre: 'Morbilidad' }]
      : []),
  ]

  return (
    <>
      {eventos.map(({ id, nombre }) => (
        <NarrativaIA
          // Se reinicia al cambiar de análisis o de periodo: la narrativa depende de ambos.
          key={`${id}-${filterYear}-${filterMonth}`}
          analisisId={id}
          tipo="resumen_ejecutivo"
          titulo={`Resumen ejecutivo · ${nombre} (IA local)`}
          filtros={{ year: filterYear, month: filterMonth }}
        />
      ))}
    </>
  )
}
