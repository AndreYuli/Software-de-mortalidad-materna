import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MainTabs } from './MainTabs'

describe('MainTabs', () => {
  it('muestra las tres pestañas, en orden, dentro de un tablist', () => {
    render(<MainTabs active="generalidades" onChange={vi.fn()} />)
    expect(screen.getByRole('tablist', { name: 'Secciones del análisis' })).toBeInTheDocument()
    const tabs = screen.getAllByRole('tab')
    expect(tabs.map((t) => t.textContent)).toEqual([
      'Generalidades',
      'Morbilidad (Ev. 549)',
      'Mortalidad (Ev. 550)',
    ])
  })

  it('marca solo la pestaña activa con aria-selected', () => {
    render(<MainTabs active="morbilidad" onChange={vi.fn()} />)
    expect(screen.getByRole('tab', { name: 'Morbilidad (Ev. 549)' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Generalidades' })).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByRole('tab', { name: 'Mortalidad (Ev. 550)' })).toHaveAttribute('aria-selected', 'false')
  })

  it('llama a onChange con la clave de la pestaña pulsada', async () => {
    const onChange = vi.fn()
    render(<MainTabs active="generalidades" onChange={onChange} />)
    await userEvent.click(screen.getByRole('tab', { name: 'Mortalidad (Ev. 550)' }))
    expect(onChange).toHaveBeenCalledWith('mortalidad')
  })
})
