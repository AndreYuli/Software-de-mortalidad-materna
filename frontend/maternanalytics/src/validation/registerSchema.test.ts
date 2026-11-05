import { describe, expect, it } from 'vitest'
import { registerSchema } from './registerSchema'

const baseValido = {
  nombre: 'Ana Pérez',
  email: 'ana@test.com',
  password: 'secreto12',
  confirmPassword: 'secreto12',
  departamento: 'antioquia',
  secretaria: 'bello',
}

describe('registerSchema nombre', () => {
  it('acepta un nombre de 120 caracteres', () => {
    const resultado = registerSchema.safeParse({ ...baseValido, nombre: 'a'.repeat(120) })
    expect(resultado.success).toBe(true)
  })

  it('rechaza un nombre de 121 caracteres con el mensaje esperado', () => {
    const resultado = registerSchema.safeParse({ ...baseValido, nombre: 'a'.repeat(121) })
    expect(resultado.success).toBe(false)
    if (!resultado.success) {
      const mensajes = resultado.error.issues
        .filter((issue) => issue.path.join('.') === 'nombre')
        .map((issue) => issue.message)
      expect(mensajes).toContain('El nombre no puede superar 120 caracteres')
    }
  })
})
