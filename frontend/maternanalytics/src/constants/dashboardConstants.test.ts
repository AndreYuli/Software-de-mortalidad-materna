import { describe, it, expect } from 'vitest'
import { getCie10Description } from './dashboardConstants'

describe('getCie10Description', () => {
  it('resuelve un código real del catálogo CIE-10, con o sin punto', () => {
    expect(getCie10Description('O141')).toBe('Preeclampsia Severa')
    expect(getCie10Description('O14.1')).toBe('Preeclampsia Severa')
  })

  it('retorna el mensaje por defecto para un código inexistente', () => {
    expect(getCie10Description('Z999999')).toBe('Descripción no disponible')
  })

  it('resuelve un código de 3 caracteres contra la entrada con relleno "X" del catálogo', () => {
    expect(getCie10Description('O85')).toBe('Sepsis Puerperal')
    expect(getCie10Description('O94')).toBe('Secuelas De Complicaciones Del Embarazo, Del Parto Y Del Puerperio')
  })

  it('retorna el mensaje por defecto para un código vacío o nulo', () => {
    expect(getCie10Description('')).toBe('Descripción no disponible')
    expect(getCie10Description(null)).toBe('Descripción no disponible')
  })
})
