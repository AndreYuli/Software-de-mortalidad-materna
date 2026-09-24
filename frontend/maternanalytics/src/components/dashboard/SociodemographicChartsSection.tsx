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

function normalizeSociodemographicSeries(labels: unknown, valores: unknown) {
  const safeLabels: string[] = Array.isArray(labels)
    ? labels
        .map((label) => (typeof label === 'string' ? label.trim() : String(label ?? '').trim()))
        .filter((label) => label.length > 0)
    : []

  const safeValues: number[] = Array.isArray(valores)
    ? valores.map((value) => Number(value)).filter((value) => Number.isFinite(value))
    : []

  const pairs = safeLabels
    .map((label, index) => ({ label, value: safeValues[index] }))
    .filter(({ value }) => Number.isFinite(value))

  return {
    labels: pairs.map((pair) => pair.label),
    valores: pairs.map((pair) => pair.value),
  }
}

const INSIGHTS: Record<string, (labels: string[], valores: number[]) => string> = {
  zona_residencia: (labels, valores) => {
    if (!labels.length) return 'Sin datos de zona de residencia.'
    const maxValue = Math.max(...valores)
    const maxLabel = labels[valores.indexOf(maxValue)] ?? labels[0]
    return `La zona ${maxLabel} concentra la mayor parte de los casos. Revise si hay correlación con tiempos de remisión y acceso a controles prenatales.`
  },
  poblacion_vulnerable: (labels, valores) => {
    if (!labels.length) return 'Sin datos de población vulnerable.'
    const maxValue = Math.max(...valores)
    const maxLabel = labels[valores.indexOf(maxValue)] ?? labels[0]
    return `La categoría "${maxLabel}" es la más frecuente. Considere barreras de acceso diferenciadas para este grupo.`
  },
  etnia: (labels, valores) => {
    if (!labels.length) return 'Sin datos de etnia.'
    const maxValue = Math.max(...valores)
    const maxLabel = labels[valores.indexOf(maxValue)] ?? labels[0]
    return `El grupo "${maxLabel}" predomina en los registros. Verifique si hay subregistro en comunidades con menor acceso a servicios.`
  },
  tipo_afiliacion: (labels, valores) => {
    if (!labels.length) return 'Sin datos de tipo de afiliación.'
    const maxValue = Math.max(...valores)
    const maxLabel = labels[valores.indexOf(maxValue)] ?? labels[0]
    return `El régimen "${maxLabel}" es el más reportado. Analice posibles diferencias en oportunidad y calidad de atención por tipo de afiliación.`
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
  const safeSeries = normalizeSociodemographicSeries(labels, valores)

  if (!safeSeries.labels.length || total === 0 || safeSeries.valores.length === 0) {
    return (
      <ChartCard title={title}>
        <p className="text-sm text-slate-500">Sin datos suficientes para esta gráfica.</p>
      </ChartCard>
    )
  }

  const insightText = INSIGHTS[insightKey]?.(safeSeries.labels, safeSeries.valores) ?? null

  return (
    <ChartCard title={title} description={`Total: ${total} casos con dato registrado`} insight={insightText}>
      <div className={chartHeightClass(calculateChartHeight(safeSeries.labels))}>
        <Bar
          role="img"
          aria-label={describeSeries(title, safeSeries.labels, safeSeries.valores)}
          data={{
            labels: safeSeries.labels.map((l) => wrapLabel(l)),
            datasets: [
              {
                data: safeSeries.valores,
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

  const hasAnyData = variables.some((v) => {
    const item = data[v.key]
    if (!item || Number(item.total) <= 0) return false
    const safeSeries = normalizeSociodemographicSeries(item.labels, item.valores)
    return safeSeries.labels.length > 0 && safeSeries.valores.length > 0
  })

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
          if (!item || Number(item.total) <= 0) return null
          const safeSeries = normalizeSociodemographicSeries(item.labels, item.valores)
          if (!safeSeries.labels.length || !safeSeries.valores.length) return null

          return (
            <SociodemographicBarChart
              key={v.key}
              title={v.label}
              insightKey={v.key}
              labels={safeSeries.labels}
              valores={safeSeries.valores}
              total={item.total}
            />
          )
        })}
      </div>
    </section>
  )
}
