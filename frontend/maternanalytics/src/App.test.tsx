import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import App from './App'

const mounts = vi.hoisted(() => ({ sidebar: 0 }))

vi.mock('./hooks/useDashboardData', () => ({
  useDashboardData: () => ({
    username: 'Ana',
    email: 'ana@correo.co',
    avatarLetter: 'A',
    mortalidadFile: null,
    mortalidadError: null,
    morbilidadFile: null,
    morbilidadError: null,
  }),
}))

vi.mock('./components/dashboard/Sidebar', async () => {
  const { useEffect } = await import('react')
  return {
    Sidebar: ({ onNavigate }: { onNavigate: (view: string) => void }) => {
      // Cuenta los montajes: si el layout se remonta al cambiar de ruta, sube.
      useEffect(() => {
        mounts.sidebar += 1
      }, [])
      return (
        <nav>
          <button onClick={() => onNavigate('historial')}>ir-historial</button>
          <button onClick={() => onNavigate('mortalidad')}>ir-mortalidad</button>
          <button onClick={() => onNavigate('analisis')}>ir-dashboard</button>
        </nav>
      )
    },
  }
})

vi.mock('./components/dashboard/DashboardViewRoute', () => ({
  DashboardViewRoute: ({ view }: { view: string }) => <div data-testid="vista">{view}</div>,
}))

describe('rutas de App', () => {
  beforeEach(() => {
    mounts.sidebar = 0
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('sin token redirige a /login', async () => {
    window.history.pushState({}, '', '/historial')
    render(<App />)
    await screen.findByRole('button', { name: /iniciar sesi/i })
    expect(window.location.pathname).toBe('/login')
  })

  it('con token, / y /dashboard muestran la vista de análisis', async () => {
    localStorage.setItem('token', 'abc')
    window.history.pushState({}, '', '/')
    const { unmount } = render(<App />)
    expect((await screen.findByTestId('vista')).textContent).toBe('analisis')
    unmount()

    window.history.pushState({}, '', '/dashboard')
    render(<App />)
    expect((await screen.findByTestId('vista')).textContent).toBe('analisis')
  })

  it('cambiar de vista navega y no remonta el layout', async () => {
    localStorage.setItem('token', 'abc')
    window.history.pushState({}, '', '/dashboard')
    render(<App />)
    await screen.findByText('analisis')

    fireEvent.click(screen.getByText('ir-historial'))
    expect((await screen.findByTestId('vista')).textContent).toBe('historial')
    expect(window.location.pathname).toBe('/historial')

    fireEvent.click(screen.getByText('ir-mortalidad'))
    expect((await screen.findByTestId('vista')).textContent).toBe('mortalidad')
    expect(window.location.pathname).toBe('/cargar-mortalidad')

    fireEvent.click(screen.getByText('ir-dashboard'))
    expect((await screen.findByTestId('vista')).textContent).toBe('analisis')
    expect(window.location.pathname).toBe('/dashboard')

    // El Sidebar (parte del layout) se montó una sola vez durante toda la navegación.
    expect(mounts.sidebar).toBe(1)
  })
})
