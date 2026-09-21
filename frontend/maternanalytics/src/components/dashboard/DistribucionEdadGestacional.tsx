import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { BAR_STYLE_VERTICAL, CHART_FONT_FAMILY, STATUS_COLORS } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { getEdadGestacionalAiInsight } from '../../utils/aiChartInsights'
import { wrapLabel } from '../../utils/causasChartLabels'
import { CHART_HEIGHT_FIXED } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'

export interface DistribucionEdadGestacionalData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadGestacionalProps {
  data: DistribucionEdadGestacionalData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const GESTACIONAL_COLORS = [STATUS_COLORS.risk, STATUS_COLORS.risk, STATUS_COLORS.safe, STATUS_COLORS.risk]

export function DistribucionEdadGestacional({ data, evento }: DistribucionEdadGestacionalProps) {
  // El backend usa {} para indicar que no pudo calcular esta distribución.
  // No debe convertirse en un error de renderizado del dashboard.
  const chartData =
    data && Array.isArray(data.labels) && Array.isArray(data.valores) && typeof data.total === 'number'
      ? data
      : null
  const insight = useMemo(() => getEdadGestacionalAiInsight(chartData, evento), [chartData, evento])

  if (!chartData || chartData.labels.length === 0 || chartData.valores.length === 0 || chartData.total === 0) {
    return (
      <ChartCard title="Distribución por Edad Gestacional">
        <p className="text-sm text-slate-500">No hay datos suficientes de edad gestacional para generar esta gráfica.</p>
      </ChartCard>
    )
  }

  const title = `Distribución por Edad Gestacional (${evento})`

  return (
    <ChartCard
      title={title}
      description="Los partos pretérmino (antes de la semana 37) o postérmino (semana 42 en adelante) tienen mayor riesgo de morbilidad y mortalidad materna. El rango a término (37-41 semanas) es el de menor riesgo."
      insight={insight}
    >
      <div className={CHART_HEIGHT_FIXED}>
        <Bar
          role="img"
          aria-label={describeSeries(title, chartData.labels, chartData.valores)}
          data={{
            labels: chartData.labels.map((l) => wrapLabel(l)),
            datasets: [
              {
                data: chartData.valores,
                backgroundColor: GESTACIONAL_COLORS,
                ...BAR_STYLE_VERTICAL,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: {
                grid: { display: false },
                ticks: {
                  font: { family: CHART_FONT_FAMILY, size: 11 },
                  maxRotation: 0,
                },
              },
              y: {
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                ticks: { precision: 0 },
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
            },
          }}
        />
      </div>
    </ChartCard>
  )
}
