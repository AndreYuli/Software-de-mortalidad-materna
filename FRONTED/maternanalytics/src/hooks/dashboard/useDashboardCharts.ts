import { useCallback, useMemo } from 'react'
import type { AnalisisCompleto } from '../../types'
import { getCie10Description } from '../../constants/dashboardConstants'
import type { Segmento } from './useDashboardMetrics'

export interface UseDashboardChartsParams {
  segmento: Segmento
  mortalidadData: AnalisisCompleto | null
  morbilidadData: AnalisisCompleto | null
  filterYear: string
}

const MONTHS_LABEL = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

function getMonthlyData(dist: Record<string, Record<string, number>> | undefined, targetYear: string): number[] {
  const months = Array.from({ length: 12 }, (_, i) => String(i + 1))
  const data = months.map(() => 0)
  if (!dist) return data

  if (targetYear) {
    const yearData = dist[String(targetYear)]
    if (yearData) {
      months.forEach((m, idx) => {
        data[idx] = yearData[m] || 0
      })
    }
  } else {
    Object.values(dist).forEach((yearData) => {
      months.forEach((m, idx) => {
        data[idx] += yearData[m] || 0
      })
    })
  }
  return data
}

/**
 * Arma los datasets que consumen Chart.js (top causas, edad gestacional) y
 * los que alimenta el export de reporte (evolución mensual, demoras, edad
 * materna, fallas orgánicas). Única responsabilidad: transformar los datos
 * del análisis en estructuras de gráfica/export, sin fetch ni KPIs de UI.
 */
export function useDashboardCharts({ segmento, mortalidadData, morbilidadData, filterYear }: UseDashboardChartsParams) {
  const getMonthly = useCallback(
    (dist: Record<string, Record<string, number>> | undefined) => getMonthlyData(dist, filterYear),
    [filterYear],
  )

  const lineChartData = useMemo(() => {
    const series: { name: string; color: string; data: number[] }[] = []

    if ((segmento === 'ambos' || segmento === 'mortalidad') && mortalidadData?.distribucion_mensual) {
      series.push({
        name: 'Mortalidad',
        color: '#c0392b',
        data: getMonthly(mortalidadData.distribucion_mensual),
      })
    }

    if ((segmento === 'ambos' || segmento === 'morbilidad') && morbilidadData?.distribucion_mensual) {
      series.push({
        name: 'Morbilidad',
        color: '#2ca02c',
        data: getMonthly(morbilidadData.distribucion_mensual),
      })
    }

    return { labels: MONTHS_LABEL, series }
  }, [segmento, mortalidadData, morbilidadData, getMonthly])

  const topCausasMortalidad = useMemo(() => {
    if (!(segmento === 'ambos' || segmento === 'mortalidad')) {
      return { labels: [], values: [], colors: [] }
    }
    const causas = mortalidadData?.causas_cie10?.top_causas ?? []
    const sorted = [...causas].sort((a, b) => b.casos - a.casos).slice(0, 10).reverse()
    return {
      labels: sorted.map((c) => getCie10Description(c.codigo)),
      values: sorted.map((c) => c.casos),
      colors: sorted.map(() => '#c0392b'),
    }
  }, [segmento, mortalidadData])

  const topCausasMorbilidad = useMemo(() => {
    if (!(segmento === 'ambos' || segmento === 'morbilidad')) {
      return { labels: [], values: [], colors: [] }
    }
    const causas = morbilidadData?.causas_cie10?.top_causas ?? []
    const sorted = [...causas].sort((a, b) => b.casos - a.casos).slice(0, 10).reverse()
    return {
      labels: sorted.map((c) => getCie10Description(c.codigo)),
      values: sorted.map((c) => c.casos),
      colors: sorted.map(() => '#2ca02c'),
    }
  }, [segmento, morbilidadData])

  const demorasChartData = useMemo(() => {
    const list: { label: string; casos: number }[] = []
    if (mortalidadData?.demoras) {
      Object.values(mortalidadData.demoras).forEach((d) => {
        list.push({ label: d.nombre, casos: d.casos_con_demora })
      })
    }
    return {
      labels: list.map((i) => i.label),
      values: list.map((i) => i.casos),
    }
  }, [mortalidadData])

  const edadChartData = useMemo(() => {
    const labels = new Set<string>()

    const extractAgeGroups = (data: any) => {
      if (!data?.obstetrico_edad) return {}
      const gestKey = Object.keys(data.obstetrico_edad).find((k) => k.toLowerCase().includes('estaciones'))
      const obj = gestKey ? data.obstetrico_edad[gestKey]?.por_edad : null
      if (!obj) return {}
      const res: Record<string, number> = {}
      for (const [ageGroup, counts] of Object.entries(obj)) {
        res[ageGroup] = (counts as number[]).reduce((a, b) => a + b, 0)
      }
      return res
    }

    const mortAge = extractAgeGroups(mortalidadData)
    const morbAge = extractAgeGroups(morbilidadData)

    Object.keys(mortAge).forEach((k) => labels.add(k))
    Object.keys(morbAge).forEach((k) => labels.add(k))

    const sortedLabels = Array.from(labels)
    const order = ["<20", "20-29", "30-39", "≥40"]
    sortedLabels.sort((a, b) => {
      const idxA = order.indexOf(a)
      const idxB = order.indexOf(b)
      return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB)
    })

    return {
      labels: sortedLabels,
      mortalidadValues: sortedLabels.map((l) => mortAge[l] || 0),
      morbilidadValues: sortedLabels.map((l) => morbAge[l] || 0),
    }
  }, [mortalidadData, morbilidadData])

  const edadGestacionalMortalidad = useMemo(() => {
    return mortalidadData?.distribucion_edad_gestacional ?? null
  }, [mortalidadData])

  const edadGestacionalMorbilidad = useMemo(() => {
    return morbilidadData?.distribucion_edad_gestacional ?? null
  }, [morbilidadData])

  const edadRiesgoMortalidad = useMemo(() => {
    return mortalidadData?.distribucion_edad_riesgo ?? null
  }, [mortalidadData])

  const edadRiesgoMorbilidad = useMemo(() => {
    return morbilidadData?.distribucion_edad_riesgo ?? null
  }, [morbilidadData])

  const severidadFallasData = useMemo(() => {
    return (morbilidadData as any)?.severidad_fallas
  }, [morbilidadData])

  const morbKpis = useMemo(() => {
    if (!morbilidadData) return null
    const stats = (morbilidadData as any)?.estadisticas_basicas
    if (!stats) return null
    return {
      totalCasos: stats.total_casos ?? 0,
      edadPromedio: stats.edad_promedio != null ? Math.round(stats.edad_promedio) : null,
      estanciaHospitalaria: stats.estancia_hospitalaria_promedio != null ? Math.round(stats.estancia_hospitalaria_promedio) : null,
      estanciaUci: stats.estancia_uci_promedio != null ? Math.round(stats.estancia_uci_promedio) : null,
      criteriosPromedio: stats.criterios_promedio != null ? Math.round(stats.criterios_promedio) : null,
    }
  }, [morbilidadData])

  return {
    lineChartData,
    topCausasMortalidad,
    topCausasMorbilidad,
    demorasChartData,
    edadChartData,
    edadGestacionalMortalidad,
    edadGestacionalMorbilidad,
    edadRiesgoMortalidad,
    edadRiesgoMorbilidad,
    severidadFallasData,
    morbKpis,
  }
}
