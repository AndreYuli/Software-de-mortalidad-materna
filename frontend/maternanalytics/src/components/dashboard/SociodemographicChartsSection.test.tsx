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

    const grid = container.querySelector('[data-testid="sociodemographic-grid"]')
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

  it('no rompe la vista si una variable tiene total positivo pero valores vacíos o inválidos', () => {
    const data = {
      zona_residencia: { labels: undefined as any, valores: undefined as any, total: 1 },
      poblacion_vulnerable: { labels: [], valores: [], total: 0 },
      etnia: { labels: [], valores: [], total: 0 },
      tipo_afiliacion: { labels: [], valores: [], total: 0 },
    }

    expect(() => render(<SociodemographicChartsSection data={data} evento="Mortalidad" />)).not.toThrow()
    expect(screen.getByText(/No hay datos sociodemográficos disponibles/)).toBeInTheDocument()
  })
})
