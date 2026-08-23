import { useState, useCallback } from 'react'
import { API_URL } from '../../api'
import { validateColumns, type FileValidationError } from '../../utils/excelValidation'
import { COLUMNAS_MORTALIDAD, COLUMNAS_MORBILIDAD } from '../../constants/dashboardConstants'

export interface UseFileUploadOptions {
  onSuccess?: (createdAnalysis: { id: number; tipo: string }) => void
}

export function useFileUpload(tipo: 'mortalidad' | 'morbilidad', options?: UseFileUploadOptions) {
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<FileValidationError | null>(null)
  const [validating, setValidating] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [done, setDone] = useState(false)
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)

  const columns = tipo === 'mortalidad' ? COLUMNAS_MORTALIDAD : COLUMNAS_MORBILIDAD

  const handleFile = useCallback(async (selectedFile: File | null) => {
    if (!selectedFile) {
      setFile(null)
      setError(null)
      setDone(false)
      setAnalyzeError(null)
      return
    }

    setFile(selectedFile)
    setError(null)
    setDone(false)
    setAnalyzeError(null)
    setValidating(true)

    const result = await validateColumns(selectedFile, columns, tipo)
    setValidating(false)
    if (!result.valid) {
      setError(result)
    }
  }, [columns, tipo])

  const handleAnalyze = useCallback(async () => {
    if (!file) return

    setAnalyzing(true)
    setDone(false)
    setAnalyzeError(null)

    try {
      const formData = new FormData()
      formData.append('archivo', file)
      formData.append('tipo', tipo)

      const res = await fetch(`${API_URL}/analisis/`, {
        method: 'POST',
        body: formData,
      })

      if (res.ok) {
        const createdAnalysis = await res.json()
        setDone(true)
        if (options?.onSuccess) {
          options.onSuccess(createdAnalysis)
        }
      } else {
        const err = await res.json()
        if (Array.isArray(err.columnas_faltantes) && err.columnas_faltantes.length) {
          setAnalyzeError(
            `Faltan columnas requeridas: ${err.columnas_faltantes.slice(0, 6).join(', ')}${
              err.columnas_faltantes.length > 6 ? '…' : ''
            }`,
          )
        } else {
          setAnalyzeError(err.error || 'Error al procesar el archivo.')
        }
      }
    } catch {
      setAnalyzeError('No se pudo conectar con el servidor.')
    } finally {
      setAnalyzing(false)
    }
  }, [file, options, tipo])

  return {
    file,
    error,
    validating,
    analyzing,
    done,
    analyzeError,
    setDone,
    setAnalyzeError,
    handleFile,
    handleAnalyze,
  }
}
