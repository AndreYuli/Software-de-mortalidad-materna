import { useState } from 'react'
import { obtenerNarrativa } from '../api'
import type { FiltrosNarrativa, TipoNarrativa } from '../types'

interface NarrativaIAProps {
  analisisId: number
  tipo: TipoNarrativa
  titulo: string
  filtros?: FiltrosNarrativa
}

type Estado = 'idle' | 'loading' | 'success' | 'unavailable' | 'error'

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
    <div className="chart-ai-insight narrativa-ia">
      <span>{titulo}</span>

      {estado === 'idle' && (
        <div>
          <button type="button" className="btn-mini-toggle active" onClick={() => generar(false)}>
            Generar resumen IA
          </button>
        </div>
      )}

      {estado === 'loading' && <p role="status">Generando narrativa...</p>}

      {estado === 'success' && (
        <>
          <p>{narrativa}</p>
          <div>
            <button type="button" className="btn-mini-toggle active" onClick={() => generar(true)}>
              Regenerar
            </button>
          </div>
        </>
      )}

      {estado === 'error' && (
        <>
          <p role="alert">No se pudo generar la narrativa. Intenta de nuevo.</p>
          <div>
            <button type="button" className="btn-mini-toggle active" onClick={() => generar(false)}>
              Reintentar
            </button>
          </div>
        </>
      )}
    </div>
  )
}
