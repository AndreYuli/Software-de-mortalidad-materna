import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartAiInsight } from './ChartAiInsight'

describe('ChartAiInsight', () => {
  it('no renderiza nada sin lectura', () => {
    const { container } = render(<ChartAiInsight insight={null} />)
    expect(container.innerHTML).toBe('')
  })

  it('no renderiza nada con una lectura vacía', () => {
    const { container } = render(<ChartAiInsight insight="" />)
    expect(container.innerHTML).toBe('')
  })

  it('muestra la etiqueta y el texto de la lectura', () => {
    render(<ChartAiInsight insight="La tendencia sube en el segundo trimestre." />)
    expect(screen.getByText('Lectura automatizada')).toBeInTheDocument()
    expect(screen.getByText('La tendencia sube en el segundo trimestre.')).toBeInTheDocument()
  })
})
