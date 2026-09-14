import { describe, it, expect } from 'vitest'
import { wrapLabel, calculateChartHeight } from './causasChartLabels'

describe('wrapLabel', () => {
  it('devuelve el texto tal cual si es corto', () => {
    expect(wrapLabel('Eclampsia')).toBe('Eclampsia')
  })

  it('envuelve texto largo en varias líneas sin truncar ni agregar "..."', () => {
    const texto =
      'O14.9 Preeclampsia no especificada con complicaciones hepáticas y renales graves durante el tercer trimestre'
    const resultado = wrapLabel(texto)
    expect(Array.isArray(resultado)).toBe(true)
    const lineas = resultado as string[]
    expect(lineas.length).toBeGreaterThan(2)
    expect(lineas.some((linea) => linea.includes('...'))).toBe(false)
    expect(lineas.join(' ')).toBe(texto)
  })
})

describe('calculateChartHeight', () => {
  it('devuelve el mínimo (320) cuando no hay etiquetas', () => {
    expect(calculateChartHeight([])).toBe(320)
  })

  it('devuelve el mínimo (320) con pocas etiquetas cortas', () => {
    expect(calculateChartHeight(['Eclampsia', 'Sepsis'])).toBe(320)
  })

  it('crece cuando las etiquetas ocupan más líneas', () => {
    const etiquetasCortas = ['Eclampsia', 'Sepsis', 'Hemorragia']
    const etiquetasLargas = [
      'O14.9 Preeclampsia no especificada con complicaciones hepáticas y renales graves durante el tercer trimestre',
      'O72.1 Hemorragia postparto inmediata secundaria a atonía uterina severa con compromiso hemodinámico',
      'O99.4 Enfermedades del sistema circulatorio que complican el embarazo, el parto y el puerperio',
    ]
    expect(calculateChartHeight(etiquetasLargas)).toBeGreaterThan(calculateChartHeight(etiquetasCortas))
  })
})
