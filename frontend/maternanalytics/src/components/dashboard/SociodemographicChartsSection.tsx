import type { ReactNode } from 'react'
import { Bar } from 'react-chartjs-2'
import { BAR_STYLE_HORIZONTAL, BRAND_COLOR, CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { calculateChartHeight, wrapLabel } from '../../utils/causasChartLabels'
import { chartHeightClass } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'

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
  if (!labels.length || total === 0) {
    return (
      <ChartCard title={title}>
        <p className="text-sm text-slate-500">Sin datos suficientes para esta gráfica.</p>
      </ChartCard>
    )
  }

  const insightText = INSIGHTS[insightKey]?.(labels, valores) ?? null

  return (
    <ChartCard title={title} description={`Total: ${total} casos con dato registrado`} insight={insightText}>
      <div className={chartHeightClass(calculateChartHeight(labels))}>
        <Bar
          role="img"
          aria-label={describeSeries(title, labels, valores)}
          data={{
            labels: labels.map((l) => wrapLabel(l)),
            datasets: [
              {
                data: valores,
                backgroundColor: BRAND_COLOR,
                ...BAR_STYLE_HORIZONTAL,
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
                title: { display: true, text: `Casos — ${title}`, font: { family: CHART_FONT_FAMILY } },
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
    </ChartCard>
  )
}

export interface SociodemographicChartsSectionProps {
  data: Record<string, { labels: string[]; valores: number[]; total: number; evento?: string }>
  evento: 'Mortalidad' | 'Morbilidad'
  /** Tarjeta extra que comparte la cuadrícula de dos columnas con las gráficas. */
  leading?: ReactNode
}

export function SociodemographicChartsSection({ data, evento, leading }: SociodemographicChartsSectionProps) {
  const variables: { key: string; label: string }[] = [
    { key: 'zona_residencia', label: TITLES.zona_residencia },
    { key: 'poblacion_vulnerable', label: TITLES.poblacion_vulnerable },
    { key: 'etnia', label: TITLES.etnia },
    { key: 'tipo_afiliacion', label: TITLES.tipo_afiliacion },
  ]

  const hasAnyData = variables.some((v) => data[v.key] && data[v.key].total > 0)

  if (!hasAnyData) {
    return (
      <ChartCard title={`Factores Sociodemográficos (${evento})`}>
        <p className="text-sm text-slate-500">
          No hay datos sociodemográficos disponibles. Suba archivos con las columnas de zona, población vulnerable, etnia y tipo de afiliación.
        </p>
      </ChartCard>
    )
  }

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-xl font-bold text-brand-deep">Factores Sociodemográficos ({evento})</h2>
      <div data-testid="sociodemographic-grid" className="grid gap-3 lg:grid-cols-2">
        {leading}
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
    </section>
  )
}
