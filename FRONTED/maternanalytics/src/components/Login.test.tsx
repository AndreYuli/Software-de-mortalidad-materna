import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Login from './Login'

describe('Login', () => {
  it('renderiza el formulario de inicio de sesión', () => {
    render(<Login onLogin={vi.fn()} onRegister={vi.fn()} />)
    expect(screen.getByRole('heading', { name: /inicio de sesión/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })
})
