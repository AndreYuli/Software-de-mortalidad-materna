import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { clearSession, describeNetworkError, extractErrorMessage, fetchWithTimeout, enviarMensajeChat } from './api'

describe('extractErrorMessage', () => {
  it('devuelve detail cuando es string', () => {
    expect(extractErrorMessage({ detail: 'Faltan columnas' }, 'x')).toBe('Faltan columnas')
  })

  it('toma el primer msg cuando detail es la lista de un 422 (mensaje ya en español)', () => {
    expect(extractErrorMessage({ detail: [{ msg: 'Debe ser un número entre 1 y 12.' }] }, 'x')).toBe(
      'Debe ser un número entre 1 y 12.',
    )
  })

  it('toma el primer msg cuando detail es la lista de un 422', () => {
    expect(extractErrorMessage({ detail: [{ msg: 'value is not a valid email' }] }, 'x')).toBe(
      'El correo electrónico no es válido. Usa un correo institucional válido, por ejemplo tu.correo@institucion.gov.co.',
    )
  })

  it('traduce el error de correo de Pydantic (revisión de uso, parte 1, problema 1)', () => {
    const body = {
      detail: [
        {
          type: 'value_error',
          loc: ['body', 'email'],
          msg: 'value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email.',
        },
      ],
    }
    expect(extractErrorMessage(body, 'x')).toBe(
      'Ingresa un correo electrónico válido, con un dominio real (por ejemplo, nombre@institucion.gov.co).',
    )
  })

  it('quita el prefijo "Value error," de los validadores propios', () => {
    const body = { detail: [{ type: 'value_error', loc: ['body', 'password'], msg: 'Value error, La contraseña es demasiado común; elige otra.' }] }
    expect(extractErrorMessage(body, 'x')).toBe('La contraseña es demasiado común; elige otra.')
  })

  it('traduce longitudes mínima y máxima indicando el campo', () => {
    expect(
      extractErrorMessage(
        { detail: [{ type: 'string_too_short', loc: ['body', 'password'], msg: 'String should have at least 8 characters', ctx: { min_length: 8 } }] },
        'x',
      ),
    ).toBe('La contraseña debe tener al menos 8 caracteres.')
    expect(
      extractErrorMessage(
        { detail: [{ type: 'string_too_long', loc: ['body', 'nombre'], msg: 'String should have at most 120 characters', ctx: { max_length: 120 } }] },
        'x',
      ),
    ).toBe('El nombre no puede superar 120 caracteres.')
  })

  it('un mensaje en inglés sin traducción conocida cae al fallback, no se muestra crudo', () => {
    expect(extractErrorMessage({ detail: [{ type: 'weird', loc: ['query', 'x'], msg: 'Some english text' }] }, 'fallback')).toBe('fallback')
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

describe('fetchWithTimeout — sesión', () => {
  const replace = vi.fn()

  beforeEach(() => {
    localStorage.clear()
    replace.mockReset()
    vi.stubGlobal('location', { pathname: '/dashboard', replace })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  const stubFetch = (status: number) => {
    const spy = vi.fn().mockResolvedValue(new Response('{}', { status }))
    vi.stubGlobal('fetch', spy)
    return spy
  }

  it('adjunta Authorization: Bearer en llamadas protegidas', async () => {
    localStorage.setItem('token', 'abc')
    const spy = stubFetch(200)
    await fetchWithTimeout('http://x/api/analisis/')
    const headers = spy.mock.calls[0][1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer abc')
  })

  it('no adjunta Bearer en login/registro', async () => {
    localStorage.setItem('token', 'abc')
    const spy = stubFetch(200)
    await fetchWithTimeout('http://x/api/auth/login/')
    expect((spy.mock.calls[0][1].headers as Headers).has('Authorization')).toBe(false)
  })

  it('ante un 401 borra la sesión y redirige a /login', async () => {
    localStorage.setItem('token', 'abc')
    localStorage.setItem('username', 'Ana')
    localStorage.setItem('user_email', 'a@a.co')
    stubFetch(401)
    await fetchWithTimeout('http://x/api/analisis/')
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('username')).toBeNull()
    expect(replace).toHaveBeenCalledWith('/login')
  })

  it('un 401 de login (credenciales malas) no redirige ni borra nada', async () => {
    localStorage.setItem('token', 'abc')
    stubFetch(401)
    await fetchWithTimeout('http://x/api/auth/login/')
    expect(localStorage.getItem('token')).toBe('abc')
    expect(replace).not.toHaveBeenCalled()
  })

  it('clearSession elimina token, username y user_email', () => {
    localStorage.setItem('token', 't')
    localStorage.setItem('username', 'u')
    localStorage.setItem('user_email', 'e')
    clearSession()
    expect(localStorage.length).toBe(0)
  })
})

describe('enviarMensajeChat', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('devuelve el objeto con respuesta y modelo si status 200', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ respuesta: 'Hola', modelo: 'test' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    )
    const res = await enviarMensajeChat(1, 'hola', [])
    expect(res).toEqual({ respuesta: 'Hola', modelo: 'test' })
  })

  it('devuelve null si status es 503', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 503 })))
    const res = await enviarMensajeChat(1, 'hola', [])
    expect(res).toBeNull()
  })

  it('lanza error extraído del cuerpo si status no ok y no 503', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Error de prueba' }), { status: 400 })
      )
    )
    await expect(enviarMensajeChat(1, 'hola', [])).rejects.toThrow('Error de prueba')
  })
})
