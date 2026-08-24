import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendChartsRow } from './TrendChartsRow'

const sampleProps = {
  lineChartData: {
    labels: ['Ene', 'Feb', 'Mar'],
    series: [{ name: 'Mortalidad', color: '#c0392b', data: [1, 2, 3] }],
  },
  barChartData: { labels: ['Trastornos del hígado en embarazo'], values: [5], colors: ['#c0392b'] },
  demorasChartData: { labels: ['Demora 1'], values: [3] },
  edadChartData: { labels: ['20-29'], mortalidadValues: [2], morbilidadValues: [4] },
  momentoChartData: { labels: ['Parto'], mortalidadValues: [1], morbilidadValues: [2] },
}

const emptyProps = {
  lineChartData: { labels: [], series: [] },
  barChartData: { labels: [], values: [], colors: [] },
  demorasChartData: { labels: [], values: [] },
  edadChartData: { labels: [], mortalidadValues: [], morbilidadValues: [] },
  momentoChartData: { labels: [], mortalidadValues: [], morbilidadValues: [] },
}

describe('TrendChartsRow', () => {
  it('renderiza los 4 gráficos sin lanzar excepciones cuando hay datos', () => {
    render(<TrendChartsRow {...sampleProps} />)
    expect(screen.getByText('Evolución Temporal de Casos')).toBeInTheDocument()
    expect(screen.getByText('Top 5 Causas Principales')).toBeInTheDocument()
    expect(screen.getByText('Demoras Críticas en la Atención')).toBeInTheDocument()
    expect(screen.getByText('Distribución por Edad Materna')).toBeInTheDocument()
    expect(screen.getByText('Momento de Ocurrencia / Muerte')).toBeInTheDocument()
  })

  it('muestra los mensajes de estado vacío cuando no hay datos', () => {
    render(<TrendChartsRow {...emptyProps} />)
    expect(screen.getByText('Sin datos de evolución temporal')).toBeInTheDocument()
    expect(screen.getByText('Sin registros de causas')).toBeInTheDocument()
    expect(screen.getByText('Sin datos de demoras (Aplica principalmente a Mortalidad)')).toBeInTheDocument()
    expect(screen.getByText('Sin datos de distribución por edad')).toBeInTheDocument()
    expect(screen.getByText('Sin datos del momento del evento')).toBeInTheDocument()
  })
})
