import './UploadHistorySection.css'
import { useUploadHistory } from '../../hooks/dashboard/useUploadHistory'
import { SpinnerIcon } from '../icons'

function formatFecha(iso: string): string {
  try {
    // El backend guarda fecha_carga en UTC pero la serializa sin zona horaria;
    // sin la 'Z' el navegador la interpretaría como hora local (desfase de horas).
    const tieneZona = /(Z|[+-]\d{2}:?\d{2})$/.test(iso)
    const d = new Date(tieneZona ? iso : `${iso}Z`)
    if (Number.isNaN(d.getTime())) return iso
    return d.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

const MESES = [
  'Enero',
  'Febrero',
  'Marzo',
  'Abril',
  'Mayo',
  'Junio',
  'Julio',
  'Agosto',
  'Septiembre',
  'Octubre',
  'Noviembre',
  'Diciembre',
]

// La semana ISO va de 1 a 53.
const SEMANAS = Array.from({ length: 53 }, (_, i) => i + 1)

function formatTipo(tipo: string): string {
  return tipo === 'mortalidad' ? '550 · Mortalidad' : '549 · Morbilidad'
}

function extractResumen(resumen: Record<string, unknown>): string {
  const nuevos = (resumen.pacientes_nuevos as number) ?? 0
  const existentes = (resumen.pacientes_existentes as number) ?? 0
  const creados = (resumen.casos_creados as number) ?? 0
  const actualizados = (resumen.casos_actualizados as number) ?? 0
  const duplicados = (resumen.filas_omitidas_duplicadas as number) ?? 0
  const partes: string[] = []
  if (nuevos > 0) partes.push(`${nuevos} pacientes nuevos`)
  if (existentes > 0) partes.push(`${existentes} existentes`)
  if (creados > 0) partes.push(`${creados} casos creados`)
  if (actualizados > 0) partes.push(`${actualizados} actualizados`)
  if (duplicados > 0) partes.push(`${duplicados} duplicados omitidos`)
  return partes.length > 0 ? partes.join(' · ') : 'Sin detalle'
}

export function UploadHistorySection() {
  const {
    items,
    loading,
    error,
    page,
    totalPages,
    total,
    aniosDisponibles,
    filtros,
    hasFilters,
    setFiltro,
    clearFilters,
    setPage,
    reload,
  } = useUploadHistory()

  // Los filtros permanecen montados durante la carga y los errores: si se reemplazara toda la
  // sección por el indicador de carga, el campo de búsqueda perdería el foco en cada tecla.
  const resumen = loading
    ? 'Consultando…'
    : `${total} ${total === 1 ? 'carga' : 'cargas'}${hasFilters ? ' que coinciden con los filtros' : ' registradas'}`

  return (
    <div className="upload-history-section">
      <h2 className="section-title">Historial de Cargas</h2>
      <p className="upload-history-summary" aria-live="polite">
        {resumen}
      </p>

      <div className="history-filters" role="search" aria-label="Filtros del historial">
        <div className="history-filter-field history-filter-search">
          <label className="field-label" htmlFor="history-q">
            Buscar
          </label>
          <input
            id="history-q"
            className="history-search-input"
            type="search"
            placeholder="Archivo o evento (549 / 550)"
            value={filtros.q}
            maxLength={100}
            onChange={(e) => setFiltro('q', e.target.value)}
          />
        </div>

        <div className="history-filter-field">
          <label className="field-label" htmlFor="history-tipo">
            Evento
          </label>
          <div className="custom-select-wrapper">
            <select
              id="history-tipo"
              className="sidebar-select"
              value={filtros.tipo}
              onChange={(e) => setFiltro('tipo', e.target.value)}
            >
              <option value="">Todos</option>
              <option value="mortalidad">550 · Mortalidad</option>
              <option value="morbilidad">549 · Morbilidad</option>
            </select>
          </div>
        </div>

        <div className="history-filter-field">
          <label className="field-label" htmlFor="history-year">
            Año
          </label>
          <div className="custom-select-wrapper">
            <select
              id="history-year"
              className="sidebar-select"
              value={filtros.year}
              onChange={(e) => setFiltro('year', e.target.value)}
            >
              <option value="">Todos</option>
              {aniosDisponibles.map((anio) => (
                <option key={anio} value={String(anio)}>
                  {anio}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="history-filter-field">
          <label className="field-label" htmlFor="history-month">
            Mes
          </label>
          <div className="custom-select-wrapper">
            <select
              id="history-month"
              className="sidebar-select"
              value={filtros.month}
              onChange={(e) => setFiltro('month', e.target.value)}
            >
              <option value="">Todos</option>
              {MESES.map((mes, i) => (
                <option key={mes} value={String(i + 1)}>
                  {mes}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="history-filter-field">
          <label className="field-label" htmlFor="history-week">
            Semana
          </label>
          <div className="custom-select-wrapper">
            <select
              id="history-week"
              className="sidebar-select"
              value={filtros.week}
              onChange={(e) => setFiltro('week', e.target.value)}
            >
              <option value="">Todas</option>
              {SEMANAS.map((semana) => (
                <option key={semana} value={String(semana)}>
                  {semana}
                </option>
              ))}
            </select>
          </div>
        </div>

        {hasFilters && (
          <button className="history-page-btn history-clear-btn" type="button" onClick={clearFilters}>
            Limpiar filtros
          </button>
        )}
      </div>

      {loading && (
        <div className="upload-history-loading">
          <SpinnerIcon />
          <span>Cargando historial...</span>
        </div>
      )}

      {!loading && error && (
        <div className="upload-history-error" role="alert">
          {error}{' '}
          <button className="history-page-btn" type="button" onClick={reload}>
            Reintentar
          </button>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="upload-history-empty">
          {hasFilters
            ? 'Ninguna carga coincide con la búsqueda o los filtros.'
            : 'No hay cargas registradas aún. Sube un archivo para comenzar.'}
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="upload-history-table-wrapper">
            <table className="upload-history-table">
              <thead>
                <tr>
                  <th>Año</th>
                  <th>Mes</th>
                  <th>Semana</th>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Archivo</th>
                  <th>Registros</th>
                  <th>Resumen</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="history-periodo">{item.anio}</td>
                    <td className="history-periodo">{MESES[item.mes - 1] ?? item.mes}</td>
                    <td className="history-periodo">{item.semana}</td>
                    <td className="history-fecha">{formatFecha(item.fecha_carga)}</td>
                    <td>
                      <span className={`history-tipo-badge history-tipo-${item.tipo}`}>
                        {formatTipo(item.tipo)}
                      </span>
                    </td>
                    <td className="history-filename" title={item.nombre_archivo}>
                      {item.nombre_archivo}
                    </td>
                    <td className="history-records">{item.total_registros}</td>
                    <td className="history-resumen">{extractResumen(item.resumen)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="upload-history-pagination">
              <button
                className="history-page-btn"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                type="button"
              >
                ← Anterior
              </button>
              <span className="history-page-info">
                Página {page} de {totalPages}
              </span>
              <button
                className="history-page-btn"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                type="button"
              >
                Siguiente →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
