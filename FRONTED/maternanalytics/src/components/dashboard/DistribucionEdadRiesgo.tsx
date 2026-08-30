import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getEdadRiesgoAiInsight } from '../../utils/aiChartInsights'

export interface DistribucionEdadRiesgoData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadRiesgoProps {
  data: DistribucionEdadRiesgoData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const RISK_COLORS = ['#dc2626', '#0066cc', '#dc2626']

export function DistribucionEdadRiesgo({ data, evento }: DistribucionEdadRiesgoProps) {
  const insight = useMemo(() => getEdadRiesgoAiInsight(data, evento), [data, evento])

  if (!data || data.labels.length === 0) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Distribución por Edad y Riesgo Obstétrico</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes de edad para generar esta gráfica.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Distribución por Edad y Riesgo Obstétrico ({evento})</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Las mujeres menores de 19 años o de 35 años en adelante tienen mayor riesgo de morbilidad y mortalidad materna.
      </p>
      <div style={{ height: '280px' }}>
        <Bar
          data={{
            labels: data.labels,
            datasets: [
              {
                data: data.valores,
                backgroundColor: RISK_COLORS,
                borderColor: '#475569',
                borderWidth: 1,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false } },
              y: {
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
            },
          }}
        />
      </div>
      <ChartAiInsight insight={insight} />
    </div>
  )
}
