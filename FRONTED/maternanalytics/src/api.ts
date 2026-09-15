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

export interface HistorialItem {
  id: number
  tipo: string
  nombre_archivo: string
  archivo: string
  fecha_carga: string
  total_registros: number
  resumen: Record<string, unknown>
}

export interface HistorialResponse {
  items: HistorialItem[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export async function fetchHistorial(
  page = 1,
  perPage = 20,
): Promise<HistorialResponse> {
  const response = await fetch(`${API_URL}/analisis/historial/?page=${page}&per_page=${perPage}`)
  if (!response.ok) throw new Error(`Error al obtener historial: ${response.status}`)
  const data = await response.json()
  return data as HistorialResponse
}

export interface CruceResponse {
  categorias_socio: string[]
  categorias_clinica: string[]
  matriz: number[][]
  total: number
  var_socio_label: string
  var_clinica_label: string
}

export async function fetchCruce(
  analisisId: number,
  varSocio: string,
  varClinica: string,
): Promise<CruceResponse> {
  const params = new URLSearchParams({ var_socio: varSocio, var_clinica: varClinica })
  const response = await fetch(`${API_URL}/analisis/${analisisId}/cruce/?${params.toString()}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `Error al calcular el cruce: ${response.status}`)
  }
  return (await response.json()) as CruceResponse
}
