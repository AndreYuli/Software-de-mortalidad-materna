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

// Empíricamente, el ancho automático que Chart.js calcula para el eje Y
// queda corto para etiquetas largas envueltas en varias líneas y recorta
// el borde izquierdo del texto (verificado visualmente con datos reales;
// no es una causa raíz confirmada en el código fuente de Chart.js). Se
// agrega un margen fijo tras el cálculo automático como workaround.
// Verificado sin recorte a 1600px y 1920px (anchos de escritorio
// habituales); a ~1280px puede seguir quedando un recorte residual menor
// — pendiente si se necesita soportar pantallas más angostas.
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
