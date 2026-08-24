import './UploadSection.css'
import type { FileValidationError } from '../../utils/excelValidation'
import { UploadCard } from './UploadCard'
import { CheckIcon, ErrorIcon, SpinnerIcon, SendIcon } from '../icons'

interface UploadSectionProps {
  title: string
  description: string
  eventLabel: string
  file: File | null // 1. Tipado nativo consistente con 'onFile'
  error: FileValidationError | null
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
  const isDisabled = !file || Boolean(error) || validating || analyzing || done

  const handleRemove = () => {
    onFile(null)
  }

  return (
    <div className="upload-section-premium">
      {/* Cabecera */}
      <header className="upload-section-header">
        <h1 className="upload-section-title">{title}</h1>
        <p className="upload-section-desc">{description}</p>
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

      {/* Mensaje de Éxito (A11y mejorado con role="status") */}
      {done && (
        <div className="upload-success-msg" role="status" aria-live="polite">
          <CheckIcon />
          <span>Análisis guardado correctamente. Puedes verlo en «Análisis guardados».</span>
        </div>
      )}

      {/* Error de Análisis (A11y mejorado con role="alert") */}
      {analyzeError && (
        <div className="upload-analyze-error" role="alert">
          <ErrorIcon />
          <span>{analyzeError}</span>
        </div>
      )}

      {/* Botón de Envío */}
      <button
        className={`upload-submit-btn ${isDisabled ? 'disabled' : ''} ${analyzing ? 'processing' : ''}`}
        disabled={isDisabled}
        onClick={onAnalyze}
        type="button"
      >
        {analyzing ? (
          <>
            <SpinnerIcon className="upload-spinner" aria-hidden="true" />
            Procesando registros...
          </>
        ) : (
          <>
            {/* 3. Estilo inline removido: la clase maneja sus dimensiones en el CSS */}
            <SendIcon className="upload-send-icon" aria-hidden="true" />
            {actionLabel}
          </>
        )}
      </button>
    </div>
  )
}