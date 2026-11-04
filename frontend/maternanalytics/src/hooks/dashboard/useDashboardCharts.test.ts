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
    estadisticas_basicas: { total_casos: totalRegistros },
    causas_cie10: {
      top_causas: causas.map(([codigo, casos]) => ({ codigo, casos })),
      total_causas_unicas: causas.length,
    },
  } as unknown as AnalisisCompleto
}

describe('useDashboardCharts — causas asociadas de morbilidad', () => {
  const morbilidadData = {
    tipo: 'morbilidad',
    estadisticas_basicas: { total_casos: 40 },
    causas_asociadas: {
      top_causas: [
        { codigo: 'O15.0', casos: 2, porcentaje: 5 },
        { codigo: 'O72.1', casos: 10, porcentaje: 25 },
      ],
      total_causas_unicas: 2,
      casos_con_causa_asociada: 11,
    },
  } as unknown as AnalisisCompleto

  it('ordena las causas asociadas y usa el total de casos de morbilidad', () => {
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData: null, morbilidadData, filterYear: '' }),
    )
    const datos = result.current.topCausasAsociadasMorbilidad
    expect(datos?.codigos).toEqual(['O72.1', 'O15.0'])
    expect(datos?.values).toEqual([10, 2])
    expect(datos?.porcentajes).toEqual([25, 5])
    expect(datos?.total).toBe(40)
    expect(datos?.casosConCausaAsociada).toBe(11)
  })

  it('es null cuando el segmento es solo mortalidad', () => {
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'mortalidad', mortalidadData: null, morbilidadData, filterYear: '' }),
    )
    expect(result.current.topCausasAsociadasMorbilidad).toBeNull()
  })

  it('sin causas asociadas devuelve listas vacías', () => {
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'morbilidad', mortalidadData: null, morbilidadData: null, filterYear: '' }),
    )
    expect(result.current.topCausasAsociadasMorbilidad?.values).toEqual([])
  })
})

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
    expect(result.current.topCausasMortalidad).toEqual({
      labels: [],
      codigos: [],
      porcentajes: [],
      values: [],
      colors: [],
      total: 0,
    })
  })
})
