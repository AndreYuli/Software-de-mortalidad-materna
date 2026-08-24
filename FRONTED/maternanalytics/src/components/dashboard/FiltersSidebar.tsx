import { MESES_ES } from '../../constants/dashboardConstants'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'
import './FiltersSidebar.css'

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
  onExport: () => void
}

export function FiltersSidebar({
  filterYear,
  onYearChange,
  availableYears,
  filterMonth,
  onMonthChange,
  onExport,
}: FiltersSidebarProps) {
  const hasActiveFilters = Boolean(filterYear || filterMonth)

  const handleClearFilters = () => {
    onYearChange('')
    onMonthChange('')
  }

  return (
    <aside className="filters-sidebar-okd">
      <div className="sidebar-section-header">
        <h3>Filtros de Análisis</h3>
        {hasActiveFilters && (
          <button className="btn-clear-filters" onClick={handleClearFilters} title="Limpiar todos los filtros">
            Limpiar
          </button>
        )}
      </div>

      <div className="sidebar-filter-content">
        {/* Year Filter */}
        <div className="filter-field-group">
          <label className="field-label">Año de Reporte</label>
          <div className="custom-select-wrapper">
            <select
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
          <label className="field-label">Mes de Reporte</label>
          <div className="custom-select-wrapper">
            <select
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
