import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SankeyMortalidad } from './SankeyMortalidad'

const data = {
  nodos: ['[Parto] Vaginal', '[Parto] Cesárea', '[Nivel] Nivel 1', '[Muerte] Intraparto'],
  links: {
    source: [0, 1],
    target: [2, 2],
    value: [5, 3],
  },
}

describe('SankeyMortalidad', () => {
  it('renderiza el diagrama Sankey sin lanzar excepciones cuando hay datos', () => {
    render(<SankeyMortalidad data={data} />)
    expect(screen.getByText('Flujo de Atención: Tipo de Parto → Nivel de Atención → Momento de Muerte')).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay datos', () => {
    render(<SankeyMortalidad data={undefined} />)
    expect(screen.getByText('No hay datos suficientes para generar el diagrama Sankey.')).toBeInTheDocument()
  })
})
