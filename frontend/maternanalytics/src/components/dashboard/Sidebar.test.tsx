import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Sidebar, type SidebarProps } from './Sidebar'

function renderSidebar(overrides: Partial<SidebarProps> = {}) {
  const props: SidebarProps = {
    user: { username: 'Ana Pérez', email: 'ana@test.com', avatarLetter: 'A' },
    activeView: 'analisis',
    onNavigate: vi.fn(),
    fileStatus: {},
    onLogout: vi.fn(),
    ...overrides,
  }
  render(<Sidebar {...props} />)
  return props
}

describe('Sidebar', () => {
  it('muestra la marca, la navegación y los tres grupos', () => {
    renderSidebar()
    expect(screen.getByRole('navigation', { name: 'Navegación principal' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Dashboard Analítico/ })).toBeInTheDocument()
    expect(screen.getByText('Carga de Datos')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Mortalidad Materna/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Morbilidad Extrema/ })).toBeInTheDocument()
    expect(screen.getByText('Administración')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Historial de Cargas/ })).toBeInTheDocument()
  })

  it('marca solo la vista activa con aria-current', () => {
    renderSidebar({ activeView: 'historial' })
    expect(screen.getByRole('button', { name: /Historial de Cargas/ })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: /Dashboard Analítico/ })).not.toHaveAttribute('aria-current')
  })

  it('llama a onNavigate con la vista de cada ítem', async () => {
    const { onNavigate } = renderSidebar()
    await userEvent.click(screen.getByRole('button', { name: /Dashboard Analítico/ }))
    await userEvent.click(screen.getByRole('button', { name: /Mortalidad Materna/ }))
    await userEvent.click(screen.getByRole('button', { name: /Morbilidad Extrema/ }))
    await userEvent.click(screen.getByRole('button', { name: /Historial de Cargas/ }))
    expect(onNavigate).toHaveBeenNthCalledWith(1, 'analisis')
    expect(onNavigate).toHaveBeenNthCalledWith(2, 'mortalidad')
    expect(onNavigate).toHaveBeenNthCalledWith(3, 'morbilidad')
    expect(onNavigate).toHaveBeenNthCalledWith(4, 'historial')
  })

  it('muestra los indicadores de archivo cargado y de error', () => {
    renderSidebar({
      fileStatus: { mortalidad: { hasFile: true }, morbilidad: { hasFile: true, hasError: true } },
    })
    expect(screen.getByLabelText('Archivo cargado correctamente')).toBeInTheDocument()
    expect(screen.getByLabelText('Error en el archivo cargado')).toBeInTheDocument()
  })

  it('muestra el usuario y su correo', () => {
    renderSidebar()
    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('ana@test.com')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('muestra un texto por defecto si no hay correo', () => {
    renderSidebar({ user: { username: 'Ana Pérez', avatarLetter: 'A' } })
    expect(screen.getByText('VidaMaterna Analytics')).toBeInTheDocument()
  })

  it('llama a onLogout al cerrar sesión', async () => {
    const { onLogout } = renderSidebar()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(onLogout).toHaveBeenCalledTimes(1)
  })

  it('llama a onMobileClose con el botón de cerrar menú', async () => {
    const onMobileClose = vi.fn()
    renderSidebar({ onMobileClose })
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar menú' }))
    expect(onMobileClose).toHaveBeenCalledTimes(1)
  })

  it('oculta el cajón en móvil cuando está cerrado y lo muestra cuando está abierto', () => {
    const { rerender } = render(
      <Sidebar
        user={{ username: 'Ana', avatarLetter: 'A' }}
        activeView="analisis"
        onNavigate={vi.fn()}
        fileStatus={{}}
        onLogout={vi.fn()}
      />,
    )
    expect(screen.getByRole('complementary')).toHaveClass('-translate-x-full')

    rerender(
      <Sidebar
        user={{ username: 'Ana', avatarLetter: 'A' }}
        activeView="analisis"
        onNavigate={vi.fn()}
        fileStatus={{}}
        onLogout={vi.fn()}
        isMobileOpen
      />,
    )
    expect(screen.getByRole('complementary')).toHaveClass('translate-x-0')
    expect(screen.getByRole('complementary')).not.toHaveClass('-translate-x-full')
  })
})
