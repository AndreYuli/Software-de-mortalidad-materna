import { describe, expect, it } from 'vitest'
import { calculateChartHeight } from './causasChartLabels'
import { CHART_HEIGHT_FIXED, calculateGroupedChartHeight, chartHeightClass } from './chartHeight'

describe('chartHeightClass', () => {
  it('devuelve el mínimo (320 px) para alturas pequeñas', () => {
    expect(chartHeightClass(0)).toBe('h-80')
    expect(chartHeightClass(320)).toBe('h-80')
  })

  it('sube al siguiente paso cuando la altura lo supera', () => {
    expect(chartHeightClass(321)).toBe('h-[360px]')
    expect(chartHeightClass(400)).toBe('h-[400px]')
    expect(chartHeightClass(401)).toBe('h-[440px]')
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

describe('calculateGroupedChartHeight', () => {
  const labels = ['Urbana', 'Rural']

  it('con una sola serie añade solo el espacio de título y leyenda', () => {
    expect(calculateGroupedChartHeight(labels, 1)).toBe(calculateChartHeight(labels) + 60)
  })

  it('añade espacio por cada serie adicional y por cada categoría', () => {
    // 2 categorías × (3 − 1) series extra × 20 px + 60 px de título y leyenda
    expect(calculateGroupedChartHeight(labels, 3)).toBe(calculateChartHeight(labels) + 2 * 2 * 20 + 60)
  })

  it('crece con el número de series', () => {
    expect(calculateGroupedChartHeight(labels, 8)).toBeGreaterThan(calculateGroupedChartHeight(labels, 3))
  })

  it('con cero series no resta altura', () => {
    expect(calculateGroupedChartHeight(labels, 0)).toBe(calculateChartHeight(labels) + 60)
  })
})
