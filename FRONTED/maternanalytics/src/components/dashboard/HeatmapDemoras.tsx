import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'
import { getCie10Description } from '../../constants/dashboardConstants'
import { ChartAiInsight } from './ChartAiInsight'
import { getHeatmapAiInsight } from '../../utils/aiChartInsights'

export interface HeatmapDemorasProps {
  data: {
    causas: string[]
    demoras: string[]
    valores: number[][]
  } | undefined
}

export const HeatmapDemoras: React.FC<HeatmapDemorasProps> = ({ data }) => {
  const insight = useMemo(() => getHeatmapAiInsight(data), [data])

  const option = useMemo(() => {
    if (!data || !data.causas || data.causas.length === 0) return null

    const cells: [number, number, number][] = []
    let maxValue = -Infinity
    let minValue = Infinity
    data.demoras.forEach((_, yIdx) => {
      data.valores[yIdx].forEach((value, xIdx) => {
        cells.push([xIdx, yIdx, value])
        if (value > maxValue) maxValue = value
        if (value < minValue) minValue = value
      })
    })

    if (maxValue === -Infinity) maxValue = 1
    if (minValue === Infinity) minValue = 0

    // Si todos los valores son altos (ej. 600-880), ajustar el mínimo para dar contraste real
    const rangeDiff = maxValue - minValue
    const visualMin = minValue > 20 && rangeDiff > 0
      ? Math.max(0, Math.floor(minValue - rangeDiff * 0.1))
      : 0

    return {
      textStyle: echartsBaseTextStyle(),
      grid: { top: 20, left: 200, right: 20, bottom: 150 },
      xAxis: {
        type: 'category' as const,
        data: data.causas.map((c) => getCie10Description(c)),
        axisLabel: { rotate: 45, fontSize: 10 },
        splitArea: { show: true },
      },
      yAxis: {
        type: 'category' as const,
        data: data.demoras,
        axisLabel: { fontSize: 12, fontWeight: 600 },
        splitArea: { show: true },
      },
      visualMap: {
        min: visualMin,
        max: maxValue || 1,
        calculable: true,
        orient: 'horizontal' as const,
        left: 'center' as const,
        bottom: 0,
        inRange: {
          color: ['#f8fafc', '#fef3c7', '#fcd34d', '#fb923c', '#ef4444', '#991b1b'],
        },
      },
      series: [
        {
          type: 'heatmap' as const,
          data: cells,
          label: {
            show: true,
            formatter: (params: any) => (params.data[2] > 0 ? String(params.data[2]) : '-'),
            fontSize: 11,
            color: '#1e293b',
          },
          tooltip: {
            formatter: (params: { data: [number, number, number] }) =>
              `<div style="font-size:12px; padding:2px 4px;">
                <div><b>Causa:</b> ${getCie10Description(data.causas[params.data[0]])} (${data.causas[params.data[0]]})</div>
                <div><b>Demora:</b> ${data.demoras[params.data[1]]}</div>
                <div style="margin-top:4px; font-weight:600; color:#e11d48;">Casos con demora: ${params.data[2]}</div>
              </div>`,
          },
        },
      ],
    }
  }, [data])

  if (!option) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Mapa de Calor: Causas vs Demoras</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes para generar el mapa de calor.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Causas CIE-10 Asociadas a Demoras Obstétricas</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Matriz de calor basada en el <b>Modelo de las 4 Demoras Obstétricas</b> (Thaddeus & Maine). Permite identificar qué causas de muerte materna (CIE-10) estuvieron más afectadas por retrasos en el reconocimiento de signos de alarma, toma de decisiones, traslado o atención médica institucional.
      </p>
      <ReactECharts option={option} style={{ height: '550px', width: '100%' }} notMerge={true} />
      <ChartAiInsight insight={insight} />
    </div>
  )
}
