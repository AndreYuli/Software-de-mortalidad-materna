import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SubTabs } from './SubTabs'

describe('SubTabs', () => {
  it('renderiza los botones de Factores Sociodemográficos y Factores Clínicos', () => {
    render(<SubTabs active="clinico" onChange={() => {}} />)
    expect(screen.getByText('Factores Sociodemográficos')).toBeInTheDocument()
    expect(screen.getByText('Factores Clínicos')).toBeInTheDocument()
  })

  it('marca como activo el botón correspondiente a `active`', () => {
    render(<SubTabs active="sociodemografico" onChange={() => {}} />)
    expect(screen.getByText('Factores Sociodemográficos')).toHaveClass('active')
    expect(screen.getByText('Factores Clínicos')).not.toHaveClass('active')
  })

  it('llama a onChange con la clave de la subpestaña al hacer click', () => {
    const onChange = vi.fn()
    render(<SubTabs active="clinico" onChange={onChange} />)
    fireEvent.click(screen.getByText('Factores Sociodemográficos'))
    expect(onChange).toHaveBeenCalledWith('sociodemografico')
  })
})
