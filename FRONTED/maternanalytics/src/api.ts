import type { FiltrosNarrativa, NarrativaResponse, TipoNarrativa } from './types'

export const API_URL = 'http://localhost:8000/api'

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

  return response.json() as Promise<NarrativaResponse>
}
