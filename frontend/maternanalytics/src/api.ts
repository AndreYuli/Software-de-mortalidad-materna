import { z } from 'zod'
import type { FiltrosNarrativa, NarrativaResponse, TipoNarrativa } from './types'

const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
export const API_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl

/** Tiempo máximo de espera por defecto para una petición al backend. */
export const REQUEST_TIMEOUT_MS = 30_000
/** Las cargas de Excel procesan y persisten miles de filas: se les da más margen. */
export const UPLOAD_TIMEOUT_MS = 180_000

const SESSION_KEYS = ['token', 'username', 'user_email'] as const

/** Elimina del navegador todos los datos de la sesión. */
export function clearSession(): void {
  SESSION_KEYS.forEach((key) => localStorage.removeItem(key))
}

/** Login y registro son públicos: no llevan Bearer ni disparan la expulsión por 401. */
function isPublicAuthUrl(url: string): boolean {
  return url.includes('/auth/')
}

/**
 * `fetch` con límite de tiempo. Si vence, lanza un Error con name 'TimeoutError'.
 * Respeta un `signal` externo (p. ej. el AbortController de un efecto).
 * Adjunta `Authorization: Bearer <token>` a las llamadas protegidas y, si el backend
 * responde 401, elimina la sesión local y redirige a /login.
 */
export async function fetchWithTimeout(
  input: string,
  init: RequestInit = {},
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)
  const external = init.signal
  const onExternalAbort = () => controller.abort()
  if (external) {
    if (external.aborted) controller.abort()
    else external.addEventListener('abort', onExternalAbort, { once: true })
  }
  const headers = new Headers(init.headers)
  const token = localStorage.getItem('token')
  const isProtected = !isPublicAuthUrl(input)
  if (token && isProtected && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  try {
    const response = await fetch(input, { ...init, headers, signal: controller.signal })
    if (response.status === 401 && isProtected) {
      clearSession()
      if (window.location.pathname !== '/login') window.location.replace('/login')
    }
    return response
  } catch (err) {
    if (timedOut) {
      const timeoutError = new Error('El servidor tardó demasiado en responder. Intenta de nuevo.')
      timeoutError.name = 'TimeoutError'
      throw timeoutError
    }
    throw err
  } finally {
    clearTimeout(timer)
    external?.removeEventListener('abort', onExternalAbort)
  }
}

/**
 * Extrae un mensaje legible del cuerpo de error de FastAPI. `detail` puede ser
 * un string (HTTPException) o una lista de objetos (422 de validación): renderizar
 * la lista tal cual en React lanza una excepción y deja la pantalla en blanco.
 */
export function extractErrorMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown; error?: unknown } | null)?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown }
    if (typeof first?.msg === 'string') return first.msg
  }
  const error = (body as { error?: unknown } | null)?.error
  if (typeof error === 'string' && error.trim()) return error
  return fallback
}

/** Mensaje al usuario para un fallo de red (timeout vs. sin conexión). */
export function describeNetworkError(err: unknown, fallback: string): string {
  return err instanceof Error && err.name === 'TimeoutError' ? err.message : fallback
}

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

  const response = await fetchWithTimeout(`${API_URL}/analisis/${analisisId}/narrativa/${tipo}/?${params.toString()}`, {}, 120_000)

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
  const response = await fetchWithTimeout(`${API_URL}/analisis/historial/?page=${page}&per_page=${perPage}`)
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
  const response = await fetchWithTimeout(`${API_URL}/analisis/${analisisId}/cruce/?${params.toString()}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(extractErrorMessage(body, `Error al calcular el cruce: ${response.status}`))
  }
  return (await response.json()) as CruceResponse
}
