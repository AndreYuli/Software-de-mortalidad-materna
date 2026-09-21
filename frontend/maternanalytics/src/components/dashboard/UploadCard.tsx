import { useState, useRef, type DragEvent, type ChangeEvent } from 'react'
import { FileValidationError } from '../../utils/excelValidation'

interface UploadCardProps {
  onFile: (file: File) => void
  onRemove: () => void
  eventLabel: string
  file: { name: string } | null
  error: FileValidationError | null
  validating: boolean
}

// Componente de carga de archivos — Diseño premium drag & drop
export function UploadCard({ onFile, file, error, validating, onRemove, eventLabel }: UploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const triggerFileInput = () => {
    inputRef.current?.click()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      triggerFileInput()
    }
  }

  const processSelectedFile = (selectedFile: File) => {
    const MAX_SIZE_BYTES = 15 * 1024 * 1024 // 15MB
    if (selectedFile.size > MAX_SIZE_BYTES) {
      alert('El archivo supera el límite permitido de 15MB.')
      onRemove()
      return
    }
    onFile(selectedFile)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) processSelectedFile(dropped)
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) processSelectedFile(e.target.files[0])
    // Sin esto, seleccionar el mismo archivo dos veces seguidas (p. ej. tras
    // "Eliminar archivo") no dispara 'change' porque el input nativo no
    // considera que su valor cambió.
    e.target.value = ''
  }

  const missingColumns = error?.missing ?? []
  const missingColumnsLabel = missingColumns.length === 1 ? 'columna' : 'columnas'

  return (
    <div className="flex flex-col gap-3">
      <input ref={inputRef} type="file" accept=".xlsx" className="hidden" onChange={handleChange} />

      {/* Drop Zone */}
      <div
        className={`flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed px-6 py-8 text-center transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-magenta/40 ${
          dragging
            ? 'border-brand-magenta bg-fuchsia-50'
            : error && !file
              ? 'border-red-300 bg-red-50/60'
              : file && !error
                ? 'border-emerald-300 bg-emerald-50/60'
                : 'border-slate-300 bg-slate-50 hover:border-brand-magenta hover:bg-fuchsia-50/50'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={triggerFileInput}
        role="button"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        aria-label={`Cargar archivo Excel para ${eventLabel}`}
      >
        {/* Cloud Upload Icon */}
        <div className="mb-1 size-12 text-brand-magenta">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="16 16 12 12 8 16" />
            <line x1="12" y1="12" x2="12" y2="21" />
            <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
          </svg>
        </div>

        {validating ? (
          <>
            <p className="text-base font-semibold text-brand-deep">Validando estructura...</p>
            <p className="text-sm text-slate-500">Comprobando columnas requeridas</p>
          </>
        ) : file && !error ? (
          <>
            <p className="text-base font-semibold text-brand-deep">¡Archivo cargado con éxito!</p>
            <p className="text-sm font-medium text-emerald-700">📄 {file.name}</p>
          </>
        ) : (
          <>
            <p className="text-base font-semibold text-brand-deep">Arrastra tu archivo aquí o <span className="text-brand-magenta underline">haz clic para explorar</span></p>
            <p className="text-sm text-slate-500">Soportado: .xlsx (Máximo 15MB)</p>
          </>
        )}
      </div>

      {/* File Preview Card */}
      {file && !error && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
          <div className="flex min-w-0 items-center gap-3">
            <div className="size-9 shrink-0 rounded-lg bg-slate-100 p-2 text-slate-600">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-sm font-medium text-slate-800" title={file.name}>{file.name}</span>
              <span className="inline-flex items-center gap-1 text-xs text-emerald-700 [&_svg]:size-3.5">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Archivo válido y listo
              </span>
            </div>
          </div>
          <button
            data-prevent-open="true"
            className="btn-raised shrink-0 rounded-lg p-2 text-slate-600 hover:text-red-700 [&_svg]:size-4"
            onClick={(e) => { e.stopPropagation(); onRemove() }}
            title="Eliminar archivo"
            type="button"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
              <path d="M10 11v6"/>
              <path d="M14 11v6"/>
              <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
            </svg>
          </button>
        </div>
      )}

      {/* Error Panel */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" data-prevent-open="true">
          {error.parseError ? (
            <p className="flex items-center gap-2 font-semibold [&_svg]:size-4 [&_svg]:shrink-0">No se pudo leer el archivo. Verifica que sea un Excel válido.</p>
          ) : (
            <>
              <p className="flex items-center gap-2 font-semibold [&_svg]:size-4 [&_svg]:shrink-0">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Faltan {missingColumns.length} {missingColumnsLabel}
              </p>
              <ul className="mt-2 list-inside list-disc text-xs">
                {missingColumns.slice(0, 8).map((col) => <li key={col}>{col}</li>)}
                {missingColumns.length > 8 && <li className="list-none italic text-red-700">…y {missingColumns.length - 8} más</li>}
              </ul>
              <button className="btn-raised mt-3 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700" onClick={triggerFileInput} type="button">Intentar con otro archivo</button>
            </>
          )}
        </div>
      )}
    </div>
  )
}