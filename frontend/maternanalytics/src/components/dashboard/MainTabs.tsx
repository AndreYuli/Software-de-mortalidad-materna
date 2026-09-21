import type { MainTab } from '../../hooks/navigation/useDashboardTabs'

export interface MainTabsProps {
  active: MainTab
  onChange: (tab: MainTab) => void
}

const TABS: { key: MainTab; label: string }[] = [
  { key: 'generalidades', label: 'Generalidades' },
  { key: 'morbilidad', label: 'Morbilidad (Ev. 549)' },
  { key: 'mortalidad', label: 'Mortalidad (Ev. 550)' },
]

export function MainTabs({ active, onChange }: MainTabsProps) {
  return (
    // El borde gris va en el contenedor exterior; el interior (con scroll horizontal) baja 1 px para que
    // la línea de la pestaña activa lo tape sin que el overflow la recorte.
    <div className="border-b border-slate-200">
      <div role="tablist" aria-label="Secciones del análisis" className="-mb-px flex gap-6 overflow-x-auto">
        {TABS.map(({ key, label }) => {
          const selected = active === key
          return (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => onChange(key)}
              className={`shrink-0 whitespace-nowrap border-b-2 px-1 pb-3 text-sm font-medium transition ${
                selected
                  ? 'border-brand-magenta text-brand-magenta'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
