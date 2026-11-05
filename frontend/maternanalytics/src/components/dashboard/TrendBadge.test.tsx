import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendBadge } from './TrendBadge'

// Eventos adversos (mortalidad/morbilidad): bajar es favorable, subir es desfavorable.
describe('TrendBadge', () => {
  it('sin comparación muestra "Histórico"', () => {
    render(<TrendBadge compare={null} />)
    expect(screen.getByText('Histórico')).toBeInTheDocument()
  })

  it('con base previa 0 y casos actuales muestra "Sin base previa"', () => {
    render(<TrendBadge compare={{ cur: 4, prev: 0 }} />)
    expect(screen.getByText('Sin base previa')).toBeInTheDocument()
  })

  it('con base previa 0 y sin casos muestra "Estable"', () => {
    render(<TrendBadge compare={{ cur: 0, prev: 0 }} />)
    expect(screen.getByText('Estable')).toBeInTheDocument()
  })

  it('una subida es desfavorable (ámbar) y muestra el porcentaje con los conteos', () => {
    render(<TrendBadge compare={{ cur: 15, prev: 10 }} periodo="mes" />)
    const badge = screen.getByText('+50% vs mes anterior (15 vs 10)')
    expect(badge).toHaveClass('text-amber-800')
    expect(badge).not.toHaveClass('text-red-700')
  })

  it('una bajada es favorable (azul), no roja, y muestra los conteos', () => {
    render(<TrendBadge compare={{ cur: 8, prev: 10 }} periodo="año" />)
    const badge = screen.getByText('-20% vs año anterior (8 vs 10)')
    expect(badge).toHaveClass('text-sky-700')
    expect(badge).not.toHaveClass('text-red-700')
  })

  it('la bajada avisa que puede haber casos sin notificar (tooltip)', () => {
    render(<TrendBadge compare={{ cur: 8, prev: 10 }} periodo="año" />)
    expect(screen.getByText(/-20%/)).toHaveAttribute('title', expect.stringContaining('sin notificar'))
  })

  it('sin indicar el periodo compara con "periodo anterior"', () => {
    render(<TrendBadge compare={{ cur: 15, prev: 10 }} />)
    expect(screen.getByText('+50% vs periodo anterior (15 vs 10)')).toBeInTheDocument()
  })

  it('sin variación (cur = prev) es neutral y no usa color de alerta', () => {
    render(<TrendBadge compare={{ cur: 5, prev: 5 }} periodo="mes" />)
    const badge = screen.getByText('0% vs mes anterior (5 vs 5)')
    expect(badge).toHaveClass('text-slate-600')
  })

  it('con base previa menor a 5 no calcula porcentaje: muestra solo los conteos', () => {
    render(<TrendBadge compare={{ cur: 2, prev: 1 }} periodo="año" />)
    expect(screen.getByText('2 vs 1 casos (año anterior)')).toBeInTheDocument()
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
  })

  it('con base previa exactamente 5 ya calcula el porcentaje', () => {
    render(<TrendBadge compare={{ cur: 10, prev: 5 }} periodo="mes" />)
    expect(screen.getByText('+100% vs mes anterior (10 vs 5)')).toBeInTheDocument()
  })

  it('en la vista anual con menos de 12 meses indica los meses comparados', () => {
    render(<TrendBadge compare={{ cur: 12, prev: 10, meses: 3 }} periodo="año" />)
    expect(screen.getByText('+20% vs año anterior (ene–mar) (12 vs 10)')).toBeInTheDocument()
  })
})
