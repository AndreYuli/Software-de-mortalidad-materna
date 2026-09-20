import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SociodemographicChartsSection } from './SociodemographicChartsSection'

const variable = { labels: ['A', 'B'], valores: [3, 1], total: 4 }

describe('SociodemographicChartsSection', () => {
  it('agrupa las gráficas con datos en la rejilla que las pone lado a lado', () => {
    const data = {
      zona_residencia: variable,
      poblacion_vulnerable: variable,
      etnia: variable,
      tipo_afiliacion: { labels: [], valores: [], total: 0 },
    }
    const { container } = render(<SociodemographicChartsSection data={data} evento="Morbilidad" />)

    const grid = container.querySelector('.sociodemographic-grid')
    expect(grid).not.toBeNull()
    // La variable sin datos no ocupa un hueco en la rejilla
    expect(grid!.children).toHaveLength(3)
    expect(screen.getByText('Zona de Residencia')).toBeInTheDocument()
    expect(screen.getByText('Etnia')).toBeInTheDocument()
    expect(screen.queryByText('Tipo de Afiliación')).toBeNull()
  })

  it('muestra un mensaje cuando no hay ningún dato sociodemográfico', () => {
    render(<SociodemographicChartsSection data={{}} evento="Mortalidad" />)
    expect(screen.getByText(/No hay datos sociodemográficos disponibles/)).toBeInTheDocument()
  })
})
