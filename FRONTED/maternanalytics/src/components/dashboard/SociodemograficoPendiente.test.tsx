import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SociodemograficoPendiente } from './SociodemograficoPendiente'

describe('SociodemograficoPendiente', () => {
  it('muestra el nombre del evento en el título', () => {
    render(<SociodemograficoPendiente evento="Morbilidad" />)
    expect(screen.getByText('Factores Sociodemográficos de Morbilidad')).toBeInTheDocument()
  })

  it('explica por qué la sección está pendiente', () => {
    render(<SociodemograficoPendiente evento="Mortalidad" />)
    expect(screen.getByText(/zona, etnia, estrato/i)).toBeInTheDocument()
  })
})
