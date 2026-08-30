import { useCallback, useState } from 'react'

export type MainTab = 'generalidades' | 'morbilidad' | 'mortalidad'
export type SubTab = 'sociodemografico' | 'clinico'

export function useDashboardTabs(initialTab: MainTab = 'generalidades') {
  const [activeTab, setActiveTabState] = useState<MainTab>(initialTab)
  const [activeSubTab, setActiveSubTab] = useState<SubTab>('clinico')

  const setActiveTab = useCallback((tab: MainTab) => {
    setActiveTabState(tab)
    setActiveSubTab('clinico')
  }, [])

  return { activeTab, setActiveTab, activeSubTab, setActiveSubTab }
}
