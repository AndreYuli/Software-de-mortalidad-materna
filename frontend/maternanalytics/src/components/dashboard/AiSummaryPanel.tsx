import { useId, useState, type ReactNode } from 'react'
import { ChevronDown, Sparkles } from 'lucide-react'

export interface AiSummaryPanelProps {
  children: ReactNode
}

/** Panel plegable (cerrado por defecto) para los resúmenes generados por IA, con aviso de validación. */
export function AiSummaryPanel({ children }: AiSummaryPanelProps) {
  const [open, setOpen] = useState(false)
  const panelId = useId()

  return (
    <section className="rounded-xl border border-brand-magenta/30 bg-white shadow-sm">
      <h2 className="text-base">
        <button
          type="button"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((value) => !value)}
          className="flex w-full items-center gap-2 px-5 py-4 text-left font-semibold text-brand-deep"
        >
          <Sparkles className="size-5 text-brand-magenta" aria-hidden="true" />
          <span className="flex-1">Resumen ejecutivo (IA)</span>
          <ChevronDown
            className={`size-5 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </button>
      </h2>
      <div id={panelId} hidden={!open} className="space-y-4 border-t border-slate-200 px-5 py-4">
        <p className="text-sm text-slate-500">
          Generado automáticamente por IA local; requiere validación del equipo de vigilancia.
        </p>
        {children}
      </div>
    </section>
  )
}
