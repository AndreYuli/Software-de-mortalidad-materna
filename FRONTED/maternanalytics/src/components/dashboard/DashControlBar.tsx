import { MESES_ES } from '../../constants/dashboardConstants'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'

export interface DashControlBarProps {
  segmento: Segmento
  onSegmentoChange: (segmento: Segmento) => void
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  filterYear: string
  onYearChange: (year: string) => void
  availableYears: number[]
  filterMonth: string
  onMonthChange: (month: string) => void
  onExport: () => void
}

export function DashControlBar({
  segmento,
  onSegmentoChange,
  latestMortalidad,
  latestMorbilidad,
  filterYear,
  onYearChange,
  availableYears,
  filterMonth,
  onMonthChange,
  onExport,
}: DashControlBarProps) {
  return (
    <div className="dash-control-bar">
      <div className="dash-control-title">
        <h1>Análisis Epidemiológico</h1>
        <p>Panel descriptivo y de inteligencia de salud pública de VidaMaterna</p>
      </div>
      <div className="dash-controls-right">
        <select
          value={segmento}
          onChange={(e) => onSegmentoChange(e.target.value as Segmento)}
          className="dash-select"
        >
          <option value="ambos">Segmento: Ambos Eventos</option>
          {latestMortalidad && <option value="mortalidad">Segmento: Mortalidad (550)</option>}
          {latestMorbilidad && <option value="morbilidad">Segmento: Morbilidad (549)</option>}
        </select>

        <select
          value={filterYear}
          onChange={(e) => onYearChange(e.target.value)}
          className="dash-select"
          disabled={availableYears.length === 0}
        >
          <option value="">Todos los años</option>
          {availableYears.map((y) => (
            <option key={y} value={String(y)}>
              {y}
            </option>
          ))}
        </select>

        <select
          value={filterMonth}
          onChange={(e) => onMonthChange(e.target.value)}
          className="dash-select"
          disabled={!filterYear}
        >
          <option value="">Todos los meses</option>
          {MESES_ES.map((m, i) => (
            <option key={i + 1} value={String(i + 1)}>
              {m}
            </option>
          ))}
        </select>

        <button onClick={onExport} className="btn-export-report">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
          </svg>
          Exportar Reporte
        </button>
      </div>
    </div>
  )
}
