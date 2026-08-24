import 'echarts-gl'
import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getClusteringAiInsight } from '../../utils/aiChartInsights'
import NarrativaIA from '../NarrativaIA'
import type { ClusteringResult } from '../../hooks/dashboard/useAnalysisHomeData'
import type { ClusteringChartData } from '../../hooks/dashboard/useDashboardCharts'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'

export interface ClusteringSectionProps {
  segmento: Segmento
  clusteringSegment: 'mortalidad' | 'morbilidad'
  onClusteringSegmentChange: (segment: 'mortalidad' | 'morbilidad') => void
  pcaDim: '2d' | '3d'
  onPcaDimChange: (dim: '2d' | '3d') => void
  activeClusterData: ClusteringResult | null | undefined
  clusteringChartData: ClusteringChartData | null
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  filterYear: string
  filterMonth: string
}

function build2DOption(data: Extract<ClusteringChartData, { dim: '2d' }>) {
  return {
    textStyle: echartsBaseTextStyle(),
    tooltip: { formatter: (params: { data: { name: string } }) => params.data.name },
    grid: { top: 20, left: 50, right: 20, bottom: 40 },
    xAxis: { type: 'value' as const, name: 'Componente 1', splitLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } } },
    yAxis: { type: 'value' as const, name: 'Componente 2', splitLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } } },
    series: [
      {
        type: 'scatter' as const,
        symbolSize: 12,
        data: data.points.map((p) => ({
          value: [p.x, p.y],
          name: p.label,
          itemStyle: { color: p.color, borderColor: '#fff', borderWidth: 1 },
        })),
      },
    ],
  }
}

function build3DOption(data: Extract<ClusteringChartData, { dim: '3d' }>) {
  return {
    textStyle: echartsBaseTextStyle(),
    tooltip: {},
    grid3D: { boxWidth: 100, boxHeight: 100, boxDepth: 100 },
    xAxis3D: { type: 'value' as const, name: 'PC1' },
    yAxis3D: { type: 'value' as const, name: 'PC2' },
    zAxis3D: { type: 'value' as const, name: 'PC3' },
    series: [
      {
        type: 'scatter3D' as const,
        symbolSize: 8,
        data: data.points.map((p) => ({
          value: [p.x, p.y, p.z],
          name: p.label,
          itemStyle: { color: p.color },
        })),
      },
    ],
  }
}

export function ClusteringSection({
  segmento,
  clusteringSegment,
  onClusteringSegmentChange,
  pcaDim,
  onPcaDimChange,
  activeClusterData,
  clusteringChartData,
  latestMortalidad,
  latestMorbilidad,
  filterYear,
  filterMonth,
}: ClusteringSectionProps) {
  const filtros = { year: filterYear || undefined, month: filterMonth || undefined }

  const option = useMemo(() => {
    if (!clusteringChartData) return null
    return clusteringChartData.dim === '3d' ? build3DOption(clusteringChartData) : build2DOption(clusteringChartData)
  }, [clusteringChartData])

  const insight = useMemo(() => getClusteringAiInsight(activeClusterData), [activeClusterData])

  return (
    <div className="advanced-grid-row">
      <div className="clustering-card-span-8">
        <div className="chart-card-title">
          <span>Modelos de Clustering (PCA)</span>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {segmento === 'ambos' && (
              <div className="mini-cluster-toggles">
                <button
                  className={`btn-mini-toggle ${clusteringSegment === 'mortalidad' ? 'active' : ''}`}
                  onClick={() => onClusteringSegmentChange('mortalidad')}
                  disabled={!latestMortalidad}
                >
                  Mortalidad
                </button>
                <button
                  className={`btn-mini-toggle ${clusteringSegment === 'morbilidad' ? 'active' : ''}`}
                  onClick={() => onClusteringSegmentChange('morbilidad')}
                  disabled={!latestMorbilidad}
                >
                  Morbilidad
                </button>
              </div>
            )}
            <div className="mini-cluster-toggles">
              <button className={`btn-mini-toggle ${pcaDim === '2d' ? 'active' : ''}`} onClick={() => onPcaDimChange('2d')}>
                2D
              </button>
              <button className={`btn-mini-toggle ${pcaDim === '3d' ? 'active' : ''}`} onClick={() => onPcaDimChange('3d')}>
                3D
              </button>
            </div>
          </div>
        </div>

        <div style={{ height: '340px' }}>
          {activeClusterData && option ? (
            <ReactECharts option={option} style={{ height: '100%', width: '100%' }} notMerge={true} />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888', textAlign: 'center', padding: '0 20px' }}>
              Modelo de clustering no disponible.<br/>Se requiere mayor cantidad y variabilidad de datos numéricos.
            </div>
          )}
        </div>
        <ChartAiInsight insight={insight} />
      </div>

      <div className="ai-insight-card-span-4">
        {segmento === 'ambos' ? (
          <>
            {latestMortalidad && (
              <NarrativaIA
                analisisId={latestMortalidad.id}
                tipo="resumen_ejecutivo"
                titulo="Resumen de Hallazgos — Mortalidad"
                filtros={filtros}
              />
            )}
            {latestMorbilidad && (
              <NarrativaIA
                analisisId={latestMorbilidad.id}
                tipo="resumen_ejecutivo"
                titulo="Resumen de Hallazgos — Morbilidad"
                filtros={filtros}
              />
            )}
          </>
        ) : (
          <NarrativaIA
            analisisId={segmento === 'mortalidad' ? latestMortalidad!.id : latestMorbilidad!.id}
            tipo="resumen_ejecutivo"
            titulo="Resumen de Hallazgos"
            filtros={filtros}
          />
        )}
      </div>
    </div>
  )
}
