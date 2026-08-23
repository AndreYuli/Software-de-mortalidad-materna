import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'

export interface HeatmapDemorasProps {
  data: {
    causas: string[]
    demoras: string[]
    valores: number[][]
  } | undefined
}

export const HeatmapDemoras: React.FC<HeatmapDemorasProps> = ({ data }) => {
  const option = useMemo(() => {
    if (!data || !data.causas || data.causas.length === 0) return null

    const cells: [number, number, number][] = []
    let maxValue = 0
    data.demoras.forEach((_, yIdx) => {
      data.valores[yIdx].forEach((value, xIdx) => {
        cells.push([xIdx, yIdx, value])
        if (value > maxValue) maxValue = value
      })
    })

    return {
      textStyle: echartsBaseTextStyle(),
      grid: { top: 20, left: 200, right: 20, bottom: 150 },
      xAxis: {
        type: 'category' as const,
        data: data.causas,
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
        min: 0,
        max: maxValue || 1,
        calculable: true,
        orient: 'horizontal' as const,
        left: 'center' as const,
        bottom: 0,
        inRange: { color: ['#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d'] },
      },
      series: [
        {
          type: 'heatmap' as const,
          data: cells,
          tooltip: {
            formatter: (params: { data: [number, number, number] }) =>
              `Causa: ${data.causas[params.data[0]]}<br/>Demora: ${data.demoras[params.data[1]]}<br/>Casos: ${params.data[2]}`,
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
      <ReactECharts option={option} style={{ height: '550px', width: '100%' }} notMerge={true} />
    </div>
  )
}
