import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Register from './Register'

describe('Register', () => {
  it('renderiza el formulario de registro', () => {
    render(<Register onRegistered={vi.fn()} onBack={vi.fn()} />)
    expect(screen.getByRole('button', { name: /crear cuenta/i })).toBeInTheDocument()
  })
})
