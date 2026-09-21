import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import DashboardOKD from './DashboardOKD'

vi.mock('../hooks/useDashboardData', () => ({
  useDashboardData: () => ({
    username: 'Ana Pérez',
    email: 'ana@test.com',
    avatarLetter: 'A',
    mortalidadFile: null,
    mortalidadError: null,
    morbilidadFile: null,
    morbilidadError: null,
  }),
}))

function renderLayout(path = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<DashboardOKD />}>
          <Route path="dashboard" element={<p>vista analisis</p>} />
          <Route path="historial" element={<p>vista historial</p>} />
        </Route>
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('DashboardOKD', () => {
  beforeEach(() => localStorage.clear())

  it('muestra la vista hija dentro de un único main y los datos del usuario', () => {
    renderLayout()
    expect(screen.getAllByRole('main')).toHaveLength(1)
    expect(screen.getByRole('main')).toHaveTextContent('vista analisis')
    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('ana@test.com')).toBeInTheDocument()
  })

  it('marca como activa la vista de la URL actual', () => {
    renderLayout('/historial')
    expect(screen.getByRole('button', { name: /Historial de Cargas/ })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: /Dashboard Analítico/ })).not.toHaveAttribute('aria-current')
  })

  it('abre el menú móvil con "Abrir menú" y lo cierra al pulsar el fondo', async () => {
    renderLayout()
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú' }))
    expect(screen.getByTestId('sidebar-overlay')).toBeInTheDocument()
    expect(screen.getByRole('complementary')).toHaveClass('translate-x-0')

    await userEvent.click(screen.getByTestId('sidebar-overlay'))
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()
    expect(screen.getByRole('complementary')).toHaveClass('-translate-x-full')
  })

  it('cierra el menú móvil con el botón "Cerrar menú"', async () => {
    renderLayout()
    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar menú' }))
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()
  })

  it('navegar desde el menú cambia de vista y cierra el menú', async () => {
    renderLayout()
    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú' }))
    await userEvent.click(screen.getByRole('button', { name: /Historial de Cargas/ }))
    expect(await screen.findByText('vista historial')).toBeInTheDocument()
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()
  })

  it('cerrar sesión borra la sesión y lleva al login', async () => {
    localStorage.setItem('token', 'tok')
    renderLayout()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBeNull()
  })
})
