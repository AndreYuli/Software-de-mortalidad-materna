import type { FileValidationError, FilePreview } from '../../utils/excelValidation'
import { UploadCard } from './UploadCard'
import { FilePreviewTable } from './FilePreviewTable'
import { CheckIcon, ErrorIcon, SpinnerIcon, SendIcon } from '../icons'

interface UploadSectionProps {
  title: string
  description: string
  eventLabel: string
  file: File | null // 1. Tipado nativo consistente con 'onFile'
  error: FileValidationError | null
  preview: FilePreview | null
  validating: boolean
  done: boolean
  analyzeError: string | null
  analyzing: boolean
  actionLabel: string
  onFile: (file: File | null) => void
  onAnalyze: () => void
}

export function UploadSection({
  title,
  description,
  file,
  error,
  preview,
  validating,
  done,
  analyzeError,
  analyzing,
  actionLabel,
  onFile,
  onAnalyze,
  eventLabel,
}: UploadSectionProps) {
  // 2. Prevenir re-envíos si el análisis ya finalizó exitosamente (done)
  const isEmptyFile = Boolean(file && !error && preview && preview.totalRows === 0)
  const isDisabled = !file || Boolean(error) || validating || analyzing || done || isEmptyFile

  const handleRemove = () => {
    onFile(null)
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
      {/* Cabecera */}
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold leading-tight text-brand-deep">{title}</h1>
        <p className="text-sm text-slate-500">{description}</p>
      </header>

      {/* Drop Zone + Tarjeta de Archivo */}
      <UploadCard
        file={file}
        error={error}
        validating={validating}
        onFile={onFile}
        onRemove={handleRemove}
        eventLabel={eventLabel}
      />

      {/* Vista previa del archivo: columnas, primeras filas y cantidad de registros */}
      {file && !error && preview && <FilePreviewTable preview={preview} />}

      {/* Mensaje de Éxito (A11y mejorado con role="status") */}
      {done && (
        <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status" aria-live="polite">
          <CheckIcon className="size-5 shrink-0" />
          <span>Análisis guardado correctamente. Puedes verlo en «Dashboard Analítico» o en «Historial de Cargas».</span>
        </div>
      )}

      {isEmptyFile && (
        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          <ErrorIcon className="size-5 shrink-0" />
          <span>El archivo tiene los encabezados correctos pero no contiene registros.</span>
        </div>
      )}

      {/* Error de Análisis (A11y mejorado con role="alert") */}
      {analyzeError && (
        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          <ErrorIcon className="size-5 shrink-0" />
          <span>{analyzeError}</span>
        </div>
      )}

      {/* Botón de Envío */}
      <button
        className="btn-primary-raised inline-flex items-center justify-center gap-2 self-end rounded-lg px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50 disabled:saturate-50"
        disabled={isDisabled}
        onClick={onAnalyze}
        type="button"
      >
        {analyzing ? (
          <>
            <SpinnerIcon className="size-4 animate-spin" aria-hidden="true" />
            Procesando registros...
          </>
        ) : (
          <>
            <SendIcon className="size-4" aria-hidden="true" />
            {actionLabel}
          </>
        )}
      </button>
    </div>
  )
}