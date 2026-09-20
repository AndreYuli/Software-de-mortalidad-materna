import { describe, it, expect } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { useDashboardTabs } from './useDashboardTabs'

describe('useDashboardTabs', () => {
  it('inicia en la pestaña generalidades y en la subpestaña clínica', () => {
    const { result } = renderHook(() => useDashboardTabs())
    expect(result.current.activeTab).toBe('generalidades')
    expect(result.current.activeSubTab).toBe('clinico')
  })

  it('cambia de pestaña principal con setActiveTab', () => {
    const { result } = renderHook(() => useDashboardTabs())
    act(() => result.current.setActiveTab('morbilidad'))
    expect(result.current.activeTab).toBe('morbilidad')
  })

  it('permite cambiar de subpestaña con setActiveSubTab', () => {
    const { result } = renderHook(() => useDashboardTabs())
    act(() => result.current.setActiveSubTab('sociodemografico'))
    expect(result.current.activeSubTab).toBe('sociodemografico')
  })

  it('reinicia la subpestaña a clínico al cambiar de pestaña principal', () => {
    const { result } = renderHook(() => useDashboardTabs())
    act(() => result.current.setActiveSubTab('sociodemografico'))
    expect(result.current.activeSubTab).toBe('sociodemografico')

    act(() => result.current.setActiveTab('mortalidad'))
    expect(result.current.activeSubTab).toBe('clinico')
  })
})
