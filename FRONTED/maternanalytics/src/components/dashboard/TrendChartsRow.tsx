import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { Scale, TooltipItem } from 'chart.js'
import '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getTopCausasAiInsight } from '../../utils/aiChartInsights'
import { wrapLabel, calculateChartHeight } from '../../utils/causasChartLabels'

export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
}

export interface TrendChartsRowProps {
  topCausasMortalidad: TopCausasChartData
  topCausasMorbilidad: TopCausasChartData
}

// Chart.js mide el ancho del eje Y con la fuente aún no completamente
// asentada en el layout inicial, y subestima el ancho real que necesitan
// las etiquetas largas envueltas en varias líneas — recortando el borde
// izquierdo del texto. Se agrega un margen de seguridad fijo tras el
// cálculo automático para evitar el recorte (técnica estándar de Chart.js
// para este problema conocido con etiquetas largas en barras horizontales).
const Y_AXIS_WIDTH_SAFETY_MARGIN = 70

interface CausasBarChartProps {
  title: string
  data: TopCausasChartData
  emptyMessage: string
  insight: string | null
}

function CausasBarChart({ title, data, emptyMessage, insight }: CausasBarChartProps) {
  const chartHeight = useMemo(() => calculateChartHeight(data.labels), [data.labels])

  return (
    <div className="chart-card-col-6">
      <h3 className="chart-card-title">{title}</h3>
      <div style={{ height: `${chartHeight}px` }}>
        {data.values.length > 0 ? (
          <Bar
            data={{
              labels: data.labels.map((l) => wrapLabel(l)),
              datasets: [
                {
                  data: data.values,
                  backgroundColor: data.colors,
                  borderColor: '#475569',
                  borderWidth: 1,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y' as const,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    title: (items: TooltipItem<'bar'>[]) => {
                      const idx = items[0]?.dataIndex
                      return idx !== undefined ? data.labels[idx] : ''
                    },
                  },
                },
              },
              scales: {
                x: { title: { display: true, text: 'Casos' }, ticks: { precision: 0 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: {
                  grid: { display: false },
                  afterFit: (scale: Scale) => {
                    scale.width += Y_AXIS_WIDTH_SAFETY_MARGIN
                  },
                },
              },
            }}
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
            {emptyMessage}
          </div>
        )}
      </div>
      <ChartAiInsight insight={insight} />
    </div>
  )
}

export function TrendChartsRow({ topCausasMortalidad, topCausasMorbilidad }: TrendChartsRowProps) {
  const topCausasMortalidadInsight = useMemo(
    () => getTopCausasAiInsight(topCausasMortalidad.labels, topCausasMortalidad.values, false),
    [topCausasMortalidad],
  )

  const topCausasMorbilidadInsight = useMemo(
    () => getTopCausasAiInsight(topCausasMorbilidad.labels, topCausasMorbilidad.values, true),
    [topCausasMorbilidad],
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="charts-grid-row">
        <CausasBarChart
          title="Top 10 Causas de Mortalidad"
          data={topCausasMortalidad}
          emptyMessage="Sin registros de causas de mortalidad"
          insight={topCausasMortalidadInsight}
        />
        <CausasBarChart
          title="Top 10 Causas de Morbilidad"
          data={topCausasMorbilidad}
          emptyMessage="Sin registros de causas de morbilidad"
          insight={topCausasMorbilidadInsight}
        />
      </div>
    </div>
  )
}
