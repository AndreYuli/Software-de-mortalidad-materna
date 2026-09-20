import { useCallback, useState } from 'react'

export function useDashboardFilters() {
  const [filterYear, setFilterYearState] = useState('')
  const [filterMonth, setFilterMonthState] = useState('')
  const [filterWeek, setFilterWeek] = useState('')
  const [filterDay, setFilterDay] = useState('')

  // Los selects de mes/semana dependen del año y el de día del mes: al vaciar el padre se
  // limpian los dependientes. Si no, el filtro seguía aplicándose (el backend filtra por mes
  // sin año) mientras el select aparecía deshabilitado, sin forma de verlo ni quitarlo.
  const setFilterYear = useCallback((year: string) => {
    setFilterYearState(year)
    if (!year) {
      setFilterMonthState('')
      setFilterWeek('')
      setFilterDay('')
    }
  }, [])

  const setFilterMonth = useCallback((month: string) => {
    setFilterMonthState(month)
    if (!month) setFilterDay('')
  }, [])
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
