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
import { ClusteringSection } from './ClusteringSection'
import { HeatmapDemoras } from './HeatmapDemoras'
import { SankeyMortalidad } from './SankeyMortalidad'
import { SeveridadFallasMorbilidad } from './SeveridadFallasMorbilidad'
import { AtencionOportunidad } from './AtencionOportunidad'
import { ExportReportModal } from './ExportReportModal'
import { useDashboardTabs } from '../../hooks/navigation/useDashboardTabs'
import { SubTabs } from './SubTabs'
import { SociodemograficoPendiente } from './SociodemograficoPendiente'
import { getTimelineAiInsight } from '../../utils/aiChartInsights'

export interface AnalysisHomeSectionProps {
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  onGoToUpload: (view: 'mortalidad' | 'morbilidad') => void
  filterYear: string
  filterMonth: string
  availableYears: number[]
  onAvailableYears: (years: number[]) => void
  onYearChange: (year: string) => void
  onMonthChange: (month: string) => void
}

export function AnalysisHomeSection({
  latestMortalidad,
  latestMorbilidad,
  onGoToUpload,
  filterYear,
  filterMonth,
  availableYears,
  onAvailableYears,
  onYearChange,
  onMonthChange,
}: AnalysisHomeSectionProps) {
  const [segmento, setSegmento] = useState<Segmento>(() => {
    if (latestMortalidad && latestMorbilidad) return 'ambos'
    if (latestMortalidad) return 'mortalidad'
    if (latestMorbilidad) return 'morbilidad'
    return 'ambos'
  })
  const [pcaDim, setPcaDim] = useState<'2d' | '3d'>('2d')
  const [clusteringSegment, setClusteringSegment] = useState<'mortalidad' | 'morbilidad'>(() =>
    latestMortalidad ? 'mortalidad' : 'morbilidad',
  )
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const { activeTab, setActiveTab, activeSubTab, setActiveSubTab } = useDashboardTabs()

  const handleSegmentoChange = useCallback((value: Segmento) => {
    setSegmento(value)
    if (value !== 'ambos') setClusteringSegment(value)
  }, [])

  const handleExportReport = useCallback(() => {
    setIsExportModalOpen(true)
  }, [])

  const { mortalidadData, morbilidadData, mortalidadClustering, morbilidadClustering, loading, error, hasData } =
    useAnalysisHomeData({ latestMortalidad, latestMorbilidad, filterYear, filterMonth, onAvailableYears })

  const metrics = useDashboardMetrics({ segmento, mortalidadData, morbilidadData, filterYear, filterMonth })

  const { lineChartData, barChartData, activeClusterData, clusteringChartData, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData } = useDashboardCharts({
    segmento,
    mortalidadData,
    morbilidadData,
    filterYear,
    pcaDim,
    clusteringSegment,
    mortalidadClustering,
    morbilidadClustering,
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
        causas: barChartData.labels,
        valores: barChartData.values,
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
    barChartData,
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
              <h1>Análisis Epidemiológico</h1>
              <p>Panel descriptivo y de inteligencia de salud pública de VidaMaterna</p>
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
            <>
              <TrendChartsRow
                lineChartData={lineChartData}
                barChartData={barChartData}
                demorasChartData={demorasChartData}
                edadChartData={edadChartData}
                momentoChartData={momentoChartData}
                segmento={segmento}
              />

              <ClusteringSection
                segmento={segmento}
                clusteringSegment={clusteringSegment}
                onClusteringSegmentChange={setClusteringSegment}
                pcaDim={pcaDim}
                onPcaDimChange={setPcaDim}
                activeClusterData={activeClusterData}
                clusteringChartData={clusteringChartData}
                latestMortalidad={latestMortalidad}
                latestMorbilidad={latestMorbilidad}
                filterYear={filterYear}
                filterMonth={filterMonth}
              />
            </>
          )}

          {activeTab === 'morbilidad' && (
            <>
              <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

              {activeSubTab === 'sociodemografico' && (
                <SociodemograficoPendiente evento="Morbilidad" />
              )}

              {activeSubTab === 'clinico' && (
                <>
                  <SeveridadFallasMorbilidad
                    data={severidadFallasData}
                    morbKpis={morbKpis}
                    criteriosInclusion={criteriosInclusionData}
                    momentoOcurrencia={momentoOcurrenciaData}
                    tiempoRemision={tiempoRemisionData}
                  />
                  <AtencionOportunidad
                    kpis={atencionKpis}
                    institucionReferencia={institucionReferenciaData}
                    obstetricoEdad={obstetricoEdadData}
                  />
                </>
              )}
            </>
          )}

          {activeTab === 'mortalidad' && (
            <>
              <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

              {activeSubTab === 'sociodemografico' && (
                <SociodemograficoPendiente evento="Mortalidad" />
              )}

              {activeSubTab === 'clinico' && (
                <>
                  <div className="charts-grid-row">
                    <SankeyMortalidad data={sankeyFlujoData} />
                  </div>
                  <div className="charts-grid-row">
                    <HeatmapDemoras data={heatmapDemorasData} />
                  </div>
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
