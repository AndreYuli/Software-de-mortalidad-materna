import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { Scale, TooltipItem } from 'chart.js'
import { barValueLabelsPlugin } from '../../utils/barValueLabels'
import { BAR_STYLE_HORIZONTAL } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { getTopCausasAiInsight } from '../../utils/aiChartInsights'
import { calculateChartHeight, wrapLabel } from '../../utils/causasChartLabels'
import { chartHeightClass } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'
import { useMediaQuery } from '../../hooks/useMediaQuery'

export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
  /** Registros del evento, para calcular el porcentaje de cada causa. */
  total?: number
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

// En pantallas estrechas las etiquetas se parten antes y se quita el margen fijo del eje Y
// (con ~300 px de gráfica, etiquetas de 45 caracteres más el margen dejaban el eje recortado).
const MAX_LABEL_LEN_DESKTOP = 45
const MAX_LABEL_LEN_NARROW = 16
const NARROW_QUERY = '(max-width: 640px)'

interface CausasBarChartProps {
  title: string
  eyebrow: string
  data: TopCausasChartData
  emptyMessage: string
  insight: string | null
}

function CausasBarChart({ title, eyebrow, data, emptyMessage, insight }: CausasBarChartProps) {
  const narrow = useMediaQuery(NARROW_QUERY)
  const maxLen = narrow ? MAX_LABEL_LEN_NARROW : MAX_LABEL_LEN_DESKTOP
  const plugins = useMemo(() => [barValueLabelsPlugin(data.total ?? 0)], [data.total])
  return (
    <ChartCard title={title} eyebrow={eyebrow} insight={insight}>
      {data.values.length > 0 ? (
        <div className={chartHeightClass(calculateChartHeight(data.labels, maxLen))}>
          <Bar
            plugins={plugins}
            role="img"
            aria-label={describeSeries(title, data.labels, data.values)}
            data={{
              labels: data.labels.map((l) => wrapLabel(l, maxLen)),
              datasets: [
                {
                  data: data.values,
                  backgroundColor: data.colors,
                  ...BAR_STYLE_HORIZONTAL,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y' as const,
              layout: { padding: { right: narrow ? 76 : 84 } },
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    title: (items: TooltipItem<'bar'>[]) => {
                      const idx = items[0]?.dataIndex
                      return idx !== undefined ? wrapLabel(data.labels[idx], maxLen) : ''
                    },
                  },
                },
              },
              scales: {
                x: { title: { display: true, text: 'Casos' }, ticks: { precision: 0 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: {
                  grid: { display: false },
                  // Sin esto Chart.js omite etiquetas cuando las filas quedan juntas (móvil).
                  ticks: { autoSkip: false, font: { size: narrow ? 10 : 12, lineHeight: 1.15 } },
                  afterFit: (scale: Scale) => {
                    if (!narrow) scale.width += Y_AXIS_WIDTH_SAFETY_MARGIN
                  },
                },
              },
            }}
          />
        </div>
      ) : (
        <p className="text-sm text-slate-500">{emptyMessage}</p>
      )}
    </ChartCard>
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
    <section className="flex flex-col gap-4" aria-label="Análisis de causas principales">
      <div>
        <span className="text-xs font-semibold uppercase tracking-wider text-brand-magenta">Priorización clínica</span>
        <h2 className="text-xl font-bold text-brand-deep">Causas principales notificadas</h2>
        <p className="text-sm text-slate-500">
          Compare los diagnósticos líderes por evento antes de pasar a variables sociodemográficas o clínicas.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <CausasBarChart
          eyebrow="Evento 550"
          title="Top 10 Causas de Mortalidad"
          data={topCausasMortalidad}
          emptyMessage="Sin registros de causas de mortalidad"
          insight={topCausasMortalidadInsight}
        />
        <CausasBarChart
          eyebrow="Evento 549"
          title="Top 10 Causas de Morbilidad"
          data={topCausasMorbilidad}
          emptyMessage="Sin registros de causas de morbilidad"
          insight={topCausasMorbilidadInsight}
        />
      </div>
    </section>
  )
}
