import { useState } from 'react'

export function useDashboardFilters() {
  const [filterYear, setFilterYear] = useState('')
  const [filterMonth, setFilterMonth] = useState('')
  const [filterWeek, setFilterWeek] = useState('')
  const [filterDay, setFilterDay] = useState('')
  const [filterEventos, setFilterEventos] = useState<string[]>(['549', '550'])
  const [availableYears, setAvailableYears] = useState<number[]>([])

  return {
    filterYear,
    setFilterYear,
    filterMonth,
    setFilterMonth,
    filterWeek,
    setFilterWeek,
    filterDay,
    setFilterDay,
    filterEventos,
    setFilterEventos,
    availableYears,
    setAvailableYears,
  }
}
