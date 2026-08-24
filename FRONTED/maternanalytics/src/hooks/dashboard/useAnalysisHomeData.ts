import { useEffect, useState } from 'react'
import { API_URL } from '../../api'
import type { AnalisisCompleto } from '../../types'

export interface ClusteringResult {
  n_clusters?: number
  n_samples?: number
  cluster_sizes?: number[]
  features_used?: string[]
  clusters?: number[]
  pca_2d?: { x: number[]; y: number[] }
  pca_3d?: { x: number[]; y: number[]; z: number[] }
  cluster_profiles?: { cluster_id: number; size: number; features: Record<string, number> }[]
}

export interface UseAnalysisHomeDataParams {
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  filterYear: string
  filterMonth: string
  onAvailableYears: (years: number[]) => void
}

async function fetchAnalisisConClustering(
  analisisId: number,
  suffix: string,
  signal: AbortSignal,
): Promise<{ data: AnalisisCompleto | null; clustering: ClusteringResult | null }> {
  const res = await fetch(`${API_URL}/analisis/${analisisId}/completo/${suffix}`, { signal })
  if (!res.ok) return { data: null, clustering: null }

  const data = await res.json()
  const clusterRes = await fetch(`${API_URL}/analisis/${analisisId}/clustering/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tipo_clustering: 'kmeans', n_clusters: 3 }),
    signal,
  })
  const clustering = clusterRes.ok ? await clusterRes.json() : null
  return { data, clustering }
}

/**
 * Obtiene los datos completos y el clustering de los últimos análisis de
 * mortalidad/morbilidad. Única responsabilidad: fetch + estados de
 * carga/error. No calcula métricas ni arma datasets de gráficas.
 */
export function useAnalysisHomeData({
  latestMortalidad,
  latestMorbilidad,
  filterYear,
  filterMonth,
  onAvailableYears,
}: UseAnalysisHomeDataParams) {
  const [mortalidadData, setMortalidadData] = useState<AnalisisCompleto | null>(null)
  const [morbilidadData, setMorbilidadData] = useState<AnalisisCompleto | null>(null)
  const [mortalidadClustering, setMortalidadClustering] = useState<ClusteringResult | null>(null)
  const [morbilidadClustering, setMorbilidadClustering] = useState<ClusteringResult | null>(null)
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
        const suffix = queryParams.toString() ? `?${queryParams.toString()}` : ''

        const [mort, morb] = await Promise.all([
          latestMortalidad
            ? fetchAnalisisConClustering(latestMortalidad.id, suffix, controller.signal)
            : Promise.resolve({ data: null, clustering: null }),
          latestMorbilidad
            ? fetchAnalisisConClustering(latestMorbilidad.id, suffix, controller.signal)
            : Promise.resolve({ data: null, clustering: null }),
        ])

        if (isMounted) {
          setMortalidadData(mort.data)
          setMorbilidadData(morb.data)
          setMortalidadClustering(mort.clustering)
          setMorbilidadClustering(morb.clustering)

          const years = Array.from(
            new Set([
              ...(mort.data?.anos_disponibles || []),
              ...(morb.data?.anos_disponibles || []),
            ]),
          ).sort((a, b) => b - a)
          onAvailableYears(years)
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError' && isMounted) {
          setError('Error al procesar la información del panel de control.')
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
  }, [latestMortalidad, latestMorbilidad, filterYear, filterMonth, onAvailableYears])

  const hasData = Boolean(latestMortalidad || latestMorbilidad)

  return {
    mortalidadData,
    morbilidadData,
    mortalidadClustering,
    morbilidadClustering,
    loading,
    error,
    hasData,
  }
}
