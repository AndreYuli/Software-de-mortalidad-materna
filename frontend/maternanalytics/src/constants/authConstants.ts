// Catálogo de departamentos y secretarías habilitadas al registrarse.
// Debe mantenerse en sincronía con backend/core/tenant.py: la secretaría elegida
// define el tenant con el que se aíslan los datos del usuario.

export interface Secretaria {
  codigo: string
  nombre: string
}

export interface Departamento {
  codigo: string
  nombre: string
  secretarias: Secretaria[]
}

export const DEPARTAMENTOS: Departamento[] = [
  {
    codigo: 'antioquia',
    nombre: 'Antioquia',
    secretarias: [
      { codigo: 'bello', nombre: 'Secretaría de Salud de Bello' },
      { codigo: 'envigado', nombre: 'Secretaría de Salud de Envigado' },
      { codigo: 'itagui', nombre: 'Secretaría de Salud de Itagüí' },
    ],
  },
]

/** Devuelve las secretarías del departamento indicado (vacio si no se ha elegido). */
export function secretariasDe(codigoDepartamento: string | undefined): Secretaria[] {
  if (!codigoDepartamento) return []
  return DEPARTAMENTOS.find((d) => d.codigo === codigoDepartamento)?.secretarias ?? []
}

/**
 * Nombre corto (el municipio) a partir del nombre completo de la secretaría.
 * «Secretaría de Salud de Bello» -> «Bello». Si no coincide con el patron, devuelve
 * el texto original para no perder información.
 */
export function municipioDeSecretaria(secretaria: string | null | undefined): string {
  if (!secretaria) return ''
  return secretaria.replace(/^Secretar[ií]a de Salud de\s+/i, '').trim()
}
