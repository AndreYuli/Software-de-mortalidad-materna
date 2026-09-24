import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DashboardLoadingState } from './DashboardLoadingState'
import { DashboardErrorState } from './DashboardErrorState'

describe('DashboardLoadingState', () => {
  it('anuncia la carga con role="status"', () => {
    render(<DashboardLoadingState />)
    expect(screen.getByRole('status')).toHaveTextContent('Generando panel estratégico...')
  })
})

describe('DashboardErrorState', () => {
  it('muestra el mensaje con role="alert" y sin emoji', () => {
    render(<DashboardErrorState message="No se pudo cargar el análisis" onRetry={vi.fn()} />)
    const alerta = screen.getByRole('alert')
    expect(alerta).toHaveTextContent('No se pudo cargar el análisis')
    expect(alerta.textContent).not.toContain('❌')
  })

  it('Reintentar llama a onRetry', async () => {
    const onRetry = vi.fn()
    render(<DashboardErrorState message="Falla" onRetry={onRetry} />)
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
