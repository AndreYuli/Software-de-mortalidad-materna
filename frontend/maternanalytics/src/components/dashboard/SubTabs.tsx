import type { SubTab } from '../../hooks/navigation/useDashboardTabs'

export interface SubTabsProps {
  active: SubTab
  onChange: (tab: SubTab) => void
}

const SUBTAB_LABELS: Record<SubTab, string> = {
  sociodemografico: 'Factores Sociodemográficos',
  clinico: 'Factores Clínicos',
}

const SUBTAB_ORDER: SubTab[] = ['sociodemografico', 'clinico']

export function SubTabs({ active, onChange }: SubTabsProps) {
  return (
    <div role="tablist" aria-label="Factores" className="flex flex-wrap gap-2">
      {SUBTAB_ORDER.map((key) => {
        const selected = active === key
        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(key)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              selected ? 'bg-brand-magenta text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {SUBTAB_LABELS[key]}
          </button>
        )
      })}
    </div>
  )
}
