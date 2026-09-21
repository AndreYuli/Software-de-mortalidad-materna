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
    <div role="tablist" aria-label="Secciones del análisis" className="flex gap-6 overflow-x-auto border-b border-slate-200">
      {TABS.map(({ key, label }) => {
        const selected = active === key
        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(key)}
            className={`-mb-px shrink-0 whitespace-nowrap border-b-2 px-1 pb-3 text-sm font-medium transition ${
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
  )
}
