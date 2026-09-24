import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { BAR_STYLE_VERTICAL, CHART_FONT_FAMILY, STATUS_COLORS } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { getEdadRiesgoAiInsight } from '../../utils/aiChartInsights'
import { wrapLabel } from '../../utils/causasChartLabels'
import { CHART_HEIGHT_FIXED } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'

export interface DistribucionEdadRiesgoData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadRiesgoProps {
  data: DistribucionEdadRiesgoData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const RISK_COLORS = [STATUS_COLORS.risk, STATUS_COLORS.safe, STATUS_COLORS.risk]

export function DistribucionEdadRiesgo({ data, evento }: DistribucionEdadRiesgoProps) {
  // El backend devuelve {} si no puede calcular la distribución. Normalizar
  // esa respuesta evita que el cambio de pestaña rompa el dashboard.
  const chartData =
    data && Array.isArray(data.labels) && Array.isArray(data.valores) && typeof data.total === 'number'
      ? data
      : null
  const insight = useMemo(() => getEdadRiesgoAiInsight(chartData, evento), [chartData, evento])

  if (!chartData || chartData.labels.length === 0 || chartData.valores.length === 0 || chartData.total === 0) {
    return (
      <ChartCard title="Distribución por Edad y Riesgo Obstétrico">
        <p className="text-sm text-slate-500">No hay datos suficientes de edad para generar esta gráfica.</p>
      </ChartCard>
    )
  }

  const title = `Distribución por Edad y Riesgo Obstétrico (${evento})`

  return (
    <ChartCard
      title={title}
      description="Las mujeres menores de 19 años o de 35 años en adelante tienen mayor riesgo de morbilidad y mortalidad materna."
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
                backgroundColor: RISK_COLORS,
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
