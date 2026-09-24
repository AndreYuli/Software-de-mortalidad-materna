import { TrendingDown, TrendingUp } from 'lucide-react'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'

export type TrendPeriodo = 'mes' | 'año'

export interface TrendBadgeProps {
  compare: CompareResult | null
  periodo?: TrendPeriodo
}

const SUFIJOS: Record<TrendPeriodo, string> = {
  mes: 'vs mes anterior',
  año: 'vs año anterior',
}
const SUFIJO_POR_DEFECTO = 'vs periodo anterior'

const PILL_CLASS = 'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium'

export function TrendBadge({ compare, periodo }: TrendBadgeProps) {
  if (!compare) return <span className="text-xs text-slate-400">Histórico</span>

  const { cur, prev } = compare
  if (prev === 0) {
    // 0 → N no es «estable»: no hay base de comparación.
    return (
      <span className={`${PILL_CLASS} bg-slate-100 text-slate-600`}>
        {cur > 0 ? 'Sin base previa' : 'Estable'}
      </span>
    )
  }

  const pct = ((cur - prev) / prev) * 100
  const sign = pct >= 0 ? '+' : ''
  const sufijo = periodo ? SUFIJOS[periodo] : SUFIJO_POR_DEFECTO
  const texto = `${sign}${pct.toFixed(0)}% ${sufijo}`

  // Más casos = verde, menos = rojo. Un 0 exacto sigue la regla anterior (estilo de bajada).
  if (pct > 0) {
    return (
      <span className={`${PILL_CLASS} bg-green-50 text-green-700`}>
        <TrendingUp className="size-3.5" aria-hidden="true" />
        {texto}
      </span>
    )
  }
  return (
    <span className={`${PILL_CLASS} bg-red-50 text-red-700`}>
      <TrendingDown className="size-3.5" aria-hidden="true" />
      {texto}
    </span>
  )
}
