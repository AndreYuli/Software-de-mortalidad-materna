import { useState } from 'react'

export type ActiveView = 'analisis' | 'mortalidad' | 'morbilidad'

export function useActiveView(initialView: ActiveView = 'analisis') {
  const [activeView, setActiveView] = useState<ActiveView>(initialView)

  return { activeView, setActiveView }
}
