import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'

export interface SankeyMortalidadProps {
  data: {
    nodos: string[]
    links: {
      source: number[]
      target: number[]
      value: number[]
    }
  } | undefined
}

function nodeColor(name: string): string {
  if (name.startsWith('[Parto]')) return '#3498db'
  if (name.startsWith('[Nivel]')) return '#f1c40f'
  if (name.startsWith('[Muerte]')) return '#e74c3c'
  return '#3498db'
}

export const SankeyMortalidad: React.FC<SankeyMortalidadProps> = ({ data }) => {
  const option = useMemo(() => {
    if (!data || !data.nodos || data.nodos.length === 0) return null

    const nodes = data.nodos.map((name) => ({ name, itemStyle: { color: nodeColor(name) } }))
    const links = data.links.source.map((sourceIdx, i) => ({
      source: data.nodos[sourceIdx],
      target: data.nodos[data.links.target[i]],
      value: data.links.value[i],
    }))

    return {
      textStyle: echartsBaseTextStyle(),
      series: [
        {
          type: 'sankey' as const,
          orient: 'horizontal' as const,
          nodeGap: 15,
          nodeWidth: 20,
          data: nodes,
          links,
          lineStyle: { color: 'gradient' as const, opacity: 0.4 },
          label: { fontSize: 12 },
        },
      ],
    }
  }, [data])

  if (!option) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Flujo de Atención Clínica</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes para generar el diagrama Sankey.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Flujo de Atención: Tipo de Parto → Nivel de Atención → Momento de Muerte</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Este diagrama muestra cómo se distribuyeron las gestantes desde el tipo de parto, pasando por el nivel de atención donde fueron atendidas, hasta el momento en que ocurrió la muerte.
      </p>
      <ReactECharts option={option} style={{ height: '450px', width: '100%' }} notMerge={true} />
    </div>
  )
}
