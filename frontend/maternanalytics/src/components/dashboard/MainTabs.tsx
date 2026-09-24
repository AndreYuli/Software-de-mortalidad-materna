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
    // La pestaña activa baja 1 px y tapa el borde superior del panel de filtros, que va justo debajo:
    // así queda fusionada con el panel. En pantallas anchas el contenedor no recorta (overflow visible);
    // en móvil hace scroll horizontal y ese solape de 1 px se recorta.
    <div>
      <div role="tablist" aria-label="Secciones del análisis" className="-mb-px flex items-end gap-1.5 overflow-x-auto px-1 pt-1 sm:overflow-visible">
        {TABS.map(({ key, label }) => {
          const selected = active === key
          return (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => onChange(key)}
              className={`shrink-0 whitespace-nowrap rounded-b-none rounded-t-lg px-4 text-sm font-medium transition ${
                selected
                  ? 'tab-raised-active pb-3 pt-2.5 font-semibold text-brand-magenta'
                  : 'tab-raised-inactive mt-1 pb-2 pt-1.5 text-slate-500 hover:text-slate-800'
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
