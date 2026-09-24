import { useState } from 'react'
import { Droplet, FileText, Hospital, type LucideIcon } from 'lucide-react'

export interface WelcomeStateProps {
  onGoToUpload: (view: 'mortalidad' | 'morbilidad') => void
}

const PRIMARY_BUTTON_CLASS =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-brand-magenta px-5 py-2.5 font-semibold text-white transition hover:opacity-90'

interface ChoiceButtonProps {
  icon: LucideIcon
  label: string
  sublabel: string
  onClick: () => void
}

function ChoiceButton({ icon: Icon, label, sublabel, onClick }: ChoiceButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center gap-1 rounded-xl border border-slate-200 p-4 transition hover:border-brand-magenta hover:bg-brand-magenta/5"
    >
      <span className="mb-1 flex size-10 items-center justify-center rounded-full bg-brand-magenta/10 text-brand-magenta">
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <span className="font-semibold text-brand-deep">{label}</span>
      <span className="text-xs text-slate-500">{sublabel}</span>
    </button>
  )
}

export function WelcomeState({ onGoToUpload }: WelcomeStateProps) {
  const [showChoices, setShowChoices] = useState(false)

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-brand-magenta/10 text-brand-magenta">
          <FileText className="size-7" aria-hidden="true" />
        </div>
        <h2 className="text-xl font-semibold text-brand-deep">Análisis Epidemiológico</h2>
        <p className="mx-auto mb-6 mt-2 max-w-md text-sm text-slate-500">
          Aún no hay datos para analizar. Carga los registros de los Eventos 549 (Morbilidad) y 550 (Mortalidad) del
          SIVIGILA para generar el panel de control y los modelos de clustering.
        </p>

        {!showChoices ? (
          <button type="button" className={PRIMARY_BUTTON_CLASS} onClick={() => setShowChoices(true)}>
            Importar Datos Epidemiológicos
          </button>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            <ChoiceButton
              icon={Droplet}
              label="Mortalidad"
              sublabel="Evento 550"
              onClick={() => onGoToUpload('mortalidad')}
            />
            <ChoiceButton
              icon={Hospital}
              label="Morbilidad Extrema"
              sublabel="Evento 549"
              onClick={() => onGoToUpload('morbilidad')}
            />
          </div>
        )}
      </div>
    </div>
  )
}
