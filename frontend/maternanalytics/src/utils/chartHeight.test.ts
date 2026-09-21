import { describe, expect, it } from 'vitest'
import { CHART_HEIGHT_FIXED, chartHeightClass } from './chartHeight'

describe('chartHeightClass', () => {
  it('devuelve el mínimo (320 px) para alturas pequeñas', () => {
    expect(chartHeightClass(0)).toBe('h-80')
    expect(chartHeightClass(320)).toBe('h-80')
  })

  it('sube al siguiente paso cuando la altura lo supera', () => {
    expect(chartHeightClass(321)).toBe('h-[400px]')
    expect(chartHeightClass(400)).toBe('h-[400px]')
  })

  it('elige el primer paso que cubre la altura pedida', () => {
    expect(chartHeightClass(940)).toBe('h-[960px]')
  })

  it('no pasa de la altura máxima (1280 px)', () => {
    expect(chartHeightClass(1281)).toBe('h-[1280px]')
    expect(chartHeightClass(5000)).toBe('h-[1280px]')
  })

  it('expone la altura fija de las gráficas de edad (280 px)', () => {
    expect(CHART_HEIGHT_FIXED).toBe('h-[280px]')
  })
})
