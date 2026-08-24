import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getSankeyAiInsight } from '../../utils/aiChartInsights'

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

function cleanNodeLabel(name: string): string {
  return name.replace(/^\[(Parto|Nivel|Muerte|Origen|Medio|Destino)\]\s*/i, '')
}

function getNodeCategory(name: string): string {
  if (name.startsWith('[Parto]')) return 'Tipo de Parto'
  if (name.startsWith('[Nivel]')) return 'Nivel de Atención'
  if (name.startsWith('[Muerte]')) return 'Momento de Muerte'
  return 'Etapa'
}

function nodeColor(name: string): string {
  if (name.startsWith('[Parto]')) return '#3498db'
  if (name.startsWith('[Nivel]')) return '#f1c40f'
  if (name.startsWith('[Muerte]')) return '#e74c3c'
  return '#3498db'
}

export const SankeyMortalidad: React.FC<SankeyMortalidadProps> = ({ data }) => {
  const insight = useMemo(() => getSankeyAiInsight(data), [data])

  const option = useMemo(() => {
    if (!data || !data.nodos || data.nodos.length === 0 || !data.links || !data.links.source || data.links.source.length === 0) {
      return null
    }

    const nodes = data.nodos.map((name) => ({
      name,
      itemStyle: { color: nodeColor(name) },
    }))

    const links = data.links.source.map((sourceIdx, i) => ({
      source: data.nodos[sourceIdx],
      target: data.nodos[data.links.target[i]],
      value: data.links.value[i],
    }))

    return {
      textStyle: echartsBaseTextStyle(),
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        formatter: (params: any) => {
          if (params.dataType === 'edge') {
            const sourceClean = cleanNodeLabel(params.data.source)
            const targetClean = cleanNodeLabel(params.data.target)
            const sourceCat = getNodeCategory(params.data.source)
            const targetCat = getNodeCategory(params.data.target)
            return `<div style="font-size:12px; padding:2px 4px;">
              <div><b>${sourceCat}:</b> ${sourceClean}</div>
              <div><b>${targetCat}:</b> ${targetClean}</div>
              <div style="margin-top:4px; font-weight:600; color:#3b82f6;">Casos: ${params.data.value}</div>
            </div>`
          }
          const clean = cleanNodeLabel(params.name)
          const cat = getNodeCategory(params.name)
          return `<div style="font-size:12px; padding:2px 4px;">
            <div><b>${cat}:</b> ${clean}</div>
            ${params.value !== undefined ? `<div style="margin-top:4px; font-weight:600;">Casos: ${params.value}</div>` : ''}
          </div>`
        },
      },
      series: [
        {
          type: 'sankey' as const,
          orient: 'horizontal' as const,
          nodeGap: 15,
          nodeWidth: 20,
          data: nodes,
          links,
          lineStyle: { color: 'gradient' as const, opacity: 0.4 },
          label: {
            fontSize: 12,
            formatter: (params: any) => cleanNodeLabel(params.name),
          },
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
        Este diagrama muestra la trayectoria de las pacientes a través del sistema de salud: cómo se relacionan el tipo de parto, el nivel de complejidad donde fueron atendidas y la etapa en que ocurrió el desenlace fatal.
      </p>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '12px', fontSize: '12px', color: '#475569' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#3498db', display: 'inline-block' }} />
          1. Tipo de Parto
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#f1c40f', display: 'inline-block' }} />
          2. Nivel de Atención
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#e74c3c', display: 'inline-block' }} />
          3. Momento de Muerte
        </span>
      </div>
      <ReactECharts option={option} style={{ height: '450px', width: '100%' }} notMerge={true} />
      <ChartAiInsight insight={insight} />
    </div>
  )
}
