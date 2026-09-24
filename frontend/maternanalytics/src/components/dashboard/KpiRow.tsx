import { useId, type ReactNode } from 'react'
import { Activity, Droplet, Hospital, Info, Percent, type LucideIcon } from 'lucide-react'
import { TrendBadge, type TrendPeriodo } from './TrendBadge'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'
import { formatoNumero } from '../../utils/indicadoresMaternos'

export interface KpiRowProps {
  totalMortalidad: number
  totalMorbilidad: number
  /** MME / MM; `null` si no se puede calcular. */
  relacionMmeMm: number | null
  /** MM / (MME + MM) × 100; `null` si no se puede calcular. */
  indiceMortalidad: number | null
  yearCompareMort: CompareResult | null
  yearCompareMorb: CompareResult | null
  periodo?: TrendPeriodo
}

const SIN_DATO = '—'
const AYUDA_RELACION = 'Casos de morbilidad materna extrema (MME) por cada muerte materna (MM).'
const AYUDA_INDICE =
  'Índice de mortalidad = MM / (MME + MM) × 100: proporción de muertes maternas (evento 550) sobre el total de eventos 549 y 550.'

function InfoTip({ text }: { text: string }) {
  const id = useId()
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-describedby={id}
        className="rounded-full p-0.5 text-slate-400 hover:text-brand-violet focus-visible:text-brand-violet"
      >
        <Info className="size-4" aria-hidden="true" />
        <span className="sr-only">Cómo se calcula</span>
      </button>
      <span
        role="tooltip"
        id={id}
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 hidden w-64 -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-normal text-white shadow-lg group-focus-within:block group-hover:block"
      >
        {text}
      </span>
    </span>
  )
}

interface KpiCellProps {
  icon: LucideIcon
  label: string
  value: string
  hint?: string
  trend?: ReactNode
}

function KpiCell({ icon: Icon, label, value, hint, trend }: KpiCellProps) {
  return (
    <div className="flex flex-col gap-2 bg-white p-5">
      <div className="flex items-center gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-magenta/10 text-brand-magenta">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <span className="text-sm font-medium text-slate-500">{label}</span>
        {hint && <InfoTip text={hint} />}
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <strong className="text-3xl font-bold text-brand-deep">{value}</strong>
        {trend}
      </div>
    </div>
  )
}

export function KpiRow({
  totalMortalidad,
  totalMorbilidad,
  relacionMmeMm,
  indiceMortalidad,
  yearCompareMort,
  yearCompareMorb,
  periodo,
}: KpiRowProps) {
  return (
    <section
      className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 shadow-sm sm:grid-cols-2 lg:grid-cols-4"
      aria-label="Resumen epidemiológico"
    >
      <KpiCell
        icon={Droplet}
        label="Mortalidad materna 550"
        value={formatoNumero(totalMortalidad)}
        trend={<TrendBadge compare={yearCompareMort} periodo={periodo} />}
      />
      <KpiCell
        icon={Hospital}
        label="Morbilidad materna extrema 549"
        value={formatoNumero(totalMorbilidad)}
        trend={<TrendBadge compare={yearCompareMorb} periodo={periodo} />}
      />
      <KpiCell
        icon={Activity}
        label="Relación MME/MM"
        value={relacionMmeMm === null ? SIN_DATO : `${formatoNumero(relacionMmeMm, 1)}:1`}
        hint={AYUDA_RELACION}
      />
      <KpiCell
        icon={Percent}
        label="Índice de mortalidad"
        value={indiceMortalidad === null ? SIN_DATO : `${formatoNumero(indiceMortalidad, 1)}%`}
        hint={AYUDA_INDICE}
      />
    </section>
  )
}
