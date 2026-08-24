import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
)

export const CHART_FONT_FAMILY = 'Plus Jakarta Sans, sans-serif'
export const CHART_TEXT_COLOR = '#1a202c'

export const CHART_COLORS = {
  mortalidad: '#c0392b',
  morbilidad: '#2ca02c',
}

ChartJS.defaults.font.family = CHART_FONT_FAMILY
ChartJS.defaults.color = CHART_TEXT_COLOR
ChartJS.defaults.plugins.legend.position = 'bottom'

export function echartsBaseTextStyle() {
  return { fontFamily: CHART_FONT_FAMILY, color: CHART_TEXT_COLOR }
}
