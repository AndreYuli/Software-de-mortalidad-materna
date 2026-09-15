import { Bar } from 'react-chartjs-2'
import { CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { wrapLabel, calculateChartHeight } from '../../utils/causasChartLabels'

const SOCIO_PALETTE = [
  '#6366f1',
  '#8b5cf6',
  '#a78bfa',
  '#c4b5fd',
  '#f472b6',
  '#fb923c',
  '#fbbf24',
  '#34d399',
]

const TITLES: Record<string, string> = {
  zona_residencia: 'Zona de Residencia',
  poblacion_vulnerable: 'Población Vulnerable',
  etnia: 'Etnia',
  tipo_afiliacion: 'Tipo de Afiliación',
}

const INSIGHTS: Record<string, (labels: string[], valores: number[]) => string> = {
  zona_residencia: (labels, valores) => {
    if (!labels.length) return 'Sin datos de zona de residencia.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `La zona ${max} concentra la mayor parte de los casos. Revise si hay correlación con tiempos de remisión y acceso a controles prenatales.`
  },
  poblacion_vulnerable: (labels, valores) => {
    if (!labels.length) return 'Sin datos de población vulnerable.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `La categoría "${max}" es la más frecuente. Considere barreras de acceso diferenciadas para este grupo.`
  },
  etnia: (labels, valores) => {
    if (!labels.length) return 'Sin datos de etnia.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `El grupo "${max}" predomina en los registros. Verifique si hay subregistro en comunidades con menor acceso a servicios.`
  },
  tipo_afiliacion: (labels, valores) => {
    if (!labels.length) return 'Sin datos de tipo de afiliación.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `El régimen "${max}" es el más reportado. Analice posibles diferencias en oportunidad y calidad de atención por tipo de afiliación.`
  },
}

function SociodemographicBarChart({
  title,
  insightKey,
  labels,
  valores,
  total,
}: {
  title: string
  insightKey: string
  labels: string[]
  valores: number[]
  total: number
}) {
  const chartHeight = calculateChartHeight(labels)

  if (!labels.length || total === 0) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '32px' }}>
        <h3 className="chart-card-title">{title}</h3>
        <p style={{ color: '#64748b' }}>Sin datos suficientes para esta gráfica.</p>
      </div>
    )
  }

  const insightText = INSIGHTS[insightKey]?.(labels, valores) ?? null

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">{title}</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Total: {total} casos con dato registrado
      </p>
      <div style={{ height: `${chartHeight}px` }}>
        <Bar
          data={{
            labels: labels.map((l) => wrapLabel(l)),
            datasets: [
              {
                data: valores,
                backgroundColor: labels.map((_, i) => SOCIO_PALETTE[i % SOCIO_PALETTE.length]),
                borderColor: '#475569',
                borderWidth: 1,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y' as const,
            plugins: { legend: { display: false } },
            scales: {
              x: {
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                ticks: { precision: 0 },
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
              y: {
                grid: { display: false },
                afterFit: (scale: import('chart.js').Scale) => {
                  scale.width += 70
                },
              },
            },
          }}
        />
      </div>
      <ChartAiInsight insight={insightText} />
    </div>
  )
}

export interface SociodemographicChartsSectionProps {
  data: Record<string, { labels: string[]; valores: number[]; total: number; evento?: string }>
  evento: 'Mortalidad' | 'Morbilidad'
}

export function SociodemographicChartsSection({ data, evento }: SociodemographicChartsSectionProps) {
  const variables: { key: string; label: string }[] = [
    { key: 'zona_residencia', label: TITLES.zona_residencia },
    { key: 'poblacion_vulnerable', label: TITLES.poblacion_vulnerable },
    { key: 'etnia', label: TITLES.etnia },
    { key: 'tipo_afiliacion', label: TITLES.tipo_afiliacion },
  ]

  const hasAnyData = variables.some((v) => data[v.key] && data[v.key].total > 0)

  if (!hasAnyData) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '32px' }}>
        <h3 className="chart-card-title">Factores Sociodemográficos ({evento})</h3>
        <p style={{ color: '#64748b' }}>
          No hay datos sociodemográficos disponibles. Suba archivos con las columnas de zona, población vulnerable, etnia y tipo de afiliación.
        </p>
      </div>
    )
  }

  return (
    <div className="sociodemographic-section">
      <h3 className="chart-card-title" style={{ marginBottom: '16px' }}>
        Factores Sociodemográficos ({evento})
      </h3>
      <div className="charts-grid-row">
        {variables.map((v) => {
          const item = data[v.key]
          if (!item || item.total === 0) return null
          return (
            <SociodemographicBarChart
              key={v.key}
              title={v.label}
              insightKey={v.key}
              labels={item.labels}
              valores={item.valores}
              total={item.total}
            />
          )
        })}
      </div>
    </div>
  )
}
