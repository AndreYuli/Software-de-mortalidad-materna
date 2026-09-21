import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import AuthCard from './AuthCard'

describe('AuthCard', () => {
  it('muestra la marca, el título, el subtítulo, el contenido y el pie', () => {
    render(
      <AuthCard title="Inicio de sesión" subtitle="Ingresa tus datos" footer={<span>pie</span>}>
        <p>contenido</p>
      </AuthCard>,
    )
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('VidaMaterna')
    expect(screen.getByRole('heading', { level: 2, name: 'Inicio de sesión' })).toBeInTheDocument()
    expect(screen.getByText('Ingresa tus datos')).toBeInTheDocument()
    expect(screen.getByText('contenido')).toBeInTheDocument()
    expect(screen.getByText('pie')).toBeInTheDocument()
  })

  it('no renderiza pie si no se indica', () => {
    render(
      <AuthCard title="Crear cuenta" subtitle="Datos">
        <p>contenido</p>
      </AuthCard>,
    )
    expect(screen.queryByText('pie')).not.toBeInTheDocument()
  })
})
