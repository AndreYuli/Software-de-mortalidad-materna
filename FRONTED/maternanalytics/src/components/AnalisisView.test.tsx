import { describe, expect, it, vi } from 'vitest'
import { render } from '@testing-library/react'
import AnalisisView from './AnalisisView'

vi.mock('react-plotly.js', () => ({ default: () => null }))
vi.stubGlobal('fetch', vi.fn(() =>
  Promise.resolve({ ok: true, json: () => Promise.resolve({}) } as Response)
))

describe('AnalisisView', () => {
  it('renderiza sin lanzar errores con props mínimas', () => {
    render(<AnalisisView analisisId={1} />)
    expect(document.body).toBeInTheDocument()
  })
})
