import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DistribucionEdadGestacional } from './DistribucionEdadGestacional'

const sampleData = { labels: ['<28 semanas', '28-36 semanas', '37-41 semanas', '≥42 semanas'], valores: [1, 2, 2, 1], total: 6 }

describe('DistribucionEdadGestacional', () => {
  it('renderiza el titulo con el nombre del evento cuando hay datos', () => {
    render(<DistribucionEdadGestacional data={sampleData} evento="Mortalidad" />)
    expect(screen.getByText('Distribución por Edad Gestacional (Mortalidad)')).toBeInTheDocument()
  })

  it('muestra un mensaje de datos insuficientes cuando no hay datos', () => {
    render(<DistribucionEdadGestacional data={null} evento="Morbilidad" />)
    expect(screen.getByText('No hay datos suficientes de edad gestacional para generar esta gráfica.')).toBeInTheDocument()
  })
})
