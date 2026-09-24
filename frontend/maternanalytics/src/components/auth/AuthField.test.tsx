import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Mail } from 'lucide-react'
import type { UseFormRegisterReturn } from 'react-hook-form'
import AuthField from './AuthField'

const registration = {
  name: 'campo',
  onChange: vi.fn(),
  onBlur: vi.fn(),
  ref: vi.fn(),
} as unknown as UseFormRegisterReturn

describe('AuthField', () => {
  it('asocia la etiqueta con el input', () => {
    render(<AuthField id="email" label="Correo electrónico" icon={Mail} type="email" registration={registration} />)
    expect(screen.getByLabelText('Correo electrónico')).toHaveAttribute('type', 'email')
  })

  it('muestra el error y marca el input como inválido', () => {
    render(<AuthField id="email" label="Correo" icon={Mail} error="Formato inválido" registration={registration} />)
    expect(screen.getByText('Formato inválido')).toBeInTheDocument()
    expect(screen.getByLabelText('Correo')).toHaveAttribute('aria-invalid', 'true')
  })

  it('no muestra botón de ver en campos que no son contraseña', () => {
    render(<AuthField id="email" label="Correo" icon={Mail} type="email" registration={registration} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('alterna la visibilidad de la contraseña', async () => {
    render(<AuthField id="pw" label="Contraseña" icon={Mail} type="password" registration={registration} />)
    const input = screen.getByLabelText('Contraseña')
    expect(input).toHaveAttribute('type', 'password')

    await userEvent.click(screen.getByRole('button', { name: 'Mostrar' }))
    expect(input).toHaveAttribute('type', 'text')

    await userEvent.click(screen.getByRole('button', { name: 'Ocultar' }))
    expect(input).toHaveAttribute('type', 'password')
  })
})
