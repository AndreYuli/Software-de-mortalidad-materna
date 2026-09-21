import { useState, type ReactNode } from 'react'
import { Download, SlidersHorizontal } from 'lucide-react'
import { MESES_ES } from '../../constants/dashboardConstants'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'

const SEMANAS_ISO = Array.from({ length: 53 }, (_, i) => i + 1)
const DIAS_MES = Array.from({ length: 31 }, (_, i) => i + 1)

const LABEL_CLASS = 'mb-1 block text-xs font-medium text-slate-500'
const SELECT_CLASS =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-magenta focus:ring-2 focus:ring-brand-magenta/30 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400'

export interface FiltersBarProps {
  segmento?: Segmento
  onSegmentoChange?: (segmento: Segmento) => void
  latestMortalidad?: { id: number } | null
  latestMorbilidad?: { id: number } | null
  filterYear: string
  onYearChange: (year: string) => void
  availableYears: number[]
  filterMonth: string
  onMonthChange: (month: string) => void
  filterWeek: string
  onWeekChange: (week: string) => void
  filterDay: string
  onDayChange: (day: string) => void
  onExport: () => void
}

interface SelectFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  /** Ayuda para cuando el campo está deshabilitado: va en `title` y como texto para lectores de pantalla. */
  hint?: string
  children: ReactNode
}

function SelectField({ id, label, value, onChange, disabled, hint, children }: SelectFieldProps) {
  const hintId = `${id}-hint`
  return (
    <div>
      <label htmlFor={id} className={LABEL_CLASS}>
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        title={hint}
        aria-describedby={hint ? hintId : undefined}
        className={SELECT_CLASS}
      >
        {children}
      </select>
      {hint && (
        <span id={hintId} className="sr-only">
          {hint}
        </span>
      )}
    </div>
  )
}

export function FiltersBar({
  segmento,
  onSegmentoChange,
  latestMortalidad,
  latestMorbilidad,
  filterYear,
  onYearChange,
  availableYears,
  filterMonth,
  onMonthChange,
  filterWeek,
  onWeekChange,
  filterDay,
  onDayChange,
  onExport,
}: FiltersBarProps) {
  const [open, setOpen] = useState(false)
  const hasActiveFilters = Boolean(filterYear || filterMonth || filterWeek || filterDay)

  const handleClearFilters = () => {
    onYearChange('')
    onMonthChange('')
    onWeekChange('')
    onDayChange('')
  }

  return (
    <section
      aria-label="Filtros del análisis"
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-0 lg:z-10"
    >
      <div className="flex flex-wrap items-end gap-3">
        <button
          type="button"
          aria-expanded={open}
          aria-controls="filters-panel"
          onClick={() => setOpen((value) => !value)}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 lg:hidden"
        >
          <SlidersHorizontal className="size-4" aria-hidden="true" />
          Filtros
          {hasActiveFilters && (
            <>
              <span className="size-2 rounded-full bg-brand-magenta" aria-hidden="true" />
              <span className="sr-only">(hay filtros activos)</span>
            </>
          )}
        </button>

        <div
          id="filters-panel"
          className={`${
            open ? 'grid' : 'hidden'
          } w-full grid-cols-1 gap-3 sm:grid-cols-2 lg:grid lg:w-auto lg:flex-1 lg:grid-cols-[repeat(auto-fit,minmax(9rem,1fr))]`}
        >
          {segmento && onSegmentoChange && (
            <SelectField
              id="filter-segmento"
              label="Evento"
              value={segmento}
              onChange={(value) => onSegmentoChange(value as Segmento)}
            >
              <option value="ambos">549 + 550 integrados</option>
              {latestMortalidad && <option value="mortalidad">Solo mortalidad 550</option>}
              {latestMorbilidad && <option value="morbilidad">Solo morbilidad 549</option>}
            </SelectField>
          )}

          <SelectField
            id="filter-year"
            label="Año de Reporte"
            value={filterYear}
            onChange={onYearChange}
            disabled={availableYears.length === 0}
          >
            <option value="">Todos los años</option>
            {availableYears.map((y) => (
              <option key={y} value={String(y)}>
                {y}
              </option>
            ))}
          </SelectField>

          <SelectField
            id="filter-month"
            label="Mes de Reporte"
            value={filterMonth}
            onChange={onMonthChange}
            disabled={!filterYear}
            hint={!filterYear ? 'Selecciona un año primero para habilitar meses.' : undefined}
          >
            <option value="">Todos los meses</option>
            {MESES_ES.map((m, i) => (
              <option key={i + 1} value={String(i + 1)}>
                {m}
              </option>
            ))}
          </SelectField>

          <SelectField
            id="filter-week"
            label="Semana de Reporte"
            value={filterWeek}
            onChange={onWeekChange}
            disabled={!filterYear}
            hint={!filterYear ? 'Selecciona un año primero para habilitar semanas.' : undefined}
          >
            <option value="">Todas las semanas</option>
            {SEMANAS_ISO.map((w) => (
              <option key={w} value={String(w)}>
                Semana {w}
              </option>
            ))}
          </SelectField>

          <SelectField
            id="filter-day"
            label="Día de Reporte"
            value={filterDay}
            onChange={onDayChange}
            disabled={!filterMonth}
            hint={!filterMonth ? 'Selecciona un mes primero para habilitar días.' : undefined}
          >
            <option value="">Todos los días</option>
            {DIAS_MES.map((d) => (
              <option key={d} value={String(d)}>
                {d}
              </option>
            ))}
          </SelectField>
        </div>

        <div className="ml-auto flex items-center gap-2">
          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleClearFilters}
              title="Limpiar todos los filtros"
              className="rounded-lg px-3 py-2 text-sm font-medium text-brand-violet hover:underline"
            >
              Limpiar
            </button>
          )}
          <button
            type="button"
            onClick={onExport}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-magenta px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
          >
            <Download className="size-4" aria-hidden="true" />
            Exportar Reporte
          </button>
        </div>
      </div>
    </section>
  )
}
