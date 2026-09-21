import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NavItem } from './NavItem'

const icon = <svg data-testid="icono" />

describe('NavItem', () => {
  it('muestra el icono y la etiqueta y llama a onClick', async () => {
    const onClick = vi.fn()
    render(<NavItem icon={icon} label="Historial" active={false} onClick={onClick} />)
    expect(screen.getByTestId('icono')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Historial' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('marca el ítem activo con aria-current', () => {
    render(<NavItem icon={icon} label="Historial" active onClick={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Historial' })).toHaveAttribute('aria-current', 'page')
  })

  it('no marca aria-current en un ítem inactivo', () => {
    render(<NavItem icon={icon} label="Historial" active={false} onClick={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Historial' })).not.toHaveAttribute('aria-current')
  })

  it('no muestra indicadores sin status', () => {
    render(<NavItem icon={icon} label="Mortalidad" active={false} onClick={vi.fn()} />)
    expect(screen.queryByLabelText('Archivo cargado correctamente')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Error en el archivo cargado')).not.toBeInTheDocument()
  })

  it('muestra el indicador de archivo cargado', () => {
    render(<NavItem icon={icon} label="Mortalidad" active={false} onClick={vi.fn()} status={{ hasFile: true }} />)
    expect(screen.getByLabelText('Archivo cargado correctamente')).toBeInTheDocument()
    expect(screen.queryByLabelText('Error en el archivo cargado')).not.toBeInTheDocument()
  })

  it('el indicador de error tiene prioridad sobre el de archivo cargado', () => {
    render(
      <NavItem icon={icon} label="Mortalidad" active={false} onClick={vi.fn()} status={{ hasFile: true, hasError: true }} />,
    )
    expect(screen.getByLabelText('Error en el archivo cargado')).toBeInTheDocument()
    expect(screen.queryByLabelText('Archivo cargado correctamente')).not.toBeInTheDocument()
  })
})
