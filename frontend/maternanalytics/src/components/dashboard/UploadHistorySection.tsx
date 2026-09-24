import { useState } from 'react'
import type { HistorialItem } from '../../api'
import { BTN, BTN_DANGER, EditarCargaDialogo, EliminarCargaDialogo } from './CargaDialogos'
import { useUploadHistory } from '../../hooks/dashboard/useUploadHistory'
import { SpinnerIcon } from '../icons'

const LABEL = 'mb-1 block text-xs font-medium text-slate-500'
const CAMPO =
  'field-inset w-full rounded-lg px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-magenta focus:ring-2 focus:ring-brand-magenta/30'
const BTN_RAISED =
  'btn-raised rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50'
const TH = 'px-3 py-2.5'
const TD = 'px-3 py-2.5 text-slate-600'

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
  const [editando, setEditando] = useState<HistorialItem | null>(null)
  const [eliminando, setEliminando] = useState<HistorialItem | null>(null)

  // Los filtros permanecen montados durante la carga y los errores: si se reemplazara toda la
  // sección por el indicador de carga, el campo de búsqueda perdería el foco en cada tecla.
  const resumen = loading
    ? 'Consultando…'
    : `${total} ${total === 1 ? 'carga' : 'cargas'}${hasFilters ? ' que coinciden con los filtros' : ' registradas'}`

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-xl font-bold text-brand-deep">Historial de Cargas</h2>
        <p className="text-sm text-slate-500" aria-live="polite">
          {resumen}
        </p>
      </div>

      <div
        role="search"
        aria-label="Filtros del historial"
        className="surface-raised grid gap-3 rounded-xl p-4 sm:grid-cols-2 lg:grid-cols-[minmax(12rem,2fr)_repeat(4,minmax(7rem,1fr))_auto] lg:items-end"
      >
        <div className="sm:col-span-2 lg:col-span-1">
          <label className={LABEL} htmlFor="history-q">
            Buscar
          </label>
          <input
            id="history-q"
            className={CAMPO}
            type="search"
            placeholder="Archivo o evento (549 / 550)"
            value={filtros.q}
            maxLength={100}
            onChange={(e) => setFiltro('q', e.target.value)}
          />
        </div>

        <div>
          <label className={LABEL} htmlFor="history-tipo">
            Evento
          </label>
          <select id="history-tipo" className={CAMPO} value={filtros.tipo} onChange={(e) => setFiltro('tipo', e.target.value)}>
            <option value="">Todos</option>
            <option value="mortalidad">550 · Mortalidad</option>
            <option value="morbilidad">549 · Morbilidad</option>
          </select>
        </div>

        <div>
          <label className={LABEL} htmlFor="history-year">
            Año
          </label>
          <select id="history-year" className={CAMPO} value={filtros.year} onChange={(e) => setFiltro('year', e.target.value)}>
            <option value="">Todos</option>
            {aniosDisponibles.map((anio) => (
              <option key={anio} value={String(anio)}>
                {anio}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={LABEL} htmlFor="history-month">
            Mes
          </label>
          <select id="history-month" className={CAMPO} value={filtros.month} onChange={(e) => setFiltro('month', e.target.value)}>
            <option value="">Todos</option>
            {MESES.map((mes, i) => (
              <option key={mes} value={String(i + 1)}>
                {mes}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={LABEL} htmlFor="history-week">
            Semana
          </label>
          <select id="history-week" className={CAMPO} value={filtros.week} onChange={(e) => setFiltro('week', e.target.value)}>
            <option value="">Todas</option>
            {SEMANAS.map((semana) => (
              <option key={semana} value={String(semana)}>
                {semana}
              </option>
            ))}
          </select>
        </div>

        {hasFilters && (
          <button className={`${BTN_RAISED} py-2`} type="button" onClick={clearFilters}>
            Limpiar filtros
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 py-6 text-sm text-slate-500">
          <SpinnerIcon className="size-5 animate-spin" />
          <span>Cargando historial...</span>
        </div>
      )}

      {!loading && error && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          {error}
          <button className={BTN_RAISED} type="button" onClick={reload}>
            Reintentar
          </button>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500">
          {hasFilters
            ? 'Ninguna carga coincide con la búsqueda o los filtros.'
            : 'No hay cargas registradas aún. Sube un archivo para comenzar.'}
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full min-w-[60rem] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <th className={TH}>Año</th>
                  <th className={TH}>Mes</th>
                  <th className={TH}>Semana</th>
                  <th className={TH}>Fecha</th>
                  <th className={TH}>Tipo</th>
                  <th className={TH}>Archivo</th>
                  <th className={`${TH} text-right`}>Registros</th>
                  <th className={TH}>Resumen</th>
                  <th className={TH}>Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/70">
                    <td className={`${TD} font-medium text-slate-800`}>{item.anio}</td>
                    <td className={TD}>{MESES[item.mes - 1] ?? item.mes}</td>
                    <td className={TD}>{item.semana}</td>
                    <td className={`${TD} whitespace-nowrap`}>{formatFecha(item.fecha_carga)}</td>
                    <td className={TD}>
                      <span
                        className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          item.tipo === 'mortalidad' ? 'bg-red-50 text-red-800' : 'bg-violet-50 text-violet-800'
                        }`}
                      >
                        {formatTipo(item.tipo)}
                      </span>
                    </td>
                    <td className={`${TD} max-w-[14rem] truncate`} title={item.nombre_archivo}>
                      {item.nombre_archivo}
                    </td>
                    <td className={`${TD} text-right tabular-nums`}>{item.total_registros}</td>
                    <td className={`${TD} min-w-[14rem] text-xs text-slate-500`}>{extractResumen(item.resumen)}</td>
                    <td className={`${TD} whitespace-nowrap`}>
                      <div className="flex gap-1">
                        <button type="button" className={BTN} aria-label={`Editar ${item.nombre_archivo}`} onClick={() => setEditando(item)}>
                          Editar
                        </button>
                        <button type="button" className={BTN_DANGER} aria-label={`Eliminar ${item.nombre_archivo}`} onClick={() => setEliminando(item)}>
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <button className={BTN_RAISED} disabled={page <= 1} onClick={() => setPage(page - 1)} type="button">
                ← Anterior
              </button>
              <span className="text-sm text-slate-600">
                Página {page} de {totalPages}
              </span>
              <button className={BTN_RAISED} disabled={page >= totalPages} onClick={() => setPage(page + 1)} type="button">
                Siguiente →
              </button>
            </div>
          )}
        </>
      )}
      {editando && (
        <EditarCargaDialogo
          item={editando}
          onCerrar={() => setEditando(null)}
          onGuardado={() => {
            setEditando(null)
            reload()
          }}
        />
      )}
      {eliminando && (
        <EliminarCargaDialogo
          item={eliminando}
          onCerrar={() => setEliminando(null)}
          onEliminado={() => {
            // Si era la única carga de la última página, retrocede para no quedar en una página vacía.
            if (items.length === 1 && page > 1) setPage(page - 1)
            setEliminando(null)
            reload()
          }}
        />
      )}
    </div>
  )
}
