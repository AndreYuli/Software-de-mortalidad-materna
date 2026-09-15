import './UploadHistorySection.css'
import { useUploadHistory } from '../../hooks/dashboard/useUploadHistory'
import { SpinnerIcon } from '../icons'

function formatFecha(iso: string): string {
  try {
    const d = new Date(iso)
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
  const { items, loading, error, page, totalPages, total, setPage } = useUploadHistory()

  if (loading) {
    return (
      <div className="upload-history-section">
        <h2 className="section-title">Historial de Cargas</h2>
        <div className="upload-history-loading">
          <SpinnerIcon />
          <span>Cargando historial...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="upload-history-section">
        <h2 className="section-title">Historial de Cargas</h2>
        <div className="upload-history-error">{error}</div>
      </div>
    )
  }

  return (
    <div className="upload-history-section">
      <h2 className="section-title">Historial de Cargas</h2>
      <p className="upload-history-summary">
        {total} {total === 1 ? 'carga registrada' : 'cargas registradas'}
      </p>

      {items.length === 0 ? (
        <div className="upload-history-empty">
          No hay cargas registradas aún. Sube un archivo para comenzar.
        </div>
      ) : (
        <>
          <div className="upload-history-table-wrapper">
            <table className="upload-history-table">
              <thead>
                <tr>
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
