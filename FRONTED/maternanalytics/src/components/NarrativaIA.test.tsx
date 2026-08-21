import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import NarrativaIA from './NarrativaIA'
import * as api from '../api'

describe('NarrativaIA', () => {
  it('muestra el botón "Generar" en estado inicial', () => {
    render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)
    expect(screen.getByRole('button', { name: /generar/i })).toBeInTheDocument()
  })

  it('muestra la narrativa tras generar exitosamente', async () => {
    vi.spyOn(api, 'obtenerNarrativa').mockResolvedValue({
      narrativa: 'Texto generado de prueba.', modelo: 'qwen2.5',
      generado_en: '2026-08-20T00:00:00Z', desde_cache: false,
    })
    const user = userEvent.setup()
    render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)

    await user.click(screen.getByRole('button', { name: /generar/i }))

    await waitFor(() => expect(screen.getByText('Texto generado de prueba.')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /regenerar/i })).toBeInTheDocument()
  })

  it('no renderiza nada si el backend devuelve null (503)', async () => {
    vi.spyOn(api, 'obtenerNarrativa').mockResolvedValue(null)
    const user = userEvent.setup()
    const { container } = render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)

    await user.click(screen.getByRole('button', { name: /generar/i }))

    await waitFor(() => expect(container.querySelector('.narrativa-ia')).toBeNull())
  })

  it('el botón Regenerar vuelve a llamar a obtenerNarrativa con regenerar=true', async () => {
    const mock = vi.spyOn(api, 'obtenerNarrativa').mockResolvedValue({
      narrativa: 'Texto v1.', modelo: 'qwen2.5', generado_en: '2026-08-20T00:00:00Z', desde_cache: false,
    })
    const user = userEvent.setup()
    render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)
    await user.click(screen.getByRole('button', { name: /generar/i }))
    await waitFor(() => screen.getByText('Texto v1.'))

    await user.click(screen.getByRole('button', { name: /regenerar/i }))

    await waitFor(() => expect(mock).toHaveBeenLastCalledWith(1, 'resumen_ejecutivo', {}, true))
  })
})
