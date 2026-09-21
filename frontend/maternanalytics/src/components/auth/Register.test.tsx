import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Register from './Register'

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<p>pantalla login</p>} />
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

async function fillForm(confirm = 'secreto1') {
  await userEvent.type(screen.getByLabelText('Nombre completo'), 'Ana Pérez')
  await userEvent.type(screen.getByLabelText('Correo electrónico'), 'ana@test.com')
  await userEvent.type(screen.getByLabelText('Contraseña'), 'secreto1')
  await userEvent.type(screen.getByLabelText('Confirmar contraseña'), confirm)
  await userEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))
}

describe('Register', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('muestra el encabezado y los cuatro campos', () => {
    renderRegister()
    expect(screen.getByRole('heading', { level: 2, name: 'Crear cuenta' })).toBeInTheDocument()
    expect(screen.getByLabelText('Nombre completo')).toBeInTheDocument()
    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument()
  })

  it('avisa cuando las contraseñas no coinciden y no llama al servidor', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    renderRegister()
    await fillForm('otra-clave')
    expect(await screen.findByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('muestra el mensaje de éxito al crear la cuenta', async () => {
    stubFetch(201, {})
    renderRegister()
    await fillForm()
    expect(await screen.findByText(/cuenta creada exitosamente/i)).toBeInTheDocument()
  })

  it('muestra el error del servidor', async () => {
    stubFetch(400, { detail: 'El correo ya está registrado' })
    renderRegister()
    await fillForm()
    expect(await screen.findByRole('alert')).toHaveTextContent('El correo ya está registrado')
  })

  it('vuelve al login con "Iniciar sesión"', async () => {
    renderRegister()
    await userEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))
    expect(screen.getByText('pantalla login')).toBeInTheDocument()
  })
})
