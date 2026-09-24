import { describe, expect, it } from 'vitest'
import { describeMatrix, describeSeries } from './chartA11y'

describe('describeSeries', () => {
  it('lista cada categoría con su valor detrás del título', () => {
    expect(describeSeries('Zona de Residencia', ['Urbana', 'Rural'], [12, 5])).toBe(
      'Zona de Residencia. Urbana: 12; Rural: 5',
    )
  })

  it('con listas vacías devuelve solo el título', () => {
    expect(describeSeries('Etnia', [], [])).toBe('Etnia')
  })

  it('usa 0 cuando falta el valor de una categoría', () => {
    expect(describeSeries('Etnia', ['A', 'B'], [3])).toBe('Etnia. A: 3; B: 0')
  })
})

describe('describeMatrix', () => {
  it('describe cada fila con el valor de cada columna', () => {
    expect(
      describeMatrix('Cruce', ['Urbana', 'Rural'], ['0', '1'], [
        [3, 1],
        [2, 4],
      ]),
    ).toBe('Cruce. Urbana (0: 3, 1: 1); Rural (0: 2, 1: 4)')
  })

  it('sin filas devuelve solo el título', () => {
    expect(describeMatrix('Cruce', [], [], [])).toBe('Cruce')
  })
})
