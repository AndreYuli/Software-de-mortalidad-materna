import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Login from './Login'

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<p>pantalla registro</p>} />
        <Route path="/dashboard" element={<p>panel</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function stubFetch(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body }),
  )
}

async function fillAndSubmit() {
  await userEvent.type(screen.getByLabelText('Correo electrónico'), 'ana@test.com')
  await userEvent.type(screen.getByLabelText('Contraseña'), 'secreto1')
  await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
}

describe('Login', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.unstubAllGlobals())

  it('muestra el encabezado y los campos', () => {
    renderLogin()
    expect(screen.getByRole('heading', { level: 2, name: /inicio de sesión/i })).toBeInTheDocument()
    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /recordarme/i })).toBeInTheDocument()
  })

  it('guarda la sesión y navega al panel si las credenciales son válidas', async () => {
    stubFetch(200, { access_token: 'tok', token_type: 'bearer', id: 1, nombre: 'Ana', email: 'ana@test.com' })
    renderLogin()
    await fillAndSubmit()
    expect(await screen.findByText('panel')).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBe('tok')
    expect(localStorage.getItem('username')).toBe('Ana')
  })

  it('muestra el error del servidor cuando las credenciales son incorrectas', async () => {
    stubFetch(401, { detail: 'Credenciales inválidas' })
    renderLogin()
    await fillAndSubmit()
    expect(await screen.findByRole('alert')).toHaveTextContent('Credenciales inválidas')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('muestra el aviso informativo al pulsar "¿Olvidaste tu contraseña?"', async () => {
    renderLogin()
    await userEvent.click(screen.getByRole('button', { name: /olvidaste/i }))
    expect(screen.getByRole('status')).toHaveTextContent(/recuperación de contraseñas/i)
  })

  it('lleva a la pantalla de registro con "Crear cuenta"', async () => {
    renderLogin()
    await userEvent.click(screen.getByRole('button', { name: /crear cuenta/i }))
    expect(screen.getByText('pantalla registro')).toBeInTheDocument()
  })
})
