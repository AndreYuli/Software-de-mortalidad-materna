import { TrendBadge } from './TrendBadge'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'
import { BloodDropIcon, HospitalIcon } from '../icons'

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
  const letalidadNumerica = Number.parseFloat(tasaLetalidad)
  const shouldReviewLetalidad = Number.isFinite(letalidadNumerica) && letalidadNumerica >= 50
  const dominantEventLabel =
    totalMortalidad > totalMorbilidad
      ? 'Predomina mortalidad registrada'
      : totalMorbilidad > totalMortalidad
        ? 'Predomina morbilidad extrema'
        : 'Eventos equilibrados'

  return (
    <section className="epidemiology-summary" aria-label="Resumen epidemiológico">
      <div className="summary-priority-panel">
        <div className="summary-priority-header">
          <span className="summary-priority-label">Lectura inicial de la cohorte</span>
          <span className={`summary-quality-chip ${shouldReviewLetalidad ? 'review' : 'stable'}`}>
            {shouldReviewLetalidad ? 'Revisar consistencia' : 'Indicador estable'}
          </span>
        </div>
        <div className="summary-priority-value">{totalCasos}</div>
        <div className="summary-priority-copy">
          casos analizados entre eventos 549 y 550. {dominantEventLabel}; use esta proporción como primer control
          antes de interpretar tendencias o causas.
        </div>
        <div className="summary-trend-line">
          <TrendBadge compare={{ cur: curTot, prev: prevTot }} />
          <span>variación frente al periodo anterior (mes previo, o año previo si solo hay año)</span>
        </div>
      </div>

      <div className="surveillance-register">
        <div className="surveillance-register-header">
          <span>Registro por evento</span>
          <span className="register-context">SIVIGILA</span>
        </div>

        <div className="register-metric register-metric-mortalidad">
          <span className="register-icon"><BloodDropIcon style={{ width: '18px', height: '18px' }} /></span>
          <div>
            <span className="register-label">Mortalidad materna 550</span>
            <span className="register-helper">Defunciones notificadas</span>
          </div>
          <strong>{totalMortalidad}</strong>
          <TrendBadge compare={yearCompareMort} />
        </div>

        <div className="register-metric register-metric-morbilidad">
          <span className="register-icon"><HospitalIcon style={{ width: '18px', height: '18px' }} /></span>
          <div>
            <span className="register-label">Morbilidad materna extrema 549</span>
            <span className="register-helper">Casos no fatales / severos</span>
          </div>
          <strong>{totalMorbilidad}</strong>
          <TrendBadge compare={yearCompareMorb} />
        </div>

        <div className={`case-fatality-note ${shouldReviewLetalidad ? 'review' : ''}`}>
          <span className="case-fatality-value">{tasaLetalidad}%</span>
          <div>
            <span className="case-fatality-label">Tasa de letalidad</span>
            <p>
              {shouldReviewLetalidad
                ? 'Valor atípicamente alto: confirme denominador, mezcla de eventos y calidad de carga.'
                : 'Cálculo sobre los eventos filtrados en la cohorte actual.'}
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
