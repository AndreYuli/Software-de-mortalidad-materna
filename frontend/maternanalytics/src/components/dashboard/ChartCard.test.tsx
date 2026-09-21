import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartCard } from './ChartCard'

describe('ChartCard', () => {
  it('muestra el título como h3 y el contenido', () => {
    render(
      <ChartCard title="Etnia">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.getByRole('heading', { level: 3, name: 'Etnia' })).toBeInTheDocument()
    expect(screen.getByText('contenido')).toBeInTheDocument()
  })

  it('muestra la etiqueta y la descripción cuando se indican', () => {
    render(
      <ChartCard title="Top 10" eyebrow="Evento 550" description="Total: 4 casos">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.getByText('Evento 550')).toBeInTheDocument()
    expect(screen.getByText('Total: 4 casos')).toBeInTheDocument()
  })

  it('muestra la lectura automatizada solo si hay insight', () => {
    const { rerender } = render(
      <ChartCard title="Etnia" insight="Predomina el grupo A.">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.getByText('Lectura automatizada')).toBeInTheDocument()
    expect(screen.getByText('Predomina el grupo A.')).toBeInTheDocument()

    rerender(
      <ChartCard title="Etnia" insight={null}>
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.queryByText('Lectura automatizada')).not.toBeInTheDocument()
  })

  it('sin etiqueta ni descripción no renderiza nada extra', () => {
    const { container } = render(
      <ChartCard title="Etnia">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(container.querySelector('article > div > span')).toBeNull()
    expect(container.querySelector('article > div > p')).toBeNull()
  })
})
