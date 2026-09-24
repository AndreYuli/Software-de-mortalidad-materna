import { useState, useEffect, useCallback } from 'react'
import { API_URL, describeNetworkError, fetchWithTimeout } from '../../api'

export interface AnalisisSummary {
  id: number
  tipo: string
  total_registros?: number
}

export function useAnalysisList(onAutoOpen?: (tipo: string, id: number) => void) {
  const [analisisList, setAnalisisList] = useState<AnalisisSummary[]>([])
  const [selectedAnalisisId, setSelectedAnalisisId] = useState<number | null>(null)
  const [analysisType, setAnalysisType] = useState<string>('mortalidad')
  const [hasAutoOpenedLatest, setHasAutoOpenedLatest] = useState(false)
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)

  const fetchAnalisis = useCallback(
    async (autoOpenLatest = false) => {
      try {
        const res = await fetchWithTimeout(`${API_URL}/analisis/`)
        setListError(res.ok ? null : 'No se pudo cargar la lista de análisis. Intenta de nuevo.')
        if (res.ok) {
          const data: AnalisisSummary[] = await res.json()
          setAnalisisList(data)

          const latestMortalidad = data.find((item) => item.tipo === 'mortalidad')
          const latestMorbilidad = data.find((item) => item.tipo === 'morbilidad')

          if (autoOpenLatest && !hasAutoOpenedLatest && !selectedAnalisisId && data.length > 0) {
            const preferredAnalysis = latestMortalidad || latestMorbilidad || data[0]
            setSelectedAnalisisId(preferredAnalysis.id)
            setAnalysisType(preferredAnalysis.tipo)
            setHasAutoOpenedLatest(true)
            if (onAutoOpen) {
              onAutoOpen(preferredAnalysis.tipo, preferredAnalysis.id)
            }
          }
        }
      } catch (e) {
        console.error('Error fetching analisis:', e)
        setListError(describeNetworkError(e, 'No se pudo conectar con el servidor. Verifica que el backend esté activo.'))
      } finally {
        setListLoading(false)
      }
    },
    [hasAutoOpenedLatest, onAutoOpen, selectedAnalisisId],
  )

  useEffect(() => {
    fetchAnalisis(true)
  }, [fetchAnalisis])

  const latestMortalidad = analisisList.find((item) => item.tipo === 'mortalidad') || null
  const latestMorbilidad = analisisList.find((item) => item.tipo === 'morbilidad') || null

  return {
    analisisList,
    setAnalisisList,
    selectedAnalisisId,
    setSelectedAnalisisId,
    analysisType,
    setAnalysisType,
    latestMortalidad,
    latestMorbilidad,
    fetchAnalisis,
    listLoading,
    listError,
  }
}
