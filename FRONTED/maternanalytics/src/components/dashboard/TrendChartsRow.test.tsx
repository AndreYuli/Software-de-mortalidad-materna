import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendChartsRow, wrapLabel } from './TrendChartsRow'

const sampleProps = {
  topCausasMortalidad: { labels: ['Preeclampsia Severa'], values: [5], colors: ['#c0392b'] },
  topCausasMorbilidad: { labels: ['Eclampsia'], values: [3], colors: ['#2ca02c'] },
}

const emptyProps = {
  topCausasMortalidad: { labels: [], values: [], colors: [] },
  topCausasMorbilidad: { labels: [], values: [], colors: [] },
}

describe('TrendChartsRow', () => {
  it('renderiza los gráficos sin lanzar excepciones cuando hay datos', () => {
    render(<TrendChartsRow {...sampleProps} />)
    expect(screen.getByText('Top 10 Causas de Mortalidad')).toBeInTheDocument()
    expect(screen.getByText('Top 10 Causas de Morbilidad')).toBeInTheDocument()
  })

  it('muestra los mensajes de estado vacío cuando no hay datos', () => {
    render(<TrendChartsRow {...emptyProps} />)
    expect(screen.getByText('Sin registros de causas de mortalidad')).toBeInTheDocument()
    expect(screen.getByText('Sin registros de causas de morbilidad')).toBeInTheDocument()
  })
})

describe('wrapLabel', () => {
  it('devuelve el texto tal cual si es corto', () => {
    expect(wrapLabel('Eclampsia')).toBe('Eclampsia')
  })

  it('envuelve texto largo en varias líneas sin truncar ni agregar "..."', () => {
    const texto =
      'O14.9 Preeclampsia no especificada con complicaciones hepáticas y renales graves durante el tercer trimestre'
    const resultado = wrapLabel(texto)
    expect(Array.isArray(resultado)).toBe(true)
    const lineas = resultado as string[]
    expect(lineas.length).toBeGreaterThan(2)
    expect(lineas.some((linea) => linea.includes('...'))).toBe(false)
    expect(lineas.join(' ')).toBe(texto)
  })
})
