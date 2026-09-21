import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useDashboardCharts } from './useDashboardCharts'
import type { AnalisisCompleto } from '../../types'
import { CHART_COLORS } from '../../constants/chartTheme'

function fixtureConSociodemo(zonaLabels: string[], zonaValores: number[]): AnalisisCompleto {
  return {
    distribucion_sociodemografica: {
      zona_residencia: { labels: zonaLabels, valores: zonaValores, total: zonaValores.reduce((a, b) => a + b, 0) },
    },
  } as unknown as AnalisisCompleto
}

describe('useDashboardCharts — sociodemografica por evento', () => {
  it('no mezcla los datos de mortalidad y morbilidad para la misma variable', () => {
    const mortalidadData = fixtureConSociodemo(['Urbana', 'Rural'], [80, 20])
    const morbilidadData = fixtureConSociodemo(['Urbana', 'Rural'], [10, 90])

    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData, morbilidadData, filterYear: '' }),
    )

    expect(result.current.sociodemograficaMortalidad.zona_residencia.valores).toEqual([80, 20])
    expect(result.current.sociodemograficaMorbilidad.zona_residencia.valores).toEqual([10, 90])
  })

  it('devuelve un objeto vacío para el evento sin datos', () => {
    const mortalidadData = fixtureConSociodemo(['Urbana', 'Rural'], [80, 20])

    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData, morbilidadData: null, filterYear: '' }),
    )

    expect(result.current.sociodemograficaMortalidad.zona_residencia.valores).toEqual([80, 20])
    expect(result.current.sociodemograficaMorbilidad).toEqual({})
  })
})

function fixtureConCausas(causas: [string, number][], totalRegistros: number): AnalisisCompleto {
  return {
    total_registros: totalRegistros,
    causas_cie10: {
      top_causas: causas.map(([codigo, casos]) => ({ codigo, casos })),
      total_causas_unicas: causas.length,
    },
  } as unknown as AnalisisCompleto
}

describe('useDashboardCharts — causas principales', () => {
  it('ordena las causas de mayor a menor (la barra mayor queda arriba)', () => {
    const mortalidadData = fixtureConCausas(
      [
        ['O85', 5],
        ['O14.1', 30],
        ['O15.0', 12],
      ],
      50,
    )
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData, morbilidadData: null, filterYear: '' }),
    )
    expect(result.current.topCausasMortalidad.values).toEqual([30, 12, 5])
  })

  it('usa el color de cada evento y expone el total de registros', () => {
    const mortalidadData = fixtureConCausas([['O14.1', 30]], 60)
    const morbilidadData = fixtureConCausas([['O14.1', 900]], 3000)
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData, morbilidadData, filterYear: '' }),
    )
    expect(result.current.topCausasMortalidad.colors).toEqual([CHART_COLORS.mortalidad])
    expect(result.current.topCausasMorbilidad.colors).toEqual([CHART_COLORS.morbilidad])
    expect(result.current.topCausasMortalidad.total).toBe(60)
    expect(result.current.topCausasMorbilidad.total).toBe(3000)
  })

  it('sin datos devuelve listas vacías y total 0', () => {
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData: null, morbilidadData: null, filterYear: '' }),
    )
    expect(result.current.topCausasMortalidad).toEqual({ labels: [], values: [], colors: [], total: 0 })
  })
})
