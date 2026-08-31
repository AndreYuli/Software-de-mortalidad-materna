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

/**
 * Colores de estado (riesgo/seguro) para gráficas que resaltan grupos de
 * mayor riesgo obstétrico (edad materna, edad gestacional). Validados con
 * `dataviz/scripts/validate_palette.js "#dc2626,#0066cc" --mode light
 * --surface #ffffff`: todos los checks pasan (CVD ΔE 25.2 protan / 36.2
 * normal-vision). Se usa azul en vez del verde "good" de la paleta de
 * estado genérica porque verde ya significa "morbilidad" en este dashboard
 * (`CHART_COLORS.morbilidad`) — reusarlo aquí generaría una colisión
 * semántica entre "seguro" y "morbilidad".
 */
export const STATUS_COLORS = {
  risk: '#dc2626',
  safe: '#0066cc',
}

ChartJS.defaults.font.family = CHART_FONT_FAMILY
ChartJS.defaults.color = CHART_TEXT_COLOR
ChartJS.defaults.plugins.legend.position = 'bottom'

export function echartsBaseTextStyle() {
  return { fontFamily: CHART_FONT_FAMILY, color: CHART_TEXT_COLOR }
}
