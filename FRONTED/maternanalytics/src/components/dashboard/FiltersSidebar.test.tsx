import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FiltersSidebar } from './FiltersSidebar'

const baseProps = {
  filterYear: '',
  onYearChange: vi.fn(),
  availableYears: [2026, 2025],
  filterMonth: '',
  onMonthChange: vi.fn(),
  filterWeek: '',
  onWeekChange: vi.fn(),
  filterDay: '',
  onDayChange: vi.fn(),
  onExport: vi.fn(),
}

describe('FiltersSidebar', () => {
  it('deshabilita semana y día cuando no hay año/mes seleccionados', () => {
    render(<FiltersSidebar {...baseProps} />)
    expect(screen.getByLabelText('Semana de Reporte')).toBeDisabled()
    expect(screen.getByLabelText('Día de Reporte')).toBeDisabled()
  })

  it('habilita semana al seleccionar año, y día al seleccionar mes', () => {
    render(<FiltersSidebar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByLabelText('Semana de Reporte')).not.toBeDisabled()
    expect(screen.getByLabelText('Día de Reporte')).not.toBeDisabled()
  })

  it('renderiza las 53 semanas ISO y los 31 días', () => {
    render(<FiltersSidebar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByText('Semana 53')).toBeInTheDocument()
    expect(screen.getByLabelText('Día de Reporte').querySelectorAll('option')).toHaveLength(32) // 31 + "Todos los días"
  })

  it('el botón Limpiar resetea los 4 filtros', () => {
    const onYearChange = vi.fn()
    const onMonthChange = vi.fn()
    const onWeekChange = vi.fn()
    const onDayChange = vi.fn()
    render(
      <FiltersSidebar
        {...baseProps}
        filterYear="2026"
        onYearChange={onYearChange}
        filterMonth="3"
        onMonthChange={onMonthChange}
        filterWeek="11"
        onWeekChange={onWeekChange}
        filterDay="15"
        onDayChange={onDayChange}
      />,
    )
    fireEvent.click(screen.getByText('Limpiar'))
    expect(onYearChange).toHaveBeenCalledWith('')
    expect(onMonthChange).toHaveBeenCalledWith('')
    expect(onWeekChange).toHaveBeenCalledWith('')
    expect(onDayChange).toHaveBeenCalledWith('')
  })
})
