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
 * `dataviz/scripts/validate_palette.js "#dc2626,#64748b" --mode light
 * --surface #ffffff`: todos los checks pasan (CVD ΔE 25.2 protan / 36.2
 * normal-vision). Se usa gris clínico en vez del verde "good" de la paleta
 * de estado genérica porque verde ya significa "morbilidad" en este
 * dashboard (`CHART_COLORS.morbilidad`) — reusarlo aquí generaría una
 * colisión semántica entre "seguro" y "morbilidad".
 */
export const STATUS_COLORS = {
  risk: '#dc2626',
  safe: '#64748b',
}

/** Color de marca para gráficas de una sola serie sin significado propio (p. ej. las sociodemográficas). */
export const BRAND_COLOR = '#89005e'

/**
 * Paleta categórica para gráficas de varias series (cruce de variables), en orden fijo.
 * Validada con `validate_palette.js --mode light`: todos los controles pasan; el contraste bajo
 * de turquesa, amarillo y rosa (< 3:1) se compensa con la leyenda visible de la gráfica.
 */
export const CATEGORICAL_PALETTE = [
  '#2a78d6',
  '#eb6834',
  '#1baf7a',
  '#eda100',
  '#e87ba4',
  '#008300',
  '#4a3aa7',
  '#e34948',
]

/** Barras delgadas: horizontales (muchas categorías) y verticales (pocas barras). */
export const BAR_STYLE_HORIZONTAL = { borderRadius: 4, borderWidth: 0, maxBarThickness: 16, barPercentage: 0.6 }
export const BAR_STYLE_VERTICAL = { borderRadius: 4, borderWidth: 0, maxBarThickness: 40 }
/** Barras agrupadas (varias series por categoría): casi sin hueco dentro del grupo para no quedar demasiado finas. */
export const BAR_STYLE_GROUPED = { ...BAR_STYLE_HORIZONTAL, barPercentage: 0.9 }

ChartJS.defaults.font.family = CHART_FONT_FAMILY
ChartJS.defaults.color = CHART_TEXT_COLOR
ChartJS.defaults.plugins.legend.position = 'bottom'

export function echartsBaseTextStyle() {
  return { fontFamily: CHART_FONT_FAMILY, color: CHART_TEXT_COLOR }
}
