import { TrendBadge } from './TrendBadge'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'

export interface KpiRowProps {
  totalCasos: number
  totalMortalidad: number
  totalMorbilidad: number
  tasaLetalidad: string
  curTot: number
  prevTot: number
  yearCompareMort: CompareResult | null
  yearCompareMorb: CompareResult | null
}

export function KpiRow({
  totalCasos,
  totalMortalidad,
  totalMorbilidad,
  tasaLetalidad,
  curTot,
  prevTot,
  yearCompareMort,
  yearCompareMorb,
}: KpiRowProps) {
  return (
    <div className="kpi-row-grid">
      <div className="kpi-dashboard-card kpi-total">
        <div className="kpi-card-header">
          <span className="kpi-card-title">Casos Totales (549 + 550)</span>
          <span className="kpi-card-icon">👥</span>
        </div>
        <div className="kpi-card-value">{totalCasos}</div>
        <div className="kpi-card-trend-container">
          <TrendBadge compare={{ cur: curTot, prev: prevTot }} />
          <span className="kpi-trend-period">vs mes ant.</span>
        </div>
      </div>

      <div className="kpi-dashboard-card kpi-mortalidad">
        <div className="kpi-card-header">
          <span className="kpi-card-title">Mortalidad Materna (550)</span>
          <span className="kpi-card-icon">🩸</span>
        </div>
        <div className="kpi-card-value">{totalMortalidad}</div>
        <div className="kpi-card-trend-container">
          <TrendBadge compare={yearCompareMort} />
          <span className="kpi-trend-period">vs mes ant.</span>
        </div>
      </div>

      <div className="kpi-dashboard-card kpi-morbilidad">
        <div className="kpi-card-header">
          <span className="kpi-card-title">Morbilidad Extrema (549)</span>
          <span className="kpi-card-icon">🏥</span>
        </div>
        <div className="kpi-card-value">{totalMorbilidad}</div>
        <div className="kpi-card-trend-container">
          <TrendBadge compare={yearCompareMorb} />
          <span className="kpi-trend-period">vs mes ant.</span>
        </div>
      </div>

      <div className="kpi-dashboard-card kpi-letalidad">
        <div className="kpi-card-header">
          <span className="kpi-card-title">Tasa de Letalidad</span>
          <span className="kpi-card-icon">📈</span>
        </div>
        <div className="kpi-card-value">{tasaLetalidad}%</div>
        <div className="kpi-card-trend-container">
          <span className="trend-badge neutral" style={{ background: '#f5f0ff', color: '#6f42c1' }}>
            Calculado
          </span>
          <span className="kpi-trend-period">Salud Pública</span>
        </div>
      </div>
    </div>
  )
}
