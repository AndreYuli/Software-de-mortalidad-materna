import { useEffect, useState } from 'react'
import { API_URL, fetchWithTimeout } from '../../api'
import type { AnalisisCompleto } from '../../types'

export interface UseAnalysisHomeDataParams {
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  filterYear: string
  filterMonth: string
  filterWeek: string
  filterDay: string
  onAvailableYears: (years: number[]) => void
}

async function fetchAnalisis(analisisId: number, suffix: string, signal: AbortSignal): Promise<AnalisisCompleto | null> {
  const res = await fetchWithTimeout(`${API_URL}/analisis/${analisisId}/completo/${suffix}`, { signal }, 90_000)
  // Antes devolvía null en silencio y el panel quedaba en ceros sin explicación.
  if (!res.ok) throw new Error(`El análisis ${analisisId} respondió con error ${res.status}.`)
  return res.json()
}

/**
 * Obtiene los datos completos de los últimos análisis de
 * mortalidad/morbilidad. Única responsabilidad: fetch + estados de
 * carga/error. No calcula métricas ni arma datasets de gráficas.
 */
export function useAnalysisHomeData({
  latestMortalidad,
  latestMorbilidad,
  filterYear,
  filterMonth,
  filterWeek,
  filterDay,
  onAvailableYears,
}: UseAnalysisHomeDataParams) {
  const [mortalidadData, setMortalidadData] = useState<AnalisisCompleto | null>(null)
  const [morbilidadData, setMorbilidadData] = useState<AnalisisCompleto | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    const controller = new AbortController()

    const loadDashboardData = async () => {
      if (!latestMortalidad && !latestMorbilidad) {
        setMortalidadData(null)
        setMorbilidadData(null)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const queryParams = new URLSearchParams()
        if (filterYear) queryParams.append('year', filterYear)
        if (filterMonth) queryParams.append('month', filterMonth)
        if (filterWeek) queryParams.append('week', filterWeek)
        if (filterDay) queryParams.append('day', filterDay)
        const suffix = queryParams.toString() ? `?${queryParams.toString()}` : ''

        const [mort, morb] = await Promise.all([
          latestMortalidad ? fetchAnalisis(latestMortalidad.id, suffix, controller.signal) : Promise.resolve(null),
          latestMorbilidad ? fetchAnalisis(latestMorbilidad.id, suffix, controller.signal) : Promise.resolve(null),
        ])

        if (isMounted) {
          setMortalidadData(mort)
          setMorbilidadData(morb)

          const years = Array.from(
            new Set([
              ...(mort?.anos_disponibles || []),
              ...(morb?.anos_disponibles || []),
            ]),
          ).sort((a, b) => b - a)
          onAvailableYears(years)
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError' && isMounted) {
          setError(
            (err as Error).name === 'TimeoutError'
              ? (err as Error).message
              : 'Error al procesar la información del panel de control.',
          )
          console.error(err)
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadDashboardData()
    return () => {
      isMounted = false
      controller.abort()
    }
  }, [latestMortalidad, latestMorbilidad, filterYear, filterMonth, filterWeek, filterDay, onAvailableYears])

  const hasData = Boolean(latestMortalidad || latestMorbilidad)

  return {
    mortalidadData,
    morbilidadData,
    loading,
    error,
    hasData,
  }
}
