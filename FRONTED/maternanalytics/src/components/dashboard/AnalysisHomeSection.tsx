import { useCallback, useMemo, useState } from 'react'
import './StrategicDashboard.css'
import { useAnalysisHomeData } from '../../hooks/dashboard/useAnalysisHomeData'
import { useDashboardMetrics, type Segmento } from '../../hooks/dashboard/useDashboardMetrics'
import { useDashboardCharts } from '../../hooks/dashboard/useDashboardCharts'
import { WelcomeState } from './WelcomeState'
import { DashboardLoadingState } from './DashboardLoadingState'
import { DashboardErrorState } from './DashboardErrorState'
import { FiltersSidebar } from './FiltersSidebar'
import { KpiRow } from './KpiRow'
import { TrendChartsRow } from './TrendChartsRow'
import { ExportReportModal } from './ExportReportModal'
import { useDashboardTabs } from '../../hooks/navigation/useDashboardTabs'
import { SubTabs } from './SubTabs'
import { DistribucionEdadGestacional } from './DistribucionEdadGestacional'
import { DistribucionEdadRiesgo } from './DistribucionEdadRiesgo'
import { SociodemographicChartsSection } from './SociodemographicChartsSection'
import { CruceVariablesSection } from './CruceVariablesSection'
import { getTimelineAiInsight } from '../../utils/aiChartInsights'

export interface AnalysisHomeSectionProps {
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  onGoToUpload: (view: 'mortalidad' | 'morbilidad') => void
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
}

export function AnalysisHomeSection({
  latestMortalidad,
  latestMorbilidad,
  onGoToUpload,
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
}: AnalysisHomeSectionProps) {
  const [segmento, setSegmento] = useState<Segmento>(() => {
    if (latestMortalidad && latestMorbilidad) return 'ambos'
    if (latestMortalidad) return 'mortalidad'
    if (latestMorbilidad) return 'morbilidad'
    return 'ambos'
  })
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const { activeTab, setActiveTab, activeSubTab, setActiveSubTab } = useDashboardTabs()

  const handleSegmentoChange = useCallback((value: Segmento) => {
    setSegmento(value)
  }, [])

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

  if (!hasData) return <WelcomeState onGoToUpload={onGoToUpload} />
  if (loading) return <DashboardLoadingState />
  if (error) return <DashboardErrorState message={error} />

  return (
    <div className="dashboard-strategic-container">
      <div className="dashboard-analysis-layout">
        <div className="dashboard-analysis-main">
          <div className="dashboard-analysis-header">
            <div className="dash-control-title">
              <span className="dash-control-eyebrow">Vigilancia materna SIVIGILA</span>
              <h1>Sistema de análisis epidemiológico</h1>
              <p>Lectura técnica de mortalidad materna 550 y morbilidad materna extrema 549</p>
              {ultimaSemanaReportada && (
                <p className="dash-ultima-semana">
                  Última carga: Semana {ultimaSemanaReportada.semana} de {ultimaSemanaReportada.anio}
                </p>
              )}
            </div>

            <div className="dashboard-tabs">
              <button
                className={`tab-button ${activeTab === 'generalidades' ? 'active' : ''}`}
                onClick={() => setActiveTab('generalidades')}
              >
                Generalidades
              </button>
              <button
                className={`tab-button ${activeTab === 'morbilidad' ? 'active' : ''}`}
                onClick={() => setActiveTab('morbilidad')}
              >
                Morbilidad (Ev. 549)
              </button>
              <button
                className={`tab-button ${activeTab === 'mortalidad' ? 'active' : ''}`}
                onClick={() => setActiveTab('mortalidad')}
              >
                Mortalidad (Ev. 550)
              </button>
            </div>
          </div>

          <KpiRow
            totalCasos={metrics.totalCasos}
            totalMortalidad={metrics.totalMortalidad}
            totalMorbilidad={metrics.totalMorbilidad}
            tasaLetalidad={metrics.tasaLetalidad}
            curTot={metrics.curTot}
            prevTot={metrics.prevTot}
            yearCompareMort={metrics.yearCompareMort}
            yearCompareMorb={metrics.yearCompareMorb}
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
        </div>

        <FiltersSidebar
          segmento={segmento}
          onSegmentoChange={handleSegmentoChange}
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
      </div>

      <ExportReportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        reportData={reportExportData}
      />
    </div>
  )
}
