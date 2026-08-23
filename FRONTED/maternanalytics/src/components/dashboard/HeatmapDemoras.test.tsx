import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HeatmapDemoras } from './HeatmapDemoras'

const data = {
  causas: ['O26.6', 'O99.3'],
  demoras: ['Demora 1', 'Demora 2'],
  valores: [
    [3, 1],
    [0, 2],
  ],
}

describe('HeatmapDemoras', () => {
  it('renderiza el mapa de calor sin lanzar excepciones cuando hay datos', () => {
    render(<HeatmapDemoras data={data} />)
    expect(screen.getByText('Causas CIE-10 Asociadas a Demoras Obstétricas')).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay datos', () => {
    render(<HeatmapDemoras data={undefined} />)
    expect(screen.getByText('No hay datos suficientes para generar el mapa de calor.')).toBeInTheDocument()
  })
})
