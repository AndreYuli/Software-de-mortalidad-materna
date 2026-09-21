import { describe, expect, it, vi } from 'vitest'
import type { Chart } from 'chart.js'
import { barValueLabelsPlugin } from './barValueLabels'

function graficaFalsa(valores: number[]) {
  const fillText = vi.fn()
  const chart = {
    ctx: { save: vi.fn(), restore: vi.fn(), fillText },
    getDatasetMeta: () => ({ data: valores.map((_, i) => ({ x: 100 + i * 10, y: 20 + i * 30 })) }),
    data: { datasets: [{ data: valores }] },
  }
  return { chart: chart as unknown as Chart<'bar'>, fillText }
}

function dibujar(chart: Chart<'bar'>, total: number) {
  const hook = barValueLabelsPlugin(total).afterDatasetsDraw as unknown as (c: Chart<'bar'>) => void
  hook(chart)
}

describe('barValueLabelsPlugin', () => {
  it('dibuja "n (p %)" a la derecha de cada barra cuando hay total', () => {
    const { chart, fillText } = graficaFalsa([50, 30])
    dibujar(chart, 200)
    expect(fillText).toHaveBeenNthCalledWith(1, '50 (25,0 %)', 106, 20)
    expect(fillText).toHaveBeenNthCalledWith(2, '30 (15,0 %)', 116, 50)
  })

  it('sin total dibuja solo el número', () => {
    const { chart, fillText } = graficaFalsa([1200])
    dibujar(chart, 0)
    expect(fillText).toHaveBeenCalledWith('1.200', 106, 20)
  })

  it('guarda y restaura el estado del canvas', () => {
    const { chart } = graficaFalsa([5])
    dibujar(chart, 10)
    expect(chart.ctx.save).toHaveBeenCalledTimes(1)
    expect(chart.ctx.restore).toHaveBeenCalledTimes(1)
  })
})
