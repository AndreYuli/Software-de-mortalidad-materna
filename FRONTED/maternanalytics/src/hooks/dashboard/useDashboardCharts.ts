import { useCallback, useMemo } from 'react'
import type { AnalisisCompleto } from '../../types'
import { getCie10Description, getClusterColor } from '../../constants/dashboardConstants'
import type { ClusteringResult } from './useAnalysisHomeData'
import type { Segmento } from './useDashboardMetrics'

export type ClusteringPoint2D = { x: number; y: number; color: string; label: string }
export type ClusteringPoint3D = { x: number; y: number; z: number; color: string; label: string }
export type ClusteringChartData =
  | { dim: '2d'; points: ClusteringPoint2D[] }
  | { dim: '3d'; points: ClusteringPoint3D[] }

export interface UseDashboardChartsParams {
  segmento: Segmento
  mortalidadData: AnalisisCompleto | null
  morbilidadData: AnalisisCompleto | null
  filterYear: string
  pcaDim: '2d' | '3d'
  clusteringSegment: 'mortalidad' | 'morbilidad'
  mortalidadClustering: ClusteringResult | null
  morbilidadClustering: ClusteringResult | null
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
 * Arma los datasets que consumen Chart.js/ECharts (evolución temporal, top
 * causas y clustering). Única responsabilidad: transformar los datos del
 * análisis en estructuras de gráfica, sin fetch ni cálculo de KPIs.
 */
export function useDashboardCharts({
  segmento,
  mortalidadData,
  morbilidadData,
  filterYear,
  pcaDim,
  clusteringSegment,
  mortalidadClustering,
  morbilidadClustering,
}: UseDashboardChartsParams) {
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

  const activeClusterData = useMemo(
    () => (clusteringSegment === 'mortalidad' ? mortalidadClustering : morbilidadClustering),
    [clusteringSegment, mortalidadClustering, morbilidadClustering],
  )

  const clusterMarkerColors = useMemo(
    () => activeClusterData?.clusters?.map((clusterId) => getClusterColor(clusterId)) || [],
    [activeClusterData?.clusters],
  )

  const clusteringChartData = useMemo((): ClusteringChartData | null => {
    if (!activeClusterData) return null

    if (pcaDim === '3d' && activeClusterData.pca_3d) {
      const { x, y, z } = activeClusterData.pca_3d
      return {
        dim: '3d',
        points: x.map((xi, i) => ({
          x: xi,
          y: y[i],
          z: z[i],
          color: clusterMarkerColors[i] ?? '#95a5a6',
          label: `Caso ${i + 1} · Cluster ${activeClusterData.clusters![i]}`,
        })),
      }
    }

    if (activeClusterData.pca_2d) {
      const { x, y } = activeClusterData.pca_2d
      return {
        dim: '2d',
        points: x.map((xi, i) => ({
          x: xi,
          y: y[i],
          color: clusterMarkerColors[i] ?? '#95a5a6',
          label: `Caso ${i + 1} · Cluster ${activeClusterData.clusters![i]}`,
        })),
      }
    }

    return null
  }, [activeClusterData, pcaDim, clusterMarkerColors])

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

  const momentoChartData = useMemo(() => {
    const labels = new Set<string>()
    const mortDist = (mortalidadData as any)?.momento_muerte?.distribucion || {}
    const morbDist = (morbilidadData as any)?.momento_ocurrencia?.distribucion || {}

    Object.keys(mortDist).forEach((k) => labels.add(k))
    Object.keys(morbDist).forEach((k) => labels.add(k))
    
    const sortedLabels = Array.from(labels).sort()
    return {
      labels: sortedLabels,
      mortalidadValues: sortedLabels.map((l) => mortDist[l] || 0),
      morbilidadValues: sortedLabels.map((l) => morbDist[l] || 0),
    }
  }, [mortalidadData, morbilidadData])

  const heatmapDemorasData = useMemo(() => {
    return (mortalidadData as any)?.heatmap_demoras
  }, [mortalidadData])

  const sankeyFlujoData = useMemo(() => {
    return (mortalidadData as any)?.sankey_flujo
  }, [mortalidadData])

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

  const criteriosInclusionData = useMemo(() => {
    if (!morbilidadData?.criterios_inclusion) return null
    const items = Object.values(morbilidadData.criterios_inclusion).map((c: any) => ({
      nombre: c.nombre,
      casos: c.casos,
      porcentaje: c.porcentaje,
    }))
    return items.sort((a, b) => b.casos - a.casos)
  }, [morbilidadData])

  const momentoOcurrenciaData = useMemo(() => {
    const dist = (morbilidadData as any)?.momento_ocurrencia?.distribucion
    if (!dist || Object.keys(dist).length === 0) return null
    return Object.entries(dist).map(([label, count]) => ({
      label,
      count: count as number,
    }))
  }, [morbilidadData])

  const tiempoRemisionData = useMemo(() => {
    const data = (morbilidadData as any)?.tiempo_remision
    if (!data || !data.valores || data.valores.length === 0) return null
    return {
      valores: data.valores as number[],
      min: data.min as number,
      q1: data.q1 as number,
      median: data.median as number,
      mean: data.mean as number,
      q3: data.q3 as number,
      max: data.max as number,
      total: data.total as number,
    }
  }, [morbilidadData])

  /* ── Atención & Oportunidad tab data ── */

  const atencionKpis = useMemo(() => {
    const mortStats = (mortalidadData as any)?.estadisticas_basicas
    const morbStats = (morbilidadData as any)?.estadisticas_basicas
    if (!mortStats && !morbStats) return null

    const cpnMort = mortStats?.controles_prenatales_promedio ?? null
    const gestMort = mortStats?.gestaciones_promedio ?? null

    // Prenatal controls: mortalidad has explicit column '8.1 No. CPN'
    // Morbilidad has 'N° controles prenatales' but it's exposed differently
    const estanciaMorb = morbStats?.estancia_hospitalaria_promedio ?? null
    const estanciaUciMorb = morbStats?.estancia_uci_promedio ?? null

    return {
      cpnPromedio: cpnMort != null ? Math.round(cpnMort) : null,
      gestacionesPromedio: gestMort != null ? Math.round(gestMort) : null,
      estanciaHospitalaria: estanciaMorb != null ? Math.round(estanciaMorb) : null,
      estanciaUci: estanciaUciMorb != null ? Math.round(estanciaUciMorb) : null,
      totalMort: mortStats?.total_casos ?? 0,
      totalMorb: morbStats?.total_casos ?? 0,
    }
  }, [mortalidadData, morbilidadData])

  const institucionReferenciaData = useMemo(() => {
    const data = (morbilidadData as any)?.institucion_referencia
    if (!data || !data.instituciones || data.instituciones.length === 0) return null
    return {
      instituciones: data.instituciones as string[],
      conteos: data.conteos as number[],
      con_uci: data.con_uci as number[],
      con_cirugia: data.con_cirugia as number[],
      totalConDato: data.total_con_dato as number,
      totalCasos: data.total_casos as number,
    }
  }, [morbilidadData])

  const obstetricoEdadData = useMemo(() => {
    // Extract prenatal/obstetric data by age from both datasets
    const extractVar = (data: any, colKey: string) => {
      const obj = data?.obstetrico_edad?.[colKey]
      if (!obj) return null
      return {
        nombre: obj.nombre as string,
        valoresEje: obj.valores_eje as number[],
        conteos: obj.conteos_total as number[],
        porEdad: obj.por_edad as Record<string, number[]>,
        promedio: obj.promedio as number,
        total: obj.total as number,
      }
    }

    // Mortalidad uses '6.5 Gestaciones', '8.1 No. CPN' etc.
    // Morbilidad uses 'N° gestaciones', 'N° controles prenatales' etc.
    const mortGest = extractVar(mortalidadData, '6.5 Gestaciones')
    const morbGest = extractVar(morbilidadData, 'N° gestaciones')
    const mortCesareas = extractVar(mortalidadData, '6.7 Cesáreas')
    const morbCesareas = extractVar(morbilidadData, 'Cesáreas')
    const mortPartos = extractVar(mortalidadData, '6.6 Partos Vaginales')
    const morbPartos = extractVar(morbilidadData, 'Partos vaginales')

    const variables: { label: string; mort: any; morb: any }[] = [
      { label: 'Gestaciones', mort: mortGest, morb: morbGest },
      { label: 'Partos Vaginales', mort: mortPartos, morb: morbPartos },
      { label: 'Cesáreas', mort: mortCesareas, morb: morbCesareas },
    ]

    const available = variables.filter(v => v.mort || v.morb)
    return available.length > 0 ? available : null
  }, [mortalidadData, morbilidadData])

  return { lineChartData, topCausasMortalidad, topCausasMorbilidad, activeClusterData, clusteringChartData, demorasChartData, edadChartData, edadGestacionalMortalidad, edadGestacionalMorbilidad, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData }
}

