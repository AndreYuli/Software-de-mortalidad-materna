import { describe, expect, it } from 'vitest'
import { getCruceLabels } from './cruceLabels'

describe('getCruceLabels', () => {
  it('nombra las variables seleccionadas en título, ejes y leyenda', () => {
    expect(getCruceLabels('Etnia', 'N° de gestaciones')).toEqual({
      title: 'Etnia según N° de gestaciones',
      xAxis: 'Casos — Etnia',
      yAxis: 'Etnia',
      legend: 'N° de gestaciones',
    })
  })

  it('cambia al cambiar las variables (sin etiquetas genéricas)', () => {
    const a = getCruceLabels('Zona de residencia', 'Cesáreas')
    const b = getCruceLabels('Tipo de afiliación', 'Partos vaginales')
    expect(a).not.toEqual(b)
    for (const l of [a, b]) {
      expect(l.xAxis).not.toBe('Casos')
      expect(l.xAxis.startsWith('Casos — ')).toBe(true)
      expect(l.yAxis).not.toBe('')
    }
  })
})
