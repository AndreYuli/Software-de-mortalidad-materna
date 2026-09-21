import { describe, it, expect } from 'vitest'
import { Chart as ChartJS } from 'chart.js'
import {
  CHART_FONT_FAMILY,
  CHART_COLORS,
  echartsBaseTextStyle,
  BRAND_COLOR,
  CATEGORICAL_PALETTE,
  BAR_STYLE_HORIZONTAL,
  BAR_STYLE_VERTICAL,
} from './chartTheme'

describe('chartTheme', () => {
  it('expone la fuente y los colores base compartidos', () => {
    expect(CHART_FONT_FAMILY).toBe('Plus Jakarta Sans, sans-serif')
    expect(CHART_COLORS.mortalidad).toBe('#c0392b')
    expect(CHART_COLORS.morbilidad).toBe('#2ca02c')
  })

  it('registra los defaults globales de Chart.js al importarse', () => {
    expect(ChartJS.defaults.font.family).toBe(CHART_FONT_FAMILY)
  })

  it('arma el textStyle base para ECharts', () => {
    expect(echartsBaseTextStyle()).toEqual({
      fontFamily: CHART_FONT_FAMILY,
      color: '#1a202c',
    })
  })

  it('expone el color de marca, la paleta categórica y los estilos de barra delgada', () => {
    expect(BRAND_COLOR).toBe('#89005e')
    expect(CATEGORICAL_PALETTE).toHaveLength(8)
    expect(new Set(CATEGORICAL_PALETTE).size).toBe(8)
    expect(BAR_STYLE_HORIZONTAL).toMatchObject({ borderWidth: 0, maxBarThickness: 16, barPercentage: 0.6 })
    expect(BAR_STYLE_VERTICAL).toMatchObject({ borderWidth: 0, maxBarThickness: 40 })
  })
})
