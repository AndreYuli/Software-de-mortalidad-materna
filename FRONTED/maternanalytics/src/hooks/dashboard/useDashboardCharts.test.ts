import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useDashboardCharts } from './useDashboardCharts'
import type { AnalisisCompleto } from '../../types'

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
