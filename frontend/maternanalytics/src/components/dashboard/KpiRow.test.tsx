import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KpiRow, type KpiRowProps } from './KpiRow'

const base: KpiRowProps = {
  totalCasos: 120,
  totalMortalidad: 15,
  totalMorbilidad: 105,
  tasaLetalidad: '12.5',
  curTot: 120,
  prevTot: 100,
  yearCompareMort: { cur: 15, prev: 10 },
  yearCompareMorb: { cur: 105, prev: 117 },
}

describe('KpiRow', () => {
  it('muestra la región, las cuatro etiquetas y las cuatro cifras', () => {
    render(<KpiRow {...base} />)
    expect(screen.getByRole('region', { name: 'Resumen epidemiológico' })).toBeInTheDocument()
    expect(screen.getByText('Casos analizados')).toBeInTheDocument()
    expect(screen.getByText('Mortalidad materna 550')).toBeInTheDocument()
    expect(screen.getByText('Morbilidad materna extrema 549')).toBeInTheDocument()
    expect(screen.getByText('Tasa de letalidad')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('105')).toBeInTheDocument()
    expect(screen.getByText('12.5%')).toBeInTheDocument()
  })

  it('muestra las tendencias con la base de comparación indicada', () => {
    render(<KpiRow {...base} periodo="mes" />)
    expect(screen.getByText('+20% vs mes anterior')).toBeInTheDocument()
    expect(screen.getByText('+50% vs mes anterior')).toBeInTheDocument()
    expect(screen.getByText('-10% vs mes anterior')).toBeInTheDocument()
  })

  it('usa "año anterior" cuando el periodo es el año', () => {
    render(<KpiRow {...base} periodo="año" />)
    expect(screen.getAllByText(/vs año anterior/)).toHaveLength(3)
  })

  it('sin comparación (sin año elegido) muestra "Histórico" en las tres tendencias', () => {
    // Sin año, curTot y prevTot valen 0 y darían un falso "Estable": debe decir "Histórico" como las otras.
    render(<KpiRow {...base} curTot={0} prevTot={0} yearCompareMort={null} yearCompareMorb={null} />)
    expect(screen.getAllByText('Histórico')).toHaveLength(3)
    expect(screen.queryByText('Estable')).not.toBeInTheDocument()
  })

  it('si solo un evento tiene comparación, la de casos sigue mostrando la variación', () => {
    render(<KpiRow {...base} yearCompareMort={null} periodo="mes" />)
    expect(screen.getByText('+20% vs mes anterior')).toBeInTheDocument()
    expect(screen.getAllByText('Histórico')).toHaveLength(1)
  })

  it('con letalidad menor de 50 no muestra la alerta', () => {
    render(<KpiRow {...base} tasaLetalidad="49.9" />)
    expect(screen.queryByText('Valor atípicamente alto')).not.toBeInTheDocument()
  })

  it('con letalidad de 50 o más muestra la alerta accesible', () => {
    render(<KpiRow {...base} tasaLetalidad="62.5" />)
    expect(screen.getByText('Valor atípicamente alto')).toBeInTheDocument()
    expect(screen.getByTitle('Valor atípicamente alto')).toBeInTheDocument()
  })

  it('con una tasa no numérica no muestra la alerta', () => {
    render(<KpiRow {...base} tasaLetalidad="N/A" />)
    expect(screen.queryByText('Valor atípicamente alto')).not.toBeInTheDocument()
  })
})
