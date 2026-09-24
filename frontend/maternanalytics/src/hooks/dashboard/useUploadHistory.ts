import { useState, useEffect, useCallback } from 'react'
import {
  fetchHistorial,
  type HistorialFiltros,
  type HistorialItem,
  type HistorialResponse,
} from '../../api'

const DEBOUNCE_BUSQUEDA_MS = 300
const SIN_FILTROS: Required<HistorialFiltros> = { q: '', tipo: '', year: '', month: '', week: '' }

export interface UseUploadHistoryReturn {
  items: HistorialItem[]
  loading: boolean
  error: string | null
  page: number
  perPage: number
  total: number
  totalPages: number
  aniosDisponibles: number[]
  filtros: Required<HistorialFiltros>
  hasFilters: boolean
  setFiltro: (campo: keyof HistorialFiltros, valor: string) => void
  clearFilters: () => void
  setPage: (p: number) => void
  reload: () => void
}

export function useUploadHistory(perPage = 20): UseUploadHistoryReturn {
  const [items, setItems] = useState<HistorialItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [aniosDisponibles, setAniosDisponibles] = useState<number[]>([])
  const [reloadKey, setReloadKey] = useState(0)
  const [filtros, setFiltros] = useState<Required<HistorialFiltros>>(SIN_FILTROS)
  // El texto se aplica con retraso para no consultar al servidor en cada tecla.
  const [busqueda, setBusqueda] = useState('')

  const reload = useCallback(() => setReloadKey((k) => k + 1), [])

  useEffect(() => {
    if (filtros.q === busqueda) return
    const timer = setTimeout(() => {
      setBusqueda(filtros.q)
      setPage(1)
    }, DEBOUNCE_BUSQUEDA_MS)
    return () => clearTimeout(timer)
  }, [filtros.q, busqueda])

  const setFiltro = useCallback((campo: keyof HistorialFiltros, valor: string) => {
    setFiltros((prev) => ({ ...prev, [campo]: valor }))
    // Los selectores aplican de inmediato y vuelven a la primera página; el texto lo hace el debounce.
    if (campo !== 'q') setPage(1)
  }, [])

  const clearFilters = useCallback(() => {
    setFiltros(SIN_FILTROS)
    setBusqueda('')
    setPage(1)
  }, [])

  const { tipo, year, month, week } = filtros

  useEffect(() => {
    const controller = new AbortController()
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchHistorial(page, perPage, { q: busqueda, tipo, year, month, week }, controller.signal)
      .then((res: HistorialResponse) => {
        if (!cancelled) {
          setItems(res.items)
          setTotal(res.total)
          setTotalPages(res.total_pages)
          setAniosDisponibles(res.anios_disponibles ?? [])
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Error al cargar el historial'
          setError(message)
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
      controller.abort()
    }
  }, [page, perPage, reloadKey, busqueda, tipo, year, month, week])

  const hasFilters = Boolean(filtros.q.trim() || tipo || year || month || week)

  return {
    items,
    loading,
    error,
    page,
    perPage,
    total,
    totalPages,
    aniosDisponibles,
    filtros,
    hasFilters,
    setFiltro,
    clearFilters,
    setPage,
    reload,
  }
}
