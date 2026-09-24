import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthUser } from './auth/useAuthUser'
import type { ActiveView } from './navigation/useActiveView'
import { useDashboardTabs } from './navigation/useDashboardTabs'
import type { Segmento } from './dashboard/useDashboardMetrics'
import { useDashboardFilters } from './filters/useDashboardFilters'
import { useFileUpload } from './files/useFileUpload'
import { useAnalysisList, type AnalisisSummary } from './analysis/useAnalysisList'

export type { ActiveView, AnalisisSummary }

export function useDashboardData() {
  const { username, email, avatarLetter } = useAuthUser()
  const navigate = useNavigate()
  const filters = useDashboardFilters()
  // Pestanas y segmento viven aqui (layout) para conservarse al cambiar de ruta.
  const tabs = useDashboardTabs()
  const analysis = useAnalysisList()

  const [segmentoElegido, setSegmento] = useState<Segmento | null>(null)
  const { latestMortalidad, latestMorbilidad } = analysis
  const segmentoPorDefecto: Segmento =
    latestMortalidad && latestMorbilidad
      ? 'ambos'
      : latestMortalidad
        ? 'mortalidad'
        : latestMorbilidad
          ? 'morbilidad'
          : 'ambos'
  const segmento = segmentoElegido ?? segmentoPorDefecto

  const redirectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(
    () => () => {
      if (redirectTimer.current) clearTimeout(redirectTimer.current)
    },
    [],
  )

  const handleUploadSuccess = useCallback(
    async (tipo: 'mortalidad' | 'morbilidad', createdAnalysis: { id: number; tipo: string }) => {
      await analysis.fetchAnalisis(false)
      // Se deja ver el mensaje de exito un momento y luego se navega al panel de analisis.
      redirectTimer.current = setTimeout(() => {
        analysis.setAnalysisType(tipo)
        if (createdAnalysis?.id) {
          analysis.setSelectedAnalisisId(createdAnalysis.id)
        }
        navigate('/dashboard')
      }, 1500)
    },
    [analysis, navigate],
  )

  const mortalidad = useFileUpload('mortalidad', {
    onSuccess: (created) => handleUploadSuccess('mortalidad', created),
  })

  const morbilidad = useFileUpload('morbilidad', {
    onSuccess: (created) => handleUploadSuccess('morbilidad', created),
  })

  return {
    username,
    email,
    avatarLetter,
    segmento,
    setSegmento,
    tabs,
    analysisType: analysis.analysisType,
    selectedAnalisisId: analysis.selectedAnalisisId,
    analisisList: analysis.analisisList,
    mortalidadFile: mortalidad.file,
    mortalidadError: mortalidad.error,
    mortalidadPreview: mortalidad.preview,
    mortalidadValidating: mortalidad.validating,
    mortalidadDone: mortalidad.done,
    mortalidadAnalyzeError: mortalidad.analyzeError,
    morbilidadFile: morbilidad.file,
    morbilidadError: morbilidad.error,
    morbilidadPreview: morbilidad.preview,
    morbilidadValidating: morbilidad.validating,
    morbilidadDone: morbilidad.done,
    morbilidadAnalyzeError: morbilidad.analyzeError,
    analyzing: mortalidad.analyzing || morbilidad.analyzing,
    listLoading: analysis.listLoading,
    listError: analysis.listError,
    refetchAnalisis: analysis.fetchAnalisis,
    latestMortalidad: analysis.latestMortalidad,
    latestMorbilidad: analysis.latestMorbilidad,
    filterYear: filters.filterYear,
    setFilterYear: filters.setFilterYear,
    filterMonth: filters.filterMonth,
    setFilterMonth: filters.setFilterMonth,
    filterWeek: filters.filterWeek,
    setFilterWeek: filters.setFilterWeek,
    filterDay: filters.filterDay,
    setFilterDay: filters.setFilterDay,
    filterEventos: filters.filterEventos,
    setFilterEventos: filters.setFilterEventos,
    availableYears: filters.availableYears,
    setAvailableYears: filters.setAvailableYears,
    handleMortalidadFile: mortalidad.handleFile,
    handleMorbilidadFile: morbilidad.handleFile,
    handleAnalyzeMortalidad: mortalidad.handleAnalyze,
    handleAnalyzeMorbilidad: morbilidad.handleAnalyze,
  }
}

export type DashboardData = ReturnType<typeof useDashboardData>
