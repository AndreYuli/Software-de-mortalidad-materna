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
    <div className="dashboard-subtabs">
      {SUBTAB_ORDER.map((key) => (
        <button
          key={key}
          type="button"
          className={`subtab-button ${active === key ? 'active' : ''}`}
          onClick={() => onChange(key)}
        >
          {SUBTAB_LABELS[key]}
        </button>
      ))}
    </div>
  )
}
