import { afterEach, describe, expect, it, vi } from 'vitest'
import { describeNetworkError, extractErrorMessage, fetchWithTimeout } from './api'

describe('extractErrorMessage', () => {
  it('devuelve detail cuando es string', () => {
    expect(extractErrorMessage({ detail: 'Faltan columnas' }, 'x')).toBe('Faltan columnas')
  })

  it('toma el primer msg cuando detail es la lista de un 422', () => {
    expect(extractErrorMessage({ detail: [{ msg: 'value is not a valid email' }] }, 'x')).toBe(
      'value is not a valid email',
    )
  })

  it('usa el fallback con cuerpos vacíos o inesperados', () => {
    expect(extractErrorMessage(null, 'fallback')).toBe('fallback')
    expect(extractErrorMessage({ detail: [{}] }, 'fallback')).toBe('fallback')
    expect(extractErrorMessage({ detail: '  ' }, 'fallback')).toBe('fallback')
  })
})

describe('fetchWithTimeout', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('lanza TimeoutError si la petición no responde a tiempo', async () => {
    vi.useFakeTimers()
    vi.stubGlobal(
      'fetch',
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
        }),
    )
    const pending = fetchWithTimeout('/x', {}, 1000)
    const assertion = expect(pending).rejects.toMatchObject({ name: 'TimeoutError' })
    await vi.advanceTimersByTimeAsync(1001)
    await assertion
  })

  it('propaga errores de red que no son timeout', async () => {
    vi.stubGlobal('fetch', () => Promise.reject(new TypeError('Failed to fetch')))
    await expect(fetchWithTimeout('/x')).rejects.toThrow('Failed to fetch')
  })
})

describe('describeNetworkError', () => {
  it('muestra el mensaje del timeout y el fallback para lo demás', () => {
    const timeout = Object.assign(new Error('tardó'), { name: 'TimeoutError' })
    expect(describeNetworkError(timeout, 'sin conexión')).toBe('tardó')
    expect(describeNetworkError(new TypeError('x'), 'sin conexión')).toBe('sin conexión')
  })
})
