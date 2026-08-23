import { useState, useEffect, useCallback } from 'react'
import { API_URL } from '../../api'

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

  const fetchAnalisis = useCallback(
    async (autoOpenLatest = false) => {
      try {
        const res = await fetch(`${API_URL}/analisis/`)
        console.log('fetchAnalisis res.ok:', res.ok)
        if (res.ok) {
          const data: AnalisisSummary[] = await res.json()
          console.log('fetchAnalisis data:', data)
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
        /* backend puede no estar activo */
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
  }
}
