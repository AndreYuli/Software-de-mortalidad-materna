import { useMemo } from 'react'
import { Line, Bar, Pie } from 'react-chartjs-2'
import { CHART_COLORS, CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import {
  getTimelineAiInsight,
  getTopCausasAiInsight,
  getDemorasAiInsight,
  getEdadAiInsight,
  getMomentoAiInsight,
} from '../../utils/aiChartInsights'

export interface TrendChartsRowProps {
  lineChartData: { labels: string[]; series: { name: string; color: string; data: number[] }[] }
  barChartData: { labels: string[]; values: number[]; colors: string[] }
  demorasChartData: { labels: string[]; values: number[] }
  edadChartData: { labels: string[]; mortalidadValues: number[]; morbilidadValues: number[] }
  momentoChartData: { labels: string[]; mortalidadValues: number[]; morbilidadValues: number[] }
  segmento?: string
}

const wrapLabel = (text: string, maxLen: number = 45): string | string[] => {
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
  if (lines.length > 2) return [lines[0], lines[1] + '...']
  return lines
}

const legendBottom = {
  legend: { position: 'bottom' as const, labels: { font: { family: CHART_FONT_FAMILY } } },
}

export function TrendChartsRow({
  lineChartData,
  barChartData,
  demorasChartData,
  edadChartData,
  momentoChartData,
  segmento,
}: TrendChartsRowProps) {
  const barTitle = segmento === 'morbilidad' ? 'Top 5 Criterios Principales' : 'Top 5 Causas Principales'

  const timelineInsight = useMemo(
    () => getTimelineAiInsight(lineChartData.labels, lineChartData.series),
    [lineChartData],
  )

  const topCausasInsight = useMemo(
    () => getTopCausasAiInsight(barChartData.labels, barChartData.values, segmento === 'morbilidad'),
    [barChartData, segmento],
  )

  const demorasInsight = useMemo(
    () => getDemorasAiInsight(demorasChartData.labels, demorasChartData.values),
    [demorasChartData],
  )

  const edadInsight = useMemo(
    () => getEdadAiInsight(edadChartData.labels, edadChartData.mortalidadValues, edadChartData.morbilidadValues),
    [edadChartData],
  )

  const momentoInsight = useMemo(
    () => getMomentoAiInsight(momentoChartData.labels, momentoChartData.mortalidadValues, momentoChartData.morbilidadValues),
    [momentoChartData],
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="charts-grid-row">
        <div className="chart-card-col-12">
          <h3 className="chart-card-title">Evolución Temporal de Casos</h3>
          <div style={{ height: '320px' }}>
            {lineChartData.series.length > 0 ? (
              <Line
                data={{
                  labels: lineChartData.labels,
                  datasets: lineChartData.series.map((s) => ({
                    label: s.name,
                    data: s.data,
                    borderColor: s.color,
                    backgroundColor: s.color,
                    tension: 0.4,
                    pointRadius: 4,
                  })),
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: legendBottom,
                  scales: {
                    x: { title: { display: true, text: 'Meses' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: {
                      title: { display: true, text: 'Casos' },
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.05)' },
                    },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de evolución temporal
              </div>
            )}
          </div>
          <ChartAiInsight insight={timelineInsight} />
        </div>
      </div>

      <div className="charts-grid-row">
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">{barTitle}</h3>
          <div style={{ height: '320px' }}>
            {barChartData.values.length > 0 ? (
              <Bar
                data={{
                  labels: barChartData.labels.map((l) => wrapLabel(l)),
                  datasets: [
                    {
                      data: barChartData.values,
                      backgroundColor: barChartData.colors,
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
                    x: { title: { display: true, text: 'Casos' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { grid: { display: false } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin registros de causas
              </div>
            )}
          </div>
          <ChartAiInsight insight={topCausasInsight} />
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Demoras Críticas en la Atención</h3>
          <div style={{ height: '320px' }}>
            {demorasChartData.values.length > 0 ? (
              <Bar
                data={{
                  labels: demorasChartData.labels.map((l) => wrapLabel(l, 25)),
                  datasets: [
                    {
                      data: demorasChartData.values,
                      backgroundColor: ['#e74c3c', '#e67e22', '#f1c40f', '#3498db'],
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
                      title: { display: true, text: 'Casos' },
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.05)' },
                    },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de demoras (Aplica principalmente a Mortalidad)
              </div>
            )}
          </div>
          <ChartAiInsight insight={demorasInsight} />
        </div>
      </div>

      <div className="charts-grid-row">
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Distribución por Edad Materna</h3>
          <div style={{ height: '320px' }}>
            {edadChartData.labels.length > 0 ? (
              <Bar
                data={{
                  labels: edadChartData.labels,
                  datasets: [
                    { label: 'Mortalidad', data: edadChartData.mortalidadValues, backgroundColor: CHART_COLORS.mortalidad },
                    { label: 'Morbilidad', data: edadChartData.morbilidadValues, backgroundColor: CHART_COLORS.morbilidad },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: legendBottom,
                  scales: {
                    x: { title: { display: true, text: 'Rango de Edad' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { title: { display: true, text: 'Casos' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de distribución por edad
              </div>
            )}
          </div>
          <ChartAiInsight insight={edadInsight} />
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Momento de Ocurrencia / Muerte</h3>
          <div style={{ height: '320px' }}>
            {momentoChartData.labels.length > 0 ? (
              <Pie
                data={{
                  labels: momentoChartData.labels,
                  datasets: [
                    {
                      data: momentoChartData.labels.map(
                        (_, i) => momentoChartData.mortalidadValues[i] + momentoChartData.morbilidadValues[i],
                      ),
                      backgroundColor: ['#34495e', '#9b59b6', '#3498db', '#e74c3c', '#1abc9c'],
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  cutout: '40%',
                  plugins: legendBottom,
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos del momento del evento
              </div>
            )}
          </div>
          <ChartAiInsight insight={momentoInsight} />
        </div>
      </div>
    </div>
  )
}
