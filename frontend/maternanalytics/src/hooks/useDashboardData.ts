import { useCallback } from 'react'
import { useAuthUser } from './auth/useAuthUser'
import { useActiveView, type ActiveView } from './navigation/useActiveView'
import { useDashboardFilters } from './filters/useDashboardFilters'
import { useFileUpload } from './files/useFileUpload'
import { useAnalysisList, type AnalisisSummary } from './analysis/useAnalysisList'

export type { ActiveView, AnalisisSummary }

export function useDashboardData() {
  const { username, email, avatarLetter } = useAuthUser()
  const { activeView, setActiveView } = useActiveView('analisis')
  const filters = useDashboardFilters()

  const handleAutoOpen = useCallback(() => {
    setActiveView('analisis')
  }, [setActiveView])

  const analysis = useAnalysisList(handleAutoOpen)

  const handleUploadSuccess = useCallback(
    async (tipo: 'mortalidad' | 'morbilidad', createdAnalysis: { id: number; tipo: string }) => {
      await analysis.fetchAnalisis(false)
      setTimeout(() => {
        setActiveView('analisis')
        analysis.setAnalysisType(tipo)
        if (createdAnalysis?.id) {
          analysis.setSelectedAnalisisId(createdAnalysis.id)
        }
      }, 1500)
    },
    [analysis, setActiveView],
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
    activeView,
    setActiveView,
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
