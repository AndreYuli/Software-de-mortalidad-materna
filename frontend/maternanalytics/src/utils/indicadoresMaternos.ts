export interface IndicadoresMaternos {
  /** Casos de morbilidad materna extrema por cada muerte materna (MME / MM). */
  relacionMmeMm: number | null
  /** Muertes maternas sobre el total de eventos: MM / (MME + MM) × 100. */
  indiceMortalidad: number | null
}

interface EntradaIndicadores {
  /** Solo tienen sentido cuando están los dos eventos en el análisis. */
  ambosEventos: boolean
  totalMortalidad: number
  totalMorbilidad: number
}

export function calcularIndicadores({
  ambosEventos,
  totalMortalidad,
  totalMorbilidad,
}: EntradaIndicadores): IndicadoresMaternos {
  if (!ambosEventos) return { relacionMmeMm: null, indiceMortalidad: null }
  const total = totalMortalidad + totalMorbilidad
  return {
    relacionMmeMm: totalMortalidad > 0 ? totalMorbilidad / totalMortalidad : null,
    indiceMortalidad: total > 0 ? (totalMortalidad / total) * 100 : null,
  }
}

/** Formato numérico colombiano: `20.100`, `50,3`. */
export function formatoNumero(valor: number, decimales = 0): string {
  return valor.toLocaleString('es-CO', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}
