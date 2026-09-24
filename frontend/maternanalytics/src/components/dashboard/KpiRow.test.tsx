import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KpiRow, type KpiRowProps } from './KpiRow'

const base: KpiRowProps = {
  totalMortalidad: 60,
  totalMorbilidad: 3000,
  relacionMmeMm: 50,
  indiceMortalidad: 1.96,
  yearCompareMort: { cur: 15, prev: 10 },
  yearCompareMorb: { cur: 105, prev: 117 },
}

describe('KpiRow', () => {
  it('muestra la región y las cuatro etiquetas nuevas', () => {
    render(<KpiRow {...base} />)
    expect(screen.getByRole('region', { name: 'Resumen epidemiológico' })).toBeInTheDocument()
    expect(screen.getByText('Mortalidad materna 550')).toBeInTheDocument()
    expect(screen.getByText('Morbilidad materna extrema 549')).toBeInTheDocument()
    expect(screen.getByText('Relación MME/MM')).toBeInTheDocument()
    expect(screen.getByText('Índice de mortalidad')).toBeInTheDocument()
  })

  it('ya no muestra "Casos analizados" ni "Tasa de letalidad"', () => {
    render(<KpiRow {...base} />)
    expect(screen.queryByText('Casos analizados')).not.toBeInTheDocument()
    expect(screen.queryByText('Tasa de letalidad')).not.toBeInTheDocument()
  })

  it('muestra las cifras con formato es-CO', () => {
    render(<KpiRow {...base} />)
    expect(screen.getByText('60')).toBeInTheDocument()
    expect(screen.getByText('3.000')).toBeInTheDocument()
    expect(screen.getByText('50,0:1')).toBeInTheDocument()
    expect(screen.getByText('2,0%')).toBeInTheDocument()
  })

  it('muestra "—" cuando la relación o el índice no se pueden calcular', () => {
    render(<KpiRow {...base} relacionMmeMm={null} indiceMortalidad={null} />)
    expect(screen.getAllByText('—')).toHaveLength(2)
  })

  it('muestra las tendencias de mortalidad y morbilidad con la base de comparación', () => {
    render(<KpiRow {...base} periodo="mes" />)
    expect(screen.getByText('+50% vs mes anterior')).toBeInTheDocument()
    expect(screen.getByText('-10% vs mes anterior')).toBeInTheDocument()
  })

  it('usa "año anterior" cuando el periodo es el año', () => {
    render(<KpiRow {...base} periodo="año" />)
    expect(screen.getAllByText(/vs año anterior/)).toHaveLength(2)
  })

  it('sin comparación muestra "Histórico" en las dos tendencias', () => {
    render(<KpiRow {...base} yearCompareMort={null} yearCompareMorb={null} />)
    expect(screen.getAllByText('Histórico')).toHaveLength(2)
  })

  it('explica cómo se calcula cada indicador en un tooltip accesible', () => {
    render(<KpiRow {...base} />)
    const botones = screen.getAllByRole('button', { name: 'Cómo se calcula' })
    expect(botones).toHaveLength(2)
    expect(botones[1]).toHaveAccessibleDescription(/MM \/ \(MME \+ MM\) × 100/)
    expect(screen.getAllByRole('tooltip', { hidden: true })).toHaveLength(2)
  })

  it('no muestra una alerta de umbral aunque el índice sea alto', () => {
    render(<KpiRow {...base} indiceMortalidad={62.5} />)
    expect(screen.queryByText('Valor atípicamente alto')).not.toBeInTheDocument()
  })
})
