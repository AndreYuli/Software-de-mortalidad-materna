import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendBadge } from './TrendBadge'

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

  it('una subida se muestra en verde con signo y compara con el mes anterior', () => {
    render(<TrendBadge compare={{ cur: 15, prev: 10 }} periodo="mes" />)
    const badge = screen.getByText('+50% vs mes anterior')
    expect(badge).toHaveClass('text-green-700')
  })

  it('una bajada se muestra en rojo y compara con el año anterior', () => {
    render(<TrendBadge compare={{ cur: 8, prev: 10 }} periodo="año" />)
    const badge = screen.getByText('-20% vs año anterior')
    expect(badge).toHaveClass('text-red-700')
  })

  it('sin indicar el periodo compara con "periodo anterior"', () => {
    render(<TrendBadge compare={{ cur: 15, prev: 10 }} />)
    expect(screen.getByText('+50% vs periodo anterior')).toBeInTheDocument()
  })

  it('una variación exactamente 0 mantiene la regla actual (signo + y estilo de bajada)', () => {
    render(<TrendBadge compare={{ cur: 5, prev: 5 }} periodo="mes" />)
    const badge = screen.getByText('+0% vs mes anterior')
    expect(badge).toHaveClass('text-red-700')
  })
})
