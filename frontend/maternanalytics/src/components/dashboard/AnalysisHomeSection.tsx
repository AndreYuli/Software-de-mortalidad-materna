import { useCallback, useMemo, useState } from 'react'
import { CalendarClock } from 'lucide-react'
import { useAnalysisHomeData } from '../../hooks/dashboard/useAnalysisHomeData'
import { useDashboardMetrics, type Segmento } from '../../hooks/dashboard/useDashboardMetrics'
import { useDashboardCharts } from '../../hooks/dashboard/useDashboardCharts'
import { WelcomeState } from './WelcomeState'
import { DashboardLoadingState } from './DashboardLoadingState'
import { DashboardErrorState } from './DashboardErrorState'
import { MainTabs } from './MainTabs'
import { FiltersBar } from './FiltersBar'
import { KpiRow } from './KpiRow'
import { TrendChartsRow } from './TrendChartsRow'
import { ExportReportModal } from './ExportReportModal'
import type { useDashboardTabs } from '../../hooks/navigation/useDashboardTabs'
import { SubTabs } from './SubTabs'
import { DistribucionEdadGestacional } from './DistribucionEdadGestacional'
import { DistribucionEdadRiesgo } from './DistribucionEdadRiesgo'
import { SociodemographicChartsSection } from './SociodemographicChartsSection'
import { CruceVariablesSection } from './CruceVariablesSection'
import { NarrativasResumen } from './NarrativasResumen'
import { getTimelineAiInsight } from '../../utils/aiChartInsights'

export interface AnalysisHomeSectionProps {
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  onGoToUpload: (view: 'mortalidad' | 'morbilidad') => void
  listLoading?: boolean
  listError?: string | null
  onRetryList?: () => void
  filterYear: string
  filterMonth: string
  filterWeek: string
  filterDay: string
  availableYears: number[]
  onAvailableYears: (years: number[]) => void
  onYearChange: (year: string) => void
  onMonthChange: (month: string) => void
  onWeekChange: (week: string) => void
  onDayChange: (day: string) => void
  segmento: Segmento
  onSegmentoChange: (value: Segmento) => void
  tabs: ReturnType<typeof useDashboardTabs>
}

