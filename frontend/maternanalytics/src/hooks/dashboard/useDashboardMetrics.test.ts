import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useDashboardMetrics } from './useDashboardMetrics'
import type { AnalisisCompleto } from '../../types'

function fixture(totalCasos: number): AnalisisCompleto {
  return { estadisticas_basicas: { total_casos: totalCasos } } as unknown as AnalisisCompleto
}

describe('useDashboardMetrics', () => {
  it('calcula la tasa de letalidad como mortalidad sobre morbilidad', () => {
    const { result } = renderHook(() =>
      useDashboardMetrics({
        segmento: 'ambos',
        mortalidadData: fixture(30),
        morbilidadData: fixture(10),
        filterYear: '',
        filterMonth: '',
      }),
    )
    expect(result.current.tasaLetalidad).toBe('300.0')
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

  it('retorna "0" cuando morbilidad es 0 (evita division por cero)', () => {
    const { result } = renderHook(() =>
      useDashboardMetrics({
        segmento: 'ambos',
        mortalidadData: fixture(30),
        morbilidadData: fixture(0),
        filterYear: '',
        filterMonth: '',
      }),
    )
    expect(result.current.tasaLetalidad).toBe('0')
  })
})
