import { useCallback, useMemo } from 'react'
import type { AnalisisCompleto } from '../../types'

export type Segmento = 'ambos' | 'mortalidad' | 'morbilidad'

export interface CompareResult {
  cur: number
  prev: number
}

export interface UseDashboardMetricsParams {
  segmento: Segmento
  mortalidadData: AnalisisCompleto | null
  morbilidadData: AnalisisCompleto | null
  filterYear: string
  filterMonth: string
}

function getMonthlyCompare(
  dist: Record<string, Record<string, number>> | undefined,
  y: string,
  m: string,
): CompareResult | null {
  if (!dist || !y) return null
  const currentYear = String(y)
  const currentMonth = String(m)

  let cur: number
  let prev: number

  if (m) {
    const mInt = parseInt(m)
    cur = dist[currentYear]?.[currentMonth] || 0

    let prevYear = currentYear
    let prevMonth = String(mInt - 1)
    if (mInt === 1) {
      prevYear = String(parseInt(currentYear) - 1)
      prevMonth = '12'
    }
    prev = dist[prevYear]?.[prevMonth] || 0
  } else {
    cur = Object.values(dist[currentYear] || {}).reduce((a, b) => a + b, 0)
    const prevYear = String(parseInt(currentYear) - 1)
    prev = Object.values(dist[prevYear] || {}).reduce((a, b) => a + b, 0)
  }

  return { cur, prev }
}

/**
 * Calcula los KPIs y comparativos de tendencia del panel. Única
 * responsabilidad: aritmética derivada de los datos ya cargados, sin fetch
 * ni JSX.
 */
export function useDashboardMetrics({
  segmento,
  mortalidadData,
  morbilidadData,
  filterYear,
  filterMonth,
}: UseDashboardMetricsParams) {
  const totalMortalidad = useMemo(
    () =>
      (segmento === 'ambos' || segmento === 'mortalidad') && mortalidadData
        ? mortalidadData.estadisticas_basicas?.total_casos || 0
        : 0,
    [segmento, mortalidadData],
  )

  const totalMorbilidad = useMemo(
    () =>
      (segmento === 'ambos' || segmento === 'morbilidad') && morbilidadData
        ? morbilidadData.estadisticas_basicas?.total_casos || 0
        : 0,
    [segmento, morbilidadData],
  )

  const totalCasos = useMemo(() => totalMortalidad + totalMorbilidad, [totalMortalidad, totalMorbilidad])

  const tasaLetalidad = useMemo(
    () => (totalCasos > 0 ? (totalMortalidad / totalCasos * 100).toFixed(1) : '0'),
    [totalCasos, totalMortalidad],
  )

  const compareFor = useCallback(
    (dist: Record<string, Record<string, number>> | undefined) => getMonthlyCompare(dist, filterYear, filterMonth),
    [filterYear, filterMonth],
  )

  const yearCompareMort = useMemo(
    () => compareFor(mortalidadData?.distribucion_mensual),
    [compareFor, mortalidadData?.distribucion_mensual],
  )
  const yearCompareMorb = useMemo(
    () => compareFor(morbilidadData?.distribucion_mensual),
    [compareFor, morbilidadData?.distribucion_mensual],
  )

  const curTot = useMemo(
    () => (yearCompareMort?.cur || 0) + (yearCompareMorb?.cur || 0),
    [yearCompareMort, yearCompareMorb],
  )
  const prevTot = useMemo(
    () => (yearCompareMort?.prev || 0) + (yearCompareMorb?.prev || 0),
    [yearCompareMort, yearCompareMorb],
  )

  return {
    totalMortalidad,
    totalMorbilidad,
    totalCasos,
    tasaLetalidad,
    yearCompareMort,
    yearCompareMorb,
    curTot,
    prevTot,
  }
}