export function AnalysisHomeSection({
  latestMortalidad,
  latestMorbilidad,
  onGoToUpload,
  listLoading = false,
  listError = null,
  onRetryList,
  filterYear,
  filterMonth,
  filterWeek,
  filterDay,
  availableYears,
  onAvailableYears,
  onYearChange,
  onMonthChange,
  onWeekChange,
  onDayChange,
  segmento,
  onSegmentoChange,
  tabs,
}: AnalysisHomeSectionProps) {
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const { activeTab, setActiveTab, activeSubTab, setActiveSubTab } = tabs

  const handleExportReport = useCallback(() => {
    setIsExportModalOpen(true)
  }, [])

  const { mortalidadData, morbilidadData, loading, error, hasData } = useAnalysisHomeData({
    latestMortalidad,
    latestMorbilidad,
    filterYear,
    filterMonth,
    filterWeek,
    filterDay,
    onAvailableYears,
  })

  const metrics = useDashboardMetrics({ segmento, mortalidadData, morbilidadData, filterYear, filterMonth })

  const ultimaSemanaReportada = useMemo(() => {
    const candidatos = [mortalidadData?.ultima_semana_reportada, morbilidadData?.ultima_semana_reportada].filter(
      (v): v is { anio: number; semana: number } => Boolean(v),
    )
    if (candidatos.length === 0) return null
    return candidatos.reduce((mas_reciente, actual) =>
      actual.anio > mas_reciente.anio || (actual.anio === mas_reciente.anio && actual.semana > mas_reciente.semana)
        ? actual
        : mas_reciente,
    )
  }, [mortalidadData, morbilidadData])

  const { lineChartData, topCausasMortalidad, topCausasMorbilidad, demorasChartData, edadChartData, severidadFallasData, morbKpis, edadGestacionalMortalidad, edadGestacionalMorbilidad, edadRiesgoMortalidad, edadRiesgoMorbilidad, sociodemograficaMortalidad, sociodemograficaMorbilidad } = useDashboardCharts({
    segmento,
    mortalidadData,
    morbilidadData,
    filterYear,
  })

  const reportExportData = useMemo(() => {
    const aiText = getTimelineAiInsight(lineChartData.labels, lineChartData.series)
    return {
      titulo: 'Informe Epidemiológico de Vigilancia Materna (SIVIGILA)',
      fechaGeneracion: new Date().toLocaleDateString('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }),
      periodo: {
        anio: filterYear,
        mes: filterMonth,
        segmento,
      },
      kpis: {
        totalDefunciones: metrics.totalMortalidad,
        totalMorbilidad: metrics.totalMorbilidad,
        casosTotales: metrics.totalCasos,
        tasaLetalidad: `${metrics.tasaLetalidad}%`,
        promedioEdad: morbKpis?.edadPromedio ? `${Math.round(morbKpis.edadPromedio)} años` : 'N/A',
      },
      evolucionMensual: {
        meses: lineChartData.labels,
        mortalidad: lineChartData.series.find((s) => s.name.toLowerCase().includes('mortalidad'))?.data || [],
        morbilidad: lineChartData.series.find((s) => s.name.toLowerCase().includes('morbilidad'))?.data || [],
      },
      causasPrincipales: {
        causas: [...topCausasMortalidad.labels, ...topCausasMorbilidad.labels],
        valores: [...topCausasMortalidad.values, ...topCausasMorbilidad.values],
      },
      demoras: {
        nombres: demorasChartData.labels,
        valores: demorasChartData.values,
      },
      distribucionEdad: {
        grupos: edadChartData.labels,
        mortalidad: edadChartData.mortalidadValues,
        morbilidad: edadChartData.morbilidadValues,
      },
      fallasOrganicas: severidadFallasData?.fallas,
      aiSummary: aiText || undefined,
    }
  }, [
    filterYear,
    filterMonth,
    segmento,
    metrics,
    lineChartData,
    topCausasMortalidad,
    topCausasMorbilidad,
    demorasChartData,
    edadChartData,
    severidadFallasData,
  ])

  // Mientras se consulta la lista de análisis no se sabe si hay datos: no mostrar «sin datos» (parpadeo)
  // ni presentar una caída del backend como si la base estuviera vacía.
  if (!hasData && listLoading) return <DashboardLoadingState />
  if (!hasData && listError) return <DashboardErrorState message={listError} onRetry={onRetryList} />
  if (!hasData) return <WelcomeState onGoToUpload={onGoToUpload} />
  if (loading) return <DashboardLoadingState />
  if (error) return <DashboardErrorState message={error} />

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-brand-magenta">
          Vigilancia materna SIVIGILA
        </span>
        <h1 className="text-2xl font-bold text-brand-deep">Sistema de análisis epidemiológico</h1>
        <p className="text-sm text-slate-500">
          Lectura técnica de mortalidad materna 550 y morbilidad materna extrema 549
        </p>
        {ultimaSemanaReportada && (
          <p className="inline-flex w-fit items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
            <CalendarClock className="size-4" aria-hidden="true" />
            Última carga: Semana {ultimaSemanaReportada.semana} de {ultimaSemanaReportada.anio}
          </p>
        )}
      </div>

      <MainTabs active={activeTab} onChange={setActiveTab} />

      <FiltersBar
        segmento={segmento}
        onSegmentoChange={onSegmentoChange}
        latestMortalidad={latestMortalidad}
        latestMorbilidad={latestMorbilidad}
        filterYear={filterYear}
        onYearChange={onYearChange}
        availableYears={availableYears}
        filterMonth={filterMonth}
        onMonthChange={onMonthChange}
        filterWeek={filterWeek}
        onWeekChange={onWeekChange}
        filterDay={filterDay}
        onDayChange={onDayChange}
        onExport={handleExportReport}
      />

      <KpiRow
        totalCasos={metrics.totalCasos}
        totalMortalidad={metrics.totalMortalidad}
        totalMorbilidad={metrics.totalMorbilidad}
        tasaLetalidad={metrics.tasaLetalidad}
        curTot={metrics.curTot}
        prevTot={metrics.prevTot}
        yearCompareMort={metrics.yearCompareMort}
        yearCompareMorb={metrics.yearCompareMorb}
        periodo={filterMonth ? 'mes' : 'año'}
      />

      <NarrativasResumen
        latestMortalidad={latestMortalidad}
        latestMorbilidad={latestMorbilidad}
        segmento={segmento}
        filterYear={filterYear}
        filterMonth={filterMonth}
      />

      {activeTab === 'generalidades' && (
        <TrendChartsRow topCausasMortalidad={topCausasMortalidad} topCausasMorbilidad={topCausasMorbilidad} />
      )}

      {activeTab === 'morbilidad' && (
        <>
          <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

          {activeSubTab === 'sociodemografico' && (
            <>
              <DistribucionEdadRiesgo data={edadRiesgoMorbilidad} evento="Morbilidad" />
              <SociodemographicChartsSection data={sociodemograficaMorbilidad} evento="Morbilidad" />
            </>
          )}

          {activeSubTab === 'clinico' && (
            <>
              <DistribucionEdadGestacional data={edadGestacionalMorbilidad} evento="Morbilidad" />
              <CruceVariablesSection analisisId={latestMorbilidad?.id ?? null} evento="Morbilidad" />
            </>
          )}
        </>
      )}

      {activeTab === 'mortalidad' && (
        <>
          <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

          {activeSubTab === 'sociodemografico' && (
            <>
              <DistribucionEdadRiesgo data={edadRiesgoMortalidad} evento="Mortalidad" />
              <SociodemographicChartsSection data={sociodemograficaMortalidad} evento="Mortalidad" />
            </>
          )}

          {activeSubTab === 'clinico' && (
            <>
              <DistribucionEdadGestacional data={edadGestacionalMortalidad} evento="Mortalidad" />
              <CruceVariablesSection analisisId={latestMortalidad?.id ?? null} evento="Mortalidad" />
            </>
          )}
        </>
      )}

      <ExportReportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        reportData={reportExportData}
      />
    </div>
  )
}
