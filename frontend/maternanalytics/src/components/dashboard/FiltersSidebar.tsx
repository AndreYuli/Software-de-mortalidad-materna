import { MESES_ES } from '../../constants/dashboardConstants'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'

const SEMANAS_ISO = Array.from({ length: 53 }, (_, i) => i + 1)
const DIAS_MES = Array.from({ length: 31 }, (_, i) => i + 1)

export interface FiltersSidebarProps {
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

export function FiltersSidebar({
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
}: FiltersSidebarProps) {
  const hasActiveFilters = Boolean(filterYear || filterMonth || filterWeek || filterDay)

  const handleClearFilters = () => {
    onYearChange('')
    onMonthChange('')
    onWeekChange('')
    onDayChange('')
  }

  return (
    <aside className="filters-sidebar-okd">
      <div className="sidebar-section-header">
        <h3>Cohorte de análisis</h3>
        {hasActiveFilters && (
          <button className="btn-clear-filters" onClick={handleClearFilters} title="Limpiar todos los filtros">
            Limpiar
          </button>
        )}
      </div>

      <div className="sidebar-filter-content">
        {segmento && onSegmentoChange && (
          <div className="filter-field-group">
            <label className="field-label" htmlFor="filter-segmento">Evento</label>
            <div className="custom-select-wrapper">
              <select
                id="filter-segmento"
                value={segmento}
                onChange={(e) => onSegmentoChange(e.target.value as Segmento)}
                className="sidebar-select"
              >
                <option value="ambos">549 + 550 integrados</option>
                {latestMortalidad && <option value="mortalidad">Solo mortalidad 550</option>}
                {latestMorbilidad && <option value="morbilidad">Solo morbilidad 549</option>}
              </select>
            </div>
            <small className="field-helper">Define el universo analítico para indicadores y gráficas.</small>
          </div>
        )}

        <div className="sidebar-divider" />

        {/* Year Filter */}
        <div className="filter-field-group">
          <label className="field-label" htmlFor="filter-year">Año de Reporte</label>
          <div className="custom-select-wrapper">
            <select
              id="filter-year"
              value={filterYear}
              onChange={(e) => onYearChange(e.target.value)}
              className="sidebar-select"
              disabled={availableYears.length === 0}
            >
              <option value="">Todos los años</option>
              {availableYears.map((y) => (
                <option key={y} value={String(y)}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Month Filter */}
        <div className="filter-field-group">
          <label className="field-label" htmlFor="filter-month">Mes de Reporte</label>
          <div className="custom-select-wrapper">
            <select
              id="filter-month"
              value={filterMonth}
              onChange={(e) => onMonthChange(e.target.value)}
              className="sidebar-select"
              disabled={!filterYear}
            >
              <option value="">Todos los meses</option>
              {MESES_ES.map((m, i) => (
                <option key={i + 1} value={String(i + 1)}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          {!filterYear && (
            <small className="field-helper warning">
              * Selecciona un año primero para habilitar meses.
            </small>
          )}
        </div>

        {/* Week Filter */}
        <div className="filter-field-group">
          <label className="field-label" htmlFor="filter-week">Semana de Reporte</label>
          <div className="custom-select-wrapper">
            <select
              id="filter-week"
              value={filterWeek}
              onChange={(e) => onWeekChange(e.target.value)}
              className="sidebar-select"
              disabled={!filterYear}
            >
              <option value="">Todas las semanas</option>
              {SEMANAS_ISO.map((w) => (
                <option key={w} value={String(w)}>
                  Semana {w}
                </option>
              ))}
            </select>
          </div>
          {!filterYear && (
            <small className="field-helper warning">
              * Selecciona un año primero para habilitar semanas.
            </small>
          )}
        </div>

        {/* Day Filter */}
        <div className="filter-field-group">
          <label className="field-label" htmlFor="filter-day">Día de Reporte</label>
          <div className="custom-select-wrapper">
            <select
              id="filter-day"
              value={filterDay}
              onChange={(e) => onDayChange(e.target.value)}
              className="sidebar-select"
              disabled={!filterMonth}
            >
              <option value="">Todos los días</option>
              {DIAS_MES.map((d) => (
                <option key={d} value={String(d)}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          {!filterMonth && (
            <small className="field-helper warning">
              * Selecciona un mes primero para habilitar días.
            </small>
          )}
        </div>

        <div className="sidebar-divider" />

        {/* Actions Group */}
        <div className="filter-actions-group">
          <button onClick={onExport} className="btn-sidebar-export">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
            </svg>
            Exportar Reporte
          </button>
        </div>
      </div>
    </aside>
  )
}
