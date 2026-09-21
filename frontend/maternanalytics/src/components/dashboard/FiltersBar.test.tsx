import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FiltersBar } from './FiltersBar'

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

describe('FiltersBar', () => {
  it('deshabilita semana y día cuando no hay año/mes seleccionados', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.getByLabelText('Semana de Reporte')).toBeDisabled()
    expect(screen.getByLabelText('Día de Reporte')).toBeDisabled()
  })

  it('habilita semana al seleccionar año, y día al seleccionar mes', () => {
    render(<FiltersBar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByLabelText('Semana de Reporte')).not.toBeDisabled()
    expect(screen.getByLabelText('Día de Reporte')).not.toBeDisabled()
  })

  it('renderiza las 53 semanas ISO y los 31 días', () => {
    render(<FiltersBar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByText('Semana 53')).toBeInTheDocument()
    expect(screen.getByLabelText('Día de Reporte').querySelectorAll('option')).toHaveLength(32) // 31 + "Todos los días"
  })

  it('el botón Limpiar resetea los 4 filtros', () => {
    const onYearChange = vi.fn()
    const onMonthChange = vi.fn()
    const onWeekChange = vi.fn()
    const onDayChange = vi.fn()
    render(
      <FiltersBar
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

  it('no muestra Limpiar cuando no hay ningún filtro activo', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.queryByText('Limpiar')).not.toBeInTheDocument()
  })

  it('el botón Filtros despliega y pliega el panel (aria-expanded)', () => {
    render(<FiltersBar {...baseProps} />)
    const toggle = screen.getByRole('button', { name: /^Filtros/ })
    const panel = document.getElementById(toggle.getAttribute('aria-controls') as string) as HTMLElement
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(panel).toHaveClass('hidden')

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(panel).not.toHaveClass('hidden')

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(panel).toHaveClass('hidden')
  })

  it('avisa de que hay filtros activos solo cuando alguno lo está', () => {
    const { rerender } = render(<FiltersBar {...baseProps} />)
    expect(screen.queryByText('(hay filtros activos)')).not.toBeInTheDocument()

    rerender(<FiltersBar {...baseProps} filterYear="2026" />)
    expect(screen.getByText('(hay filtros activos)')).toBeInTheDocument()
  })

  it('el botón Exportar Reporte llama a onExport', () => {
    const onExport = vi.fn()
    render(<FiltersBar {...baseProps} onExport={onExport} />)
    fireEvent.click(screen.getByRole('button', { name: 'Exportar Reporte' }))
    expect(onExport).toHaveBeenCalledTimes(1)
  })

  it('el selector de Evento es el primer combobox y cambia el segmento', () => {
    const onSegmentoChange = vi.fn()
    render(
      <FiltersBar
        {...baseProps}
        segmento="ambos"
        onSegmentoChange={onSegmentoChange}
        latestMortalidad={{ id: 1 }}
        latestMorbilidad={{ id: 2 }}
      />,
    )
    expect(screen.getAllByRole('combobox')[0]).toHaveAttribute('id', 'filter-segmento')
    fireEvent.change(screen.getByLabelText('Evento'), { target: { value: 'mortalidad' } })
    expect(onSegmentoChange).toHaveBeenCalledWith('mortalidad')
  })

  it('sin segmento no muestra el selector de Evento', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.queryByLabelText('Evento')).not.toBeInTheDocument()
  })
})
