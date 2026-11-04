import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useDashboardMetrics } from './useDashboardMetrics'
import type { AnalisisCompleto } from '../../types'

function fixture(totalCasos: number): AnalisisCompleto {
  return { estadisticas_basicas: { total_casos: totalCasos } } as unknown as AnalisisCompleto
}

describe('useDashboardMetrics', () => {
  it('calcula la tasa de letalidad como muertes sobre el total de casos', () => {
    const { result } = renderHook(() =>
      useDashboardMetrics({
        segmento: 'ambos',
        mortalidadData: fixture(30),
        morbilidadData: fixture(10),
        filterYear: '',
        filterMonth: '',
      }),
    )
    expect(result.current.tasaLetalidad).toBe('75.0')
  })

  it('retorna "0" cuando no hay casos totales, para evitar division por cero', () => {
    const { result } = renderHook(() =>
      useDashboardMetrics({
        segmento: 'ambos',
        mortalidadData: null,
        morbilidadData: null,
        filterYear: '',
        filterMonth: '',
      }),
    )
    expect(result.current.tasaLetalidad).toBe('0')
  })

  it('con morbilidad en 0 y solo muertes, la letalidad es 100 (sin division por cero)', () => {
    const { result } = renderHook(() =>
      useDashboardMetrics({
        segmento: 'ambos',
        mortalidadData: fixture(30),
        morbilidadData: fixture(0),
        filterYear: '',
        filterMonth: '',
      }),
    )
    expect(result.current.tasaLetalidad).toBe('100.0')
  })

  it('retorna "0" en una cohorte única (el denominador sería el propio numerador)', () => {
    const { result } = renderHook(() =>
      useDashboardMetrics({
        segmento: 'mortalidad',
        mortalidadData: fixture(30),
        morbilidadData: fixture(10),
        filterYear: '',
        filterMonth: '',
      }),
    )
    expect(result.current.tasaLetalidad).toBe('0')
  })

  describe('comparativo de tendencia (meses alineados)', () => {
    const conDist = (d: Record<string, Record<string, number>>) =>
      ({ estadisticas_basicas: { total_casos: 0 }, distribucion_mensual: d }) as unknown as AnalisisCompleto
    const run = (d: Record<string, Record<string, number>>, y: string, m = '') =>
      renderHook(() =>
        useDashboardMetrics({
          segmento: 'mortalidad',
          mortalidadData: conDist(d),
          morbilidadData: null,
          filterYear: y,
          filterMonth: m,
        }),
      ).result.current.yearCompareMort

    it('año incompleto: compara solo los mismos meses del año anterior', () => {
      // 2026 llega hasta marzo; 2025 está completo. No debe compararse 3 meses contra 12.
      const d = {
        '2026': { '1': 2, '2': 3, '3': 1 },
        '2025': { '1': 2, '2': 2, '3': 2, '4': 5, '5': 5, '6': 5, '12': 5 },
      }
      expect(run(d, '2026')).toEqual({ cur: 6, prev: 6, meses: 3 })
    })

    it('año completo: suma los 12 meses de ambos años', () => {
      const m = (n: number) => Object.fromEntries(Array.from({ length: 12 }, (_, i) => [String(i + 1), n]))
      expect(run({ '2025': m(2), '2024': m(1) }, '2025')).toEqual({ cur: 24, prev: 12, meses: 12 })
    })

    it('año elegido sin datos cargados: no hay comparación (evita un falso -100 %)', () => {
      expect(run({ '2025': { '1': 4 } }, '2026')).toBeNull()
    })

    it('vista por mes: compara con el mes anterior y cruza el cambio de año', () => {
      const d = { '2026': { '1': 4 }, '2025': { '12': 7 } }
      expect(run(d, '2026', '1')).toEqual({ cur: 4, prev: 7 })
    })
  })
})

