import { z } from 'zod'
import type { FiltrosNarrativa, NarrativaResponse, TipoNarrativa } from './types'

const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
export const API_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl

const NarrativaResponseSchema = z.object({
  narrativa: z.string(),
  modelo: z.string(),
  generado_en: z.string(),
  desde_cache: z.boolean(),
})

export async function obtenerNarrativa(
  analisisId: number,
  tipo: TipoNarrativa,
  filtros: FiltrosNarrativa = {},
  regenerar = false,
): Promise<NarrativaResponse | null> {
  const params = new URLSearchParams()
  if (filtros.year) params.append('year', filtros.year)
  if (filtros.month) params.append('month', filtros.month)
  if (filtros.tipoClustering) params.append('tipo_clustering', filtros.tipoClustering)
  if (filtros.nClusters) params.append('n_clusters', String(filtros.nClusters))
  if (regenerar) params.append('regenerar', 'true')

  const response = await fetch(`${API_URL}/analisis/${analisisId}/narrativa/${tipo}/?${params.toString()}`)

  if (response.status === 503) return null
  if (!response.ok) throw new Error(`Error al obtener narrativa: ${response.status}`)

  const data = await response.json()
  return NarrativaResponseSchema.parse(data)
}
