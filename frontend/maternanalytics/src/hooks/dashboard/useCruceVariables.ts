import { useEffect, useState } from 'react'
import { fetchCruce, type CruceResponse } from '../../api'

export interface UseCruceVariablesReturn {
  varSocio: string
  varClinica: string
  setVarSocio: (v: string) => void
  setVarClinica: (v: string) => void
  data: CruceResponse | null
  loading: boolean
  error: string | null
}

export function useCruceVariables(
  analisisId: number | null,
  defaultVarSocio: string,
  defaultVarClinica: string,
): UseCruceVariablesReturn {
  const [varSocio, setVarSocio] = useState(defaultVarSocio)
  const [varClinica, setVarClinica] = useState(defaultVarClinica)
  const [data, setData] = useState<CruceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!analisisId) {
      setData(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchCruce(analisisId, varSocio, varClinica)
      .then((res) => {
        if (!cancelled) {
          setData(res)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Error al calcular el cruce'
          setError(message)
          setData(null)
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [analisisId, varSocio, varClinica])

  return { varSocio, varClinica, setVarSocio, setVarClinica, data, loading, error }
}
