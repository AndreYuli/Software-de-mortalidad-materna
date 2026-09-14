import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getTopCausasAiInsight } from '../../utils/aiChartInsights'

export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
}

export interface TrendChartsRowProps {
  topCausasMortalidad: TopCausasChartData
  topCausasMorbilidad: TopCausasChartData
}

const LINE_HEIGHT = 28
const MIN_BAR_HEIGHT = 32
const AXIS_PADDING = 60
const MIN_CHART_HEIGHT = 320

export const wrapLabel = (text: string, maxLen: number = 45): string | string[] => {
  if (text.length <= maxLen) return text
  const words = text.split(' ')
  const lines: string[] = []
  let currentLine = ''
  for (const word of words) {
    if ((currentLine + word).length > maxLen) {
      if (currentLine) lines.push(currentLine.trim())
      currentLine = word + ' '
    } else {
      currentLine += word + ' '
    }
  }
  if (currentLine) lines.push(currentLine.trim())
  return lines
}

export const calculateChartHeight = (labels: string[]): number => {
  if (labels.length === 0) return MIN_CHART_HEIGHT
  const totalBarsHeight = labels.reduce((sum, label) => {
    const wrapped = wrapLabel(label)
    const lineCount = Array.isArray(wrapped) ? wrapped.length : 1
    return sum + MIN_BAR_HEIGHT + lineCount * LINE_HEIGHT
  }, 0)
  return Math.max(MIN_CHART_HEIGHT, AXIS_PADDING + totalBarsHeight)
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
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Top 10 Causas de Mortalidad</h3>
          <div style={{ height: '320px' }}>
            {topCausasMortalidad.values.length > 0 ? (
              <Bar
                data={{
                  labels: topCausasMortalidad.labels.map((l) => wrapLabel(l)),
                  datasets: [
                    {
                      data: topCausasMortalidad.values,
                      backgroundColor: topCausasMortalidad.colors,
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
                    x: { title: { display: true, text: 'Casos' }, ticks: { precision: 0 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { grid: { display: false } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin registros de causas de mortalidad
              </div>
            )}
          </div>
          <ChartAiInsight insight={topCausasMortalidadInsight} />
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Top 10 Causas de Morbilidad</h3>
          <div style={{ height: '320px' }}>
            {topCausasMorbilidad.values.length > 0 ? (
              <Bar
                data={{
                  labels: topCausasMorbilidad.labels.map((l) => wrapLabel(l)),
                  datasets: [
                    {
                      data: topCausasMorbilidad.values,
                      backgroundColor: topCausasMorbilidad.colors,
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
                    x: { title: { display: true, text: 'Casos' }, ticks: { precision: 0 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { grid: { display: false } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin registros de causas de morbilidad
              </div>
            )}
          </div>
          <ChartAiInsight insight={topCausasMorbilidadInsight} />
        </div>
      </div>
    </div>
  )
}
