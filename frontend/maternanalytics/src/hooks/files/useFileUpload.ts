import { useState, useCallback, useRef } from 'react'
import { API_URL, UPLOAD_TIMEOUT_MS, describeNetworkError, extractErrorMessage, fetchWithTimeout } from '../../api'
import { validateColumns, previewExcel, type FileValidationError, type FilePreview } from '../../utils/excelValidation'
import { COLUMNAS_MORTALIDAD, COLUMNAS_MORBILIDAD } from '../../constants/dashboardConstants'

export interface UseFileUploadOptions {
  onSuccess?: (createdAnalysis: { id: number; tipo: string }) => void
}

export function useFileUpload(tipo: 'mortalidad' | 'morbilidad', options?: UseFileUploadOptions) {
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<FileValidationError | null>(null)
  const [preview, setPreview] = useState<FilePreview | null>(null)
  const [validating, setValidating] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [done, setDone] = useState(false)
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)

  // Descarta resultados de validaciones antiguas si el usuario cambió de archivo mientras se leía.
  const validationRun = useRef(0)

  const columns = tipo === 'mortalidad' ? COLUMNAS_MORTALIDAD : COLUMNAS_MORBILIDAD

  const handleFile = useCallback(async (selectedFile: File | null) => {
    const run = ++validationRun.current
    if (!selectedFile) {
      setValidating(false)
      setFile(null)
      setError(null)
      setPreview(null)
      setDone(false)
      setAnalyzeError(null)
      return
    }

    setFile(selectedFile)
    setError(null)
    setPreview(null)
    setDone(false)
    setAnalyzeError(null)

    // El backend solo lee .xlsx; un archivo arrastrado con otra extensión no pasa por el `accept` del input.
    if (!/\.xlsx$/i.test(selectedFile.name)) {
      setError({ parseError: true })
      return
    }

    setValidating(true)

    const result = await validateColumns(selectedFile, columns, tipo)
    if (run !== validationRun.current) return
    setValidating(false)
    if (!result.valid) {
      setError(result)
      return
    }

    const filePreview = await previewExcel(selectedFile, columns, tipo)
    if (run !== validationRun.current) return
    setPreview(filePreview)
  }, [columns, tipo])

  const handleAnalyze = useCallback(async () => {
    if (!file || analyzing) return

    setAnalyzing(true)
    setDone(false)
    setAnalyzeError(null)

    try {
      const formData = new FormData()
      formData.append('archivo', file)
      formData.append('tipo', tipo)

      const res = await fetchWithTimeout(
        `${API_URL}/analisis/`,
        { method: 'POST', body: formData },
        UPLOAD_TIMEOUT_MS,
      )

      if (res.ok) {
        const createdAnalysis = await res.json()
        setDone(true)
        if (options?.onSuccess) {
          options.onSuccess(createdAnalysis)
        }
      } else {
        const err = await res.json().catch(() => null)
        // FastAPI devuelve { detail: string } (o una lista de errores en 422 de validación)
        setAnalyzeError(extractErrorMessage(err, 'Error al procesar el archivo.'))
      }
    } catch (err) {
      setAnalyzeError(describeNetworkError(err, 'No se pudo conectar con el servidor.'))
    } finally {
      setAnalyzing(false)
    }
  }, [file, analyzing, options, tipo])

  return {
    file,
    error,
    preview,
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
