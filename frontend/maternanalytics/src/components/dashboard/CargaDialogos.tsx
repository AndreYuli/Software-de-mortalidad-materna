import { useState, type FormEvent, type ReactNode } from 'react'
import { actualizarCarga, eliminarCarga, type HistorialItem } from '../../api'

export const BTN = 'rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100'
export const BTN_DANGER = 'rounded-md border border-red-300 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50'
const INPUT =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-magenta focus:ring-2 focus:ring-brand-magenta/30'

/** Fecha de la carga como la ve el usuario (hora de Colombia) para un `datetime-local`. */
function toInputLocal(iso: string): string {
  const tieneZona = /(Z|[+-]\d{2}:?\d{2})$/.test(iso)
  const d = new Date(tieneZona ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('sv-SE', { timeZone: 'America/Bogota' }).replace(' ', 'T').slice(0, 16)
}

function Dialogo({ titulo, onCerrar, children }: { titulo: string; onCerrar: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onCerrar}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-3 text-lg font-semibold text-brand-deep">{titulo}</h3>
        {children}
      </div>
    </div>
  )
}

interface EditarProps {
  item: HistorialItem
  onCerrar: () => void
  onGuardado: () => void
}

export function EditarCargaDialogo({ item, onCerrar, onGuardado }: EditarProps) {
  const [nombre, setNombre] = useState(item.nombre_archivo)
  const [fecha, setFecha] = useState(toInputLocal(item.fecha_carga))
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const guardar = async (e: FormEvent) => {
    e.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      await actualizarCarga(item.id, { nombre_archivo: nombre, ...(fecha ? { fecha_carga: fecha } : {}) })
      onGuardado()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar la carga')
      setGuardando(false)
    }
  }

  return (
    <Dialogo titulo="Editar carga" onCerrar={onCerrar}>
      <form onSubmit={guardar} className="flex flex-col gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500" htmlFor="editar-nombre">
            Nombre del archivo
          </label>
          <input
            id="editar-nombre"
            className={INPUT}
            value={nombre}
            maxLength={255}
            onChange={(e) => setNombre(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500" htmlFor="editar-fecha">
            Fecha de la carga
          </label>
          <input
            id="editar-fecha"
            className={INPUT}
            type="datetime-local"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
          />
          <p className="mt-1 text-xs text-slate-500">Define el año, el mes y la semana en que aparece la carga.</p>
        </div>
        {error && (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <button type="button" className={BTN} onClick={onCerrar} disabled={guardando}>
            Cancelar
          </button>
          <button type="submit" className={BTN} disabled={guardando || !nombre.trim()}>
            {guardando ? 'Guardando…' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </Dialogo>
  )
}

interface EliminarProps {
  item: HistorialItem
  onCerrar: () => void
  onEliminado: () => void
}

export function EliminarCargaDialogo({ item, onCerrar, onEliminado }: EliminarProps) {
  const [eliminando, setEliminando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const confirmar = async () => {
    setEliminando(true)
    setError(null)
    try {
      await eliminarCarga(item.id)
      onEliminado()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo eliminar la carga')
      setEliminando(false)
    }
  }

  return (
    <Dialogo titulo="Eliminar carga" onCerrar={onCerrar}>
      <p className="mb-3 text-sm text-slate-600">
        ¿Eliminar la carga <strong>{item.nombre_archivo}</strong> del historial? Esta acción no se puede deshacer.
      </p>
      {error && (
        <p role="alert" className="mb-3 text-sm text-red-700">
          {error}
        </p>
      )}
      <div className="flex justify-end gap-2">
        <button type="button" className={BTN} onClick={onCerrar} disabled={eliminando}>
          Cancelar
        </button>
        <button type="button" className={BTN_DANGER} onClick={confirmar} disabled={eliminando}>
          {eliminando ? 'Eliminando…' : 'Eliminar'}
        </button>
      </div>
    </Dialogo>
  )
}
