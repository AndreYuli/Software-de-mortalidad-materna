import { describe, it, expect } from 'vitest'
import {
  getTimelineAiInsight,
  getTopCausasAiInsight,
  getEdadAiInsight,
  getEdadGestacionalAiInsight,
  getMomentoAiInsight,
  getDemorasAiInsight,
  getSankeyAiInsight,
  getHeatmapAiInsight,
  getSeveridadFallasAiInsight,
  getCriteriosInclusionAiInsight,
  getTiempoRemisionAiInsight,
  getInstitucionesAiInsight,
  getObstetricoEdadAiInsight,
  getIndicadoresSeveridadAiInsight,
  getClusteringAiInsight,
} from './aiChartInsights'

describe('aiChartInsights', () => {
  it('genera resumen de evolución temporal con porcentajes enteros y nombres de mes completos', () => {
    const labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    const series = [{ name: 'Mortalidad', data: [10, 20, 100, 40, 50, 60, 70, 80, 90, 10, 11, 12] }]
    const result = getTimelineAiInsight(labels, series)
    expect(result).toBeTruthy()
    expect(result).toContain('marzo') // Debe traducir Mar a marzo
    expect(result).not.toMatch(/\d+\.\d+%/) // No debe contener decimales en porcentajes
  })

  it('genera resumen de top causas con porcentajes enteros', () => {
    const labels = ['Preeclampsia', 'Hemorragia', 'Sepsis']
    const values = [50, 30, 20]
    const result = getTopCausasAiInsight(labels, values)
    expect(result).toContain('50%')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('genera resumen de edad con grupo mayoritario', () => {
    const labels = ['<20', '20-29', '30-39', '≥40']
    const mort = [10, 50, 30, 10]
    const morb = [20, 80, 40, 10]
    const result = getEdadAiInsight(labels, mort, morb)
    expect(result).toContain('20-29')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('genera resumen de distribucion de edad gestacional', () => {
    const data = { labels: ['<28 semanas', '28-36 semanas', '37-41 semanas', '≥42 semanas'], valores: [1, 2, 2, 1], total: 6 }
    const result = getEdadGestacionalAiInsight(data, 'Mortalidad')
    expect(result).toContain('mortalidad')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('retorna null para distribucion de edad gestacional sin datos', () => {
    expect(getEdadGestacionalAiInsight(null, 'Morbilidad')).toBeNull()
  })

  it('genera resumen de momento de ocurrencia', () => {
    const labels = ['Embarazo', 'Parto', 'Puerperio']
    const mort = [20, 10, 30]
    const morb = [40, 20, 60]
    const result = getMomentoAiInsight(labels, mort, morb)
    expect(result).toContain('Puerperio')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('genera resumen de demoras obstétricas', () => {
    const labels = ['Demora 1', 'Demora 2', 'Demora 3', 'Demora 4']
    const values = [15, 25, 10, 50]
    const result = getDemorasAiInsight(labels, values)
    expect(result).toContain('Demora 4')
    expect(result).toContain('50%')
  })

  it('genera resumen para Sankey', () => {
    const data = {
      nodos: ['[Parto] Vaginal', '[Nivel] Nivel 2', '[Muerte] Puerperio'],
      links: { source: [0, 1], target: [1, 2], value: [20, 20] },
    }
    const result = getSankeyAiInsight(data)
    expect(result).toBeTruthy()
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('genera resumen para Heatmap', () => {
    const data = {
      causas: ['O14.1', 'O72.1'],
      demoras: ['Demora 1', 'Demora 4'],
      valores: [[10, 20], [30, 40]],
    }
    const result = getHeatmapAiInsight(data)
    expect(result).toBeTruthy()
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('genera resumen para fallas orgánicas', () => {
    const data = {
      fallas: [
        { nombre: 'Falla Vascular', casos: 40, porcentaje: 40 },
        { nombre: 'Falla Renal', casos: 20, porcentaje: 20 },
      ],
      total_casos: 100,
    }
    const result = getSeveridadFallasAiInsight(data)
    expect(result).toContain('Falla Vascular')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('genera resumen para tiempo de remisión en horas enteras', () => {
    const data = { min: 1, q1: 2, median: 4.8, mean: 5.2, q3: 8, max: 24, total: 35 }
    const result = getTiempoRemisionAiInsight(data)
    expect(result).toContain('5 horas')
    expect(result).not.toMatch(/\d+\.\d+h/)
  })

  it('genera resumen para criterios de inclusión', () => {
    const data = [
      { nombre: 'Hemorragia', casos: 25, porcentaje: 50 },
      { nombre: 'Sepsis', casos: 25, porcentaje: 50 },
    ]
    const result = getCriteriosInclusionAiInsight(data)
    expect(result).toContain('Hemorragia')
    expect(result).toContain('50%')
  })

  it('genera resumen para instituciones de referencia', () => {
    const data = { instituciones: ['Hospital General'], conteos: [40], totalCasos: 100 }
    const result = getInstitucionesAiInsight(data)
    expect(result).toContain('Hospital General')
    expect(result).toContain('100%')
  })

  it('genera resumen para variables obstétricas', () => {
    const data = [
      { label: 'Controles Prenatales (CPN)', mort: { promedio: 4.2 }, morb: { promedio: 5.1 } },
      { label: 'Gestaciones previas', mort: { promedio: 2.1 }, morb: { promedio: 2.8 } },
    ]
    const result = getObstetricoEdadAiInsight(data)
    expect(result).toContain('4 controles prenatales')
    expect(result).toContain('2 gestaciones previas')
  })

  it('genera resumen para indicadores de severidad', () => {
    const severidad = [
      { nombre: 'Ingreso UCI', casos: 30 },
      { nombre: 'Cirugía Adicional', casos: 10 },
      { nombre: 'Transfusión', casos: 20 },
    ]
    const result = getIndicadoresSeveridadAiInsight(severidad, 100)
    expect(result).toContain('30%')
    expect(result).toContain('UCI')
  })

  it('genera resumen para modelo de clustering PCA', () => {
    const data = {
      n_clusters: 3,
      n_samples: 100,
      cluster_sizes: [60, 30, 10],
      features_used: ['edad', 'controles_prenatales'],
    }
    const result = getClusteringAiInsight(data)
    expect(result).toContain('3 conglomerados')
    expect(result).toContain('Cluster 1')
    expect(result).toContain('60%')
  })
})
