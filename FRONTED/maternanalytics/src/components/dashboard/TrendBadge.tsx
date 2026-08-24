import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'

export interface TrendBadgeProps {
  compare: CompareResult | null
}

export function TrendBadge({ compare }: TrendBadgeProps) {
  if (!compare) return <span className="kpi-trend-period">Histórico</span>

  const { cur, prev } = compare
  if (prev === 0) {
    return <span className="trend-badge neutral">Estable</span>
  }

  const diff = cur - prev
  const pct = (diff / prev) * 100
  const sign = pct >= 0 ? '+' : ''
  const trendClass = pct > 0 ? 'trend-up' : 'trend-down'

  return (
    <span className={`trend-badge ${trendClass}`}>
      {sign}
      {pct.toFixed(0)}% vs ant.
    </span>
  )
}
