import { useCallback, useState } from 'react'
import './StrategicDashboard.css'
import { useAnalysisHomeData } from '../../hooks/dashboard/useAnalysisHomeData'
import { useDashboardMetrics, type Segmento } from '../../hooks/dashboard/useDashboardMetrics'
import { useDashboardCharts } from '../../hooks/dashboard/useDashboardCharts'
import { WelcomeState } from './WelcomeState'
import { DashboardLoadingState } from './DashboardLoadingState'
import { DashboardErrorState } from './DashboardErrorState'
import { DashControlBar } from './DashControlBar'
import { KpiRow } from './KpiRow'
import { TrendChartsRow } from './TrendChartsRow'
import { ClusteringSection } from './ClusteringSection'
import { HeatmapDemoras } from './HeatmapDemoras'
import { SankeyMortalidad } from './SankeyMortalidad'
import { SeveridadFallasMorbilidad } from './SeveridadFallasMorbilidad'
import { AtencionOportunidad } from './AtencionOportunidad'

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
  const [activeTab, setActiveTab] = useState<'panorama' | 'morbilidad' | 'mortalidad' | 'demoras' | 'atencion'>('panorama')

  const handleSegmentoChange = useCallback((value: Segmento) => {
    setSegmento(value)
    if (value !== 'ambos') setClusteringSegment(value)
  }, [])

  const handleExportReport = useCallback(() => {
    alert('Generando reporte epidemiológico para impresión...')
    window.print()
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

  if (!hasData) return <WelcomeState onGoToUpload={onGoToUpload} />
  if (loading) return <DashboardLoadingState />
  if (error) return <DashboardErrorState message={error} />

  return (
    <div className="dashboard-strategic-container">
      <DashControlBar
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

      <div className="dashboard-tabs">
        <button 
          className={`tab-button ${activeTab === 'panorama' ? 'active' : ''}`}
          onClick={() => setActiveTab('panorama')}
        >
          Panorama General
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
        <button 
          className={`tab-button ${activeTab === 'demoras' ? 'active' : ''}`}
          onClick={() => setActiveTab('demoras')}
        >
          Análisis de Demoras
        </button>
        <button 
          className={`tab-button ${activeTab === 'atencion' ? 'active' : ''}`}
          onClick={() => setActiveTab('atencion')}
        >
          Atención y Oportunidad
        </button>
      </div>

      {activeTab === 'panorama' && (
        <>
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

          <TrendChartsRow 
            lineChartData={lineChartData} 
            barChartData={barChartData} 
            demorasChartData={demorasChartData}
            edadChartData={edadChartData}
            momentoChartData={momentoChartData}
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
        <SeveridadFallasMorbilidad
          data={severidadFallasData}
          morbKpis={morbKpis}
          criteriosInclusion={criteriosInclusionData}
          momentoOcurrencia={momentoOcurrenciaData}
          tiempoRemision={tiempoRemisionData}
        />
      )}

      {activeTab === 'mortalidad' && (
        <div className="charts-grid-row">
          <SankeyMortalidad data={sankeyFlujoData} />
        </div>
      )}

      {activeTab === 'demoras' && (
        <div className="charts-grid-row">
          <HeatmapDemoras data={heatmapDemorasData} />
        </div>
      )}

      {activeTab === 'atencion' && (
        <AtencionOportunidad
          kpis={atencionKpis}
          institucionReferencia={institucionReferenciaData}
          obstetricoEdad={obstetricoEdadData}
        />
      )}
    </div>
  )
}
