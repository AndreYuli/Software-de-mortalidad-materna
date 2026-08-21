import { describe, expect, it, vi } from 'vitest'
import { API_URL, obtenerNarrativa } from './api'

describe('api', () => {
  it('expone una URL base http válida', () => {
    expect(API_URL).toMatch(/^https?:\/\//)
  })
})

describe('obtenerNarrativa', () => {
  it('arma la URL con filtros y llama a fetch', async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ narrativa: 'texto', modelo: 'qwen2.5', generado_en: '2026-08-20', desde_cache: false }),
      } as Response)
    )
    vi.stubGlobal('fetch', fetchMock)

    const resultado = await obtenerNarrativa(1, 'resumen_ejecutivo', { year: '2026' })

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/analisis/1/narrativa/resumen_ejecutivo/?year=2026'))
    expect(resultado?.narrativa).toBe('texto')
  })

  it('devuelve null si el backend responde 503', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false, status: 503 } as Response)))

    const resultado = await obtenerNarrativa(1, 'resumen_ejecutivo')

    expect(resultado).toBeNull()
  })
})
