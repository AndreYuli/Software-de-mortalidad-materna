import { useState, useEffect, useCallback } from 'react'
import { fetchHistorial, type HistorialItem, type HistorialResponse } from '../../api'

export interface UseUploadHistoryReturn {
  items: HistorialItem[]
  loading: boolean
  error: string | null
  page: number
  perPage: number
  total: number
  totalPages: number
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
  const [reloadKey, setReloadKey] = useState(0)

  const reload = useCallback(() => setReloadKey((k) => k + 1), [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchHistorial(page, perPage)
      .then((res: HistorialResponse) => {
        if (!cancelled) {
          setItems(res.items)
          setTotal(res.total)
          setTotalPages(res.total_pages)
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
    return () => { cancelled = true }
  }, [page, perPage, reloadKey])

  return {
    items,
    loading,
    error,
    page,
    perPage,
    total,
    totalPages,
    setPage,
    reload,
  }
}
