import { Minus, TrendingDown, TrendingUp } from 'lucide-react'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'

export type TrendPeriodo = 'mes' | 'año'

export interface TrendBadgeProps {
  compare: CompareResult | null
  periodo?: TrendPeriodo
}

// Eventos adversos (mortalidad/morbilidad): bajar es favorable y subir desfavorable. Se evita
// el verde/rojo puro (una bajada puede ser subregistro) y el color siempre va con flecha y texto.
const REFERENCIA: Record<TrendPeriodo, string> = { mes: 'mes anterior', año: 'año anterior' }
const REFERENCIA_POR_DEFECTO = 'periodo anterior'
const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/** Con una base previa menor el porcentaje es inestable (de 1 a 2 casos sería +100 %). */
export const BASE_MINIMA_PORCENTAJE = 5

const AVISO_BAJADA = 'Una cifra menor puede deberse a casos aún sin notificar.'
const PILL_CLASS = 'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium'

export function TrendBadge({ compare, periodo }: TrendBadgeProps) {
  if (!compare) return <span className="text-xs text-slate-600">Histórico</span>

  const { cur, prev, meses } = compare
  if (prev === 0) {
    // 0 → N no es «estable»: no hay base de comparación.
    return (
      <span className={`${PILL_CLASS} bg-slate-100 text-slate-600`}>
        {cur > 0 ? 'Sin base previa' : 'Estable'}
      </span>
    )
  }

  const referencia = periodo ? REFERENCIA[periodo] : REFERENCIA_POR_DEFECTO
  const alineado = periodo === 'año' && meses !== undefined && meses < 12 ? ` (ene–${MESES[meses - 1]})` : ''
  let texto: string
  if (prev < BASE_MINIMA_PORCENTAJE) {
    texto = `${cur} vs ${prev} casos (${referencia}${alineado})`
  } else {
    const pct = ((cur - prev) / prev) * 100
    texto = `${pct > 0 ? '+' : ''}${pct.toFixed(0)}% vs ${referencia}${alineado} (${cur} vs ${prev})`
  }

  if (cur > prev) {
    return (
      <span className={`${PILL_CLASS} bg-amber-50 text-amber-800`}>
        <TrendingUp className="size-3.5" aria-hidden="true" />
        {texto}
      </span>
    )
  }
  if (cur < prev) {
    return (
      <span className={`${PILL_CLASS} bg-sky-50 text-sky-700`} title={AVISO_BAJADA}>
        <TrendingDown className="size-3.5" aria-hidden="true" />
        {texto}
      </span>
    )
  }
  return (
    <span className={`${PILL_CLASS} bg-slate-100 text-slate-600`}>
      <Minus className="size-3.5" aria-hidden="true" />
      {texto}
    </span>
  )
}
