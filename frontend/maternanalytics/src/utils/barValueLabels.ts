import type { Plugin } from 'chart.js'
import { CHART_FONT_FAMILY, CHART_TEXT_COLOR } from '../constants/chartTheme'
import { formatoNumero } from './indicadoresMaternos'

/** Plugin de Chart.js que escribe `n (p %)` a la derecha de cada barra horizontal (solo `n` sin total). */
export function barValueLabelsPlugin(total: number): Plugin<'bar'> {
  return {
    id: 'barValueLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart
      const barras = chart.getDatasetMeta(0).data
      const valores = chart.data.datasets[0]?.data as number[] | undefined
      if (!valores) return
      ctx.save()
      ctx.font = `600 11px ${CHART_FONT_FAMILY}`
      ctx.fillStyle = CHART_TEXT_COLOR
      ctx.textBaseline = 'middle'
      ctx.textAlign = 'left'
      barras.forEach((barra, i) => {
        const valor = valores[i]
        const texto =
          total > 0 ? `${formatoNumero(valor)} (${formatoNumero((valor / total) * 100, 1)} %)` : formatoNumero(valor)
        ctx.fillText(texto, barra.x + 6, barra.y)
      })
      ctx.restore()
    },
  }
}
