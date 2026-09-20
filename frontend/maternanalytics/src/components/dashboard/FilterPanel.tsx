import './FilterPanel.css'
import { MESES_ES } from '../../constants/dashboardConstants'

export interface FilterPanelProps {
  year: string
  month: string
  eventos: string[]
  availableYears: number[]
  onYearChange: (year: string) => void
  onMonthChange: (month: string) => void
  onEventosChange: (eventos: string[]) => void
}

export function FilterPanel({ year, month, eventos, availableYears, onYearChange, onMonthChange, onEventosChange }: FilterPanelProps) {
  const toggleEvento = (codigo: string) => {
    const isChecked = eventos.includes(codigo)
    if (isChecked && eventos.length === 1) return
    onEventosChange(isChecked ? eventos.filter(e => e !== codigo) : [...eventos, codigo])
  }

  const hasDateFilter = year || month

  return (
    <div className="filter-panel-okd">
      <span className="filter-label-okd">Filtros</span>

      <div className="filter-group-okd">
        <select value={year} onChange={e => onYearChange(e.target.value)} className="filter-select-okd">
          <option value="">Todos los años</option>
          {availableYears.map(y => <option key={y} value={String(y)}>{y}</option>)}
        </select>

        <select value={month} onChange={e => onMonthChange(e.target.value)} className="filter-select-okd">
          <option value="">Todos los meses</option>
          {MESES_ES.map((m, i) => <option key={i + 1} value={String(i + 1)}>{m}</option>)}
        </select>

        {hasDateFilter && (
          <button className="filter-clear-okd" onClick={() => { onYearChange(''); onMonthChange('') }}>
            ✕ Limpiar
          </button>
        )}
      </div>

      <div className="filter-divider-okd" />

      <div className="filter-eventos-okd">
        <label className="filter-check-okd">
          <input type="checkbox" checked={eventos.includes('549')} onChange={() => toggleEvento('549')} />
          <span className="check-badge-549">549</span>
          Morbilidad
        </label>
        <label className="filter-check-okd">
          <input type="checkbox" checked={eventos.includes('550')} onChange={() => toggleEvento('550')} />
          <span className="check-badge-550">550</span>
          Mortalidad
        </label>
      </div>
    </div>
  )
}