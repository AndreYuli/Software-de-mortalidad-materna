import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AiSummaryPanel } from './AiSummaryPanel'

describe('AiSummaryPanel', () => {
  it('empieza cerrado', () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    expect(screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ })).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByText('contenido de la IA')).not.toBeVisible()
  })

  it('se abre y se cierra con el botón', async () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    const boton = screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ })

    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('contenido de la IA')).toBeVisible()

    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByText('contenido de la IA')).not.toBeVisible()
  })

  it('muestra el aviso de validación al abrirlo', async () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    expect(screen.getByText(/requiere validación del equipo de vigilancia/)).not.toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ }))
    expect(screen.getByText(/Generado automáticamente por IA local/)).toBeVisible()
  })

  it('el botón controla el panel con aria-controls', () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    const boton = screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ })
    expect(document.getElementById(boton.getAttribute('aria-controls') as string)).not.toBeNull()
  })
})
