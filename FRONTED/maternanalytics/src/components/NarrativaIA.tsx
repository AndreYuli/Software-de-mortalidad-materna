import { useState } from 'react'
import { obtenerNarrativa } from '../api'
import type { FiltrosNarrativa, TipoNarrativa } from '../types'

interface NarrativaIAProps {
  analisisId: number
  tipo: TipoNarrativa
  titulo: string
  filtros?: FiltrosNarrativa
}

type Estado = 'idle' | 'loading' | 'success' | 'unavailable'

export default function NarrativaIA({ analisisId, tipo, titulo, filtros = {} }: NarrativaIAProps) {
  const [estado, setEstado] = useState<Estado>('idle')
  const [narrativa, setNarrativa] = useState('')

  const generar = async (regenerar: boolean) => {
    setEstado('loading')
    const resultado = await obtenerNarrativa(analisisId, tipo, filtros, regenerar)
    if (resultado === null) {
      console.debug(`NarrativaIA: IA-SERVICE no disponible para tipo=${tipo}, analisisId=${analisisId}`)
      setEstado('unavailable')
      return
    }
    setNarrativa(resultado.narrativa)
    setEstado('success')
  }

  if (estado === 'unavailable') return null

  return (
    <div className="narrativa-ia">
      <span className="ai-badge-pulsing">Inteligencia IA</span>
      <h3 className="ai-title">{titulo}</h3>

      {estado === 'idle' && (
        <button className="btn-mini-toggle" onClick={() => generar(false)}>
          Generar resumen IA
        </button>
      )}

      {estado === 'loading' && <p className="ai-no-data">Generando narrativa...</p>}

      {estado === 'success' && (
        <div className="ai-content">
          <p>{narrativa}</p>
          <button className="btn-mini-toggle" onClick={() => generar(true)}>
            Regenerar
          </button>
        </div>
      )}
    </div>
  )
}
