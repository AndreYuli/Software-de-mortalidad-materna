import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getEdadGestacionalAiInsight } from '../../utils/aiChartInsights'

export interface DistribucionEdadGestacionalData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadGestacionalProps {
  data: DistribucionEdadGestacionalData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const GESTACIONAL_COLORS = ['#dc2626', '#dc2626', '#0066cc', '#dc2626']

export function DistribucionEdadGestacional({ data, evento }: DistribucionEdadGestacionalProps) {
  const insight = useMemo(() => getEdadGestacionalAiInsight(data, evento), [data, evento])

  if (!data || data.labels.length === 0) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Distribución por Edad Gestacional</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes de edad gestacional para generar esta gráfica.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Distribución por Edad Gestacional ({evento})</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Los partos pretérmino (antes de la semana 37) o postérmino (semana 42 en adelante) tienen mayor riesgo de morbilidad y mortalidad materna. El rango a término (37-41 semanas) es el de menor riesgo.
      </p>
      <div style={{ height: '280px' }}>
        <Bar
          data={{
            labels: data.labels,
            datasets: [
              {
                data: data.valores,
                backgroundColor: GESTACIONAL_COLORS,
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
