import { describe, expect, it } from 'vitest'
import { calcularIndicadores, formatoNumero } from './indicadoresMaternos'

describe('calcularIndicadores', () => {
  it('sin ambos eventos no hay relación ni índice', () => {
    expect(calcularIndicadores({ ambosEventos: false, totalMortalidad: 60, totalMorbilidad: 3000 })).toEqual({
      relacionMmeMm: null,
      indiceMortalidad: null,
    })
  })

  it('calcula la relación MME/MM y el índice de mortalidad', () => {
    const { relacionMmeMm, indiceMortalidad } = calcularIndicadores({
      ambosEventos: true,
      totalMortalidad: 60,
      totalMorbilidad: 3000,
    })
    expect(relacionMmeMm).toBe(50)
    expect(indiceMortalidad).toBeCloseTo(1.96, 2)
  })

  it('sin muertes la relación no existe y el índice es 0', () => {
    expect(calcularIndicadores({ ambosEventos: true, totalMortalidad: 0, totalMorbilidad: 100 })).toEqual({
      relacionMmeMm: null,
      indiceMortalidad: 0,
    })
  })

  it('sin ningún caso no hay ni relación ni índice', () => {
    expect(calcularIndicadores({ ambosEventos: true, totalMortalidad: 0, totalMorbilidad: 0 })).toEqual({
      relacionMmeMm: null,
      indiceMortalidad: null,
    })
  })
})

describe('formatoNumero', () => {
  it('usa el punto de miles del es-CO', () => {
    expect(formatoNumero(20100)).toBe('20.100')
    expect(formatoNumero(3000)).toBe('3.000')
    expect(formatoNumero(1234567)).toBe('1.234.567')
  })

  it('usa la coma decimal y los decimales pedidos', () => {
    expect(formatoNumero(50.31, 1)).toBe('50,3')
    expect(formatoNumero(50, 1)).toBe('50,0')
  })
})
