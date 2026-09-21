import { useState } from 'react'
import { Loader2, RefreshCw, Sparkles } from 'lucide-react'
import { obtenerNarrativa } from '../api'
import type { FiltrosNarrativa, TipoNarrativa } from '../types'

interface NarrativaIAProps {
  analisisId: number
  tipo: TipoNarrativa
  titulo: string
  filtros?: FiltrosNarrativa
}

type Estado = 'idle' | 'loading' | 'success' | 'unavailable' | 'error'

const BUTTON_CLASS =
  'inline-flex items-center gap-2 rounded-lg bg-brand-magenta px-3 py-1.5 text-sm font-semibold text-white transition hover:opacity-90'

// Opcional y asíncrona: no se genera nada hasta que la persona lo pide, y si el servicio de IA
// no está disponible el bloque desaparece sin afectar al resto del dashboard.
export default function NarrativaIA({ analisisId, tipo, titulo, filtros = {} }: NarrativaIAProps) {
  const [estado, setEstado] = useState<Estado>('idle')
  const [narrativa, setNarrativa] = useState('')

  const generar = async (regenerar: boolean) => {
    setEstado('loading')
    try {
      const resultado = await obtenerNarrativa(analisisId, tipo, filtros, regenerar)
      if (resultado === null) {
        console.debug(`NarrativaIA: IA-SERVICE no disponible para tipo=${tipo}, analisisId=${analisisId}`)
        setEstado('unavailable')
        return
      }
      setNarrativa(resultado.narrativa)
      setEstado('success')
    } catch (err) {
      console.error('NarrativaIA: error al obtener la narrativa', err)
      setEstado('error')
    }
  }

  if (estado === 'unavailable') return null

  return (
    <div className="mt-4 rounded-xl border border-brand-magenta/30 bg-brand-magenta/5 p-4">
      <div className="mb-3 flex items-center gap-2 font-semibold text-brand-deep">
        <Sparkles className="size-5 text-brand-magenta" aria-hidden="true" />
        <span>{titulo}</span>
      </div>

      {estado === 'idle' && (
        <button type="button" className={BUTTON_CLASS} onClick={() => generar(false)}>
          Generar resumen IA
        </button>
      )}

      {estado === 'loading' && (
        <p role="status" className="flex items-center gap-2 text-sm text-slate-600">
          <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          Generando narrativa...
        </p>
      )}

      {estado === 'success' && (
        <>
          <p className="text-sm leading-relaxed text-slate-700">{narrativa}</p>
          <div className="mt-3 flex justify-end">
            <button type="button" className={BUTTON_CLASS} onClick={() => generar(true)}>
              <RefreshCw className="size-4" aria-hidden="true" />
              Regenerar
            </button>
          </div>
        </>
      )}

      {estado === 'error' && (
        <>
          <p role="alert" className="text-sm text-red-700">
            No se pudo generar la narrativa. Intenta de nuevo.
          </p>
          <div className="mt-3">
            <button type="button" className={BUTTON_CLASS} onClick={() => generar(false)}>
              <RefreshCw className="size-4" aria-hidden="true" />
              Reintentar
            </button>
          </div>
        </>
      )}
    </div>
  )
}
