import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DistribucionEdadRiesgo } from './DistribucionEdadRiesgo'

const sampleData = { labels: ['<19 años', '19-34 años', '≥35 años'], valores: [1, 3, 2], total: 6 }

describe('DistribucionEdadRiesgo', () => {
  it('renderiza el titulo con el nombre del evento cuando hay datos', () => {
    render(<DistribucionEdadRiesgo data={sampleData} evento="Mortalidad" />)
    expect(screen.getByText('Distribución por Edad y Riesgo Obstétrico (Mortalidad)')).toBeInTheDocument()
  })

  it('muestra un mensaje de datos insuficientes cuando no hay datos', () => {
    render(<DistribucionEdadRiesgo data={null} evento="Morbilidad" />)
    expect(screen.getByText('No hay datos suficientes de edad para generar esta gráfica.')).toBeInTheDocument()
  })
})
