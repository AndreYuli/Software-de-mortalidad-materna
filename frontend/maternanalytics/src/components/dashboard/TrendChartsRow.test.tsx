import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendChartsRow } from './TrendChartsRow'

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

  it('cada gráfica expone una descripción accesible con sus datos', () => {
    render(<TrendChartsRow {...sampleProps} />)
    expect(
      screen.getByRole('img', { name: 'Top 10 Causas de Mortalidad. Preeclampsia Severa: 5' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Top 10 Causas de Morbilidad. Eclampsia: 3' })).toBeInTheDocument()
  })

  it('muestra las causas asociadas de morbilidad cuando se reciben', () => {
    render(
      <TrendChartsRow
        {...sampleProps}
        topCausasAsociadasMorbilidad={{ labels: ['Hemorragia postparto'], values: [4], colors: ['#2ca02c'] }}
      />,
    )
    expect(
      screen.getByRole('img', { name: 'Top 10 Causas asociadas de Morbilidad. Hemorragia postparto: 4' }),
    ).toBeInTheDocument()
  })

  it('sin causas asociadas registradas muestra su estado vacío, y sin la prop no aparece', () => {
    const { unmount } = render(
      <TrendChartsRow {...sampleProps} topCausasAsociadasMorbilidad={{ labels: [], values: [], colors: [] }} />,
    )
    expect(screen.getByText('Sin causas asociadas registradas')).toBeInTheDocument()
    unmount()
    render(<TrendChartsRow {...sampleProps} topCausasAsociadasMorbilidad={null} />)
    expect(screen.queryByText('Top 10 Causas asociadas de Morbilidad')).not.toBeInTheDocument()
  })
})
