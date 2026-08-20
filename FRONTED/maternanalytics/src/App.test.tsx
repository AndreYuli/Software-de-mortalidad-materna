import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('muestra la vista de inicio de sesión por defecto', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /inicio de sesión/i })).toBeInTheDocument()
  })
})
