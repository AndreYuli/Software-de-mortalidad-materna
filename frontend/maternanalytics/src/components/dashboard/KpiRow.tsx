import type { ReactNode } from 'react'
import { Activity, Droplet, Hospital, Percent, TriangleAlert, type LucideIcon } from 'lucide-react'
import { TrendBadge, type TrendPeriodo } from './TrendBadge'
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
  periodo?: TrendPeriodo
}

const LETALIDAD_ALTA_TEXTO = 'Valor atípicamente alto'

interface KpiCellProps {
  icon: LucideIcon
  label: string
  value: string | number
  trend?: ReactNode
  alert?: boolean
}

function KpiCell({ icon: Icon, label, value, trend, alert = false }: KpiCellProps) {
  return (
    <div
      className={`flex flex-col gap-2 p-5 ${alert ? 'bg-amber-50' : 'bg-white'}`}
      title={alert ? LETALIDAD_ALTA_TEXTO : undefined}
    >
      <div className="flex items-center gap-3">
        <span
          className={`flex size-9 shrink-0 items-center justify-center rounded-full ${
            alert ? 'bg-amber-100 text-amber-700' : 'bg-brand-magenta/10 text-brand-magenta'
          }`}
        >
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <span className="text-sm font-medium text-slate-500">{label}</span>
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <strong className={`text-3xl font-bold ${alert ? 'text-amber-700' : 'text-brand-deep'}`}>{value}</strong>
        {alert && <TriangleAlert className="size-5 text-amber-600" aria-hidden="true" />}
        {alert && <span className="sr-only">{LETALIDAD_ALTA_TEXTO}</span>}
        {trend}
      </div>
    </div>
  )
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
  periodo,
}: KpiRowProps) {
  const letalidadNumerica = Number.parseFloat(tasaLetalidad)
  const shouldReviewLetalidad = Number.isFinite(letalidadNumerica) && letalidadNumerica >= 50

  return (
    <section
      className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 shadow-sm sm:grid-cols-2 lg:grid-cols-4"
      aria-label="Resumen epidemiológico"
    >
      <KpiCell
        icon={Activity}
        label="Casos analizados"
        value={totalCasos}
        trend={<TrendBadge compare={{ cur: curTot, prev: prevTot }} periodo={periodo} />}
      />
      <KpiCell
        icon={Droplet}
        label="Mortalidad materna 550"
        value={totalMortalidad}
        trend={<TrendBadge compare={yearCompareMort} periodo={periodo} />}
      />
      <KpiCell
        icon={Hospital}
        label="Morbilidad materna extrema 549"
        value={totalMorbilidad}
        trend={<TrendBadge compare={yearCompareMorb} periodo={periodo} />}
      />
      <KpiCell icon={Percent} label="Tasa de letalidad" value={`${tasaLetalidad}%`} alert={shouldReviewLetalidad} />
    </section>
  )
}
