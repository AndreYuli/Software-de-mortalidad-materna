import { describe, expect, it } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useDocumentTitle } from './useDocumentTitle'

describe('useDocumentTitle', () => {
  it('pone "<titulo> · VidaMaterna" mientras está montado', () => {
    const { unmount } = renderHook(() => useDocumentTitle('Historial de cargas'))
    expect(document.title).toBe('Historial de cargas · VidaMaterna')
    unmount()
  })

  it('actualiza el título al cambiar y restaura la base al desmontar', () => {
    const { rerender, unmount } = renderHook(({ titulo }: { titulo: string }) => useDocumentTitle(titulo), {
      initialProps: { titulo: 'Historial de cargas' },
    })
    expect(document.title).toBe('Historial de cargas · VidaMaterna')
    rerender({ titulo: 'Análisis' })
    expect(document.title).toBe('Análisis · VidaMaterna')
    unmount()
    expect(document.title).toBe('VidaMaterna')
  })
})
