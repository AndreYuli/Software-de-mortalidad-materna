import { describe, expect, it, vi } from 'vitest'
import { render } from '@testing-library/react'
import DashboardOKD from './DashboardOKD'

vi.mock('react-plotly.js', () => ({ default: () => null }))

describe('DashboardOKD', () => {
  it('renderiza sin lanzar errores', () => {
    render(<DashboardOKD onLogout={vi.fn()} />)
    expect(document.body).toBeInTheDocument()
  })
})
