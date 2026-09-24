import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WelcomeState } from './WelcomeState'

describe('WelcomeState', () => {
  it('muestra el título y el botón de importar, sin las opciones todavía', () => {
    render(<WelcomeState onGoToUpload={vi.fn()} />)
    expect(screen.getByRole('heading', { name: 'Análisis Epidemiológico' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Mortalidad/ })).not.toBeInTheDocument()
  })

  it('al pulsar Importar muestra las dos opciones y oculta el botón', async () => {
    render(<WelcomeState onGoToUpload={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' }))
    expect(screen.getByRole('button', { name: /Mortalidad/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Morbilidad Extrema/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Importar Datos Epidemiológicos' })).not.toBeInTheDocument()
  })

  it('Mortalidad lleva a la carga de mortalidad', async () => {
    const onGoToUpload = vi.fn()
    render(<WelcomeState onGoToUpload={onGoToUpload} />)
    await userEvent.click(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' }))
    await userEvent.click(screen.getByRole('button', { name: /Mortalidad/ }))
    expect(onGoToUpload).toHaveBeenCalledWith('mortalidad')
  })

  it('Morbilidad Extrema lleva a la carga de morbilidad', async () => {
    const onGoToUpload = vi.fn()
    render(<WelcomeState onGoToUpload={onGoToUpload} />)
    await userEvent.click(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' }))
    await userEvent.click(screen.getByRole('button', { name: /Morbilidad Extrema/ }))
    expect(onGoToUpload).toHaveBeenCalledWith('morbilidad')
  })
})
