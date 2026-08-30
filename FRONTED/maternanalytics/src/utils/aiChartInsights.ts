/**
 * Utilidad de generación de resúmenes inteligentes (IA) para cada gráfico del dashboard.
 * Todos los porcentajes y conteos se formatean estrictamente como enteros (sin floats).
 */

/** Helper para redondear porcentajes a enteros de forma segura */
function pct(value: number, total: number): number {
  if (!total || total === 0) return 0
  return Math.round((value / total) * 100)
}

/** Helper para formatear números enteros */
function intVal(val: number | null | undefined): number {
  if (val == null || isNaN(val)) return 0
  return Math.round(val)
}

/** Helper para eliminar códigos numéricos de ficha confusos (ej: "6.5 Gestaciones", "8.1 No. CPN") */
export function cleanClinicalLabel(label: string): string {
  if (!label) return ''
  return label
    .replace(/^\[.*?\]\s*/, '')
    .replace(/^\d+(\.\d+)+\s*/, '')
    .replace(/^N°\s*/i, '')
    .replace(/^No\.\s*/i, '')
    .replace(/^Nro\.\s*/i, '')
    .trim()
}

const MONTH_NAMES_FULL: Record<string, string> = {
  ene: 'enero',
  feb: 'febrero',
  mar: 'marzo',
  abr: 'abril',
  may: 'mayo',
  jun: 'junio',
  jul: 'julio',
  ago: 'agosto',
  sep: 'septiembre',
  oct: 'octubre',
  nov: 'noviembre',
  dic: 'diciembre',
}

function getFullMonthName(shortName: string): string {
  const clean = shortName.toLowerCase().trim()
  return MONTH_NAMES_FULL[clean] || shortName
}

// 1. Evolución Temporal
export function getTimelineAiInsight(
  labels: string[],
  series: { name: string; data: number[] }[],
): string | null {
  if (!series || series.length === 0) return null

  const totalsBySeries = series.map((s) => ({
    name: s.name,
    total: s.data.reduce((a, b) => a + b, 0),
    data: s.data,
  }))

  const globalTotal = totalsBySeries.reduce((a, b) => a + b.total, 0)
  if (globalTotal === 0) return 'Sin registros suficientes en el periodo seleccionado para generar el análisis.'

  // Mes pico sumando todas las series
  const monthlySums = labels.map((_, idx) =>
    series.reduce((sum, s) => sum + (s.data[idx] || 0), 0),
  )
  const maxMonthVal = Math.max(...monthlySums)
  const maxMonthIdx = monthlySums.indexOf(maxMonthVal)
  const rawPeakMonth = labels[maxMonthIdx] || 'mes pico'
  const peakMonth = getFullMonthName(rawPeakMonth)
  const peakPct = pct(maxMonthVal, globalTotal)

  // Comparativa de semestre (primeros 6 meses vs últimos 6)
  const sem1 = monthlySums.slice(0, 6).reduce((a, b) => a + b, 0)
  const sem2 = monthlySums.slice(6).reduce((a, b) => a + b, 0)
  const sem1Pct = pct(sem1, globalTotal)
  const sem2Pct = pct(sem2, globalTotal)

  const semDesc =
    sem1Pct > sem2Pct
      ? `El primer semestre concentró el ${sem1Pct}% de la carga de casos.`
      : `El segundo semestre concentró la mayor proporción con el ${sem2Pct}% de los casos.`

  if (totalsBySeries.length === 2) {
    const mort = totalsBySeries.find((s) => s.name.toLowerCase().includes('mortalidad'))
    const morb = totalsBySeries.find((s) => s.name.toLowerCase().includes('morbilidad'))
    return `Se consolidaron ${intVal(mort?.total)} defunciones y ${intVal(morb?.total)} eventos de morbilidad extrema (${globalTotal} casos en total). El pico máximo ocurrió en ${peakMonth} con ${maxMonthVal} casos (${peakPct}% del total anual). ${semDesc}`
  }

  return `Se registraron un total de ${globalTotal} casos distribuidos en el año. La mayor incidencia se concentró en ${peakMonth} con ${maxMonthVal} casos (${peakPct}% del periodo). ${semDesc}`
}

// 2. Top Causas / Criterios
export function getTopCausasAiInsight(
  labels: string[],
  values: number[],
  isMorbilidad: boolean = false,
): string | null {
  if (!values || values.length === 0 || !labels || labels.length === 0) return null

  const total = values.reduce((a, b) => a + b, 0)
  if (total === 0) return 'Sin casos registrados en las causas principales.'

  const topName = labels[0] || 'Causa principal'
  const topVal = values[0] || 0
  const topPct = pct(topVal, total)

  const top3Val = values.slice(0, 3).reduce((a, b) => a + b, 0)
  const top3Pct = pct(top3Val, total)

  const concepto = isMorbilidad ? 'criterio de morbilidad' : 'causa de mortalidad'

  return `El principal ${concepto} identificado es "${topName}", acumulando ${topVal} casos (${topPct}% del grupo evaluado). Las 3 primeras categorías concentran de forma combinada el ${top3Pct}% de todos los eventos (${top3Val} casos).`
}

// 3. Distribución por Edad
export function getEdadAiInsight(
  labels: string[],
  mortValues: number[],
  morbValues: number[],
): string | null {
  if (!labels || labels.length === 0) return null

  const totalMort = mortValues.reduce((a, b) => a + b, 0)
  const totalMorb = morbValues.reduce((a, b) => a + b, 0)
  const total = totalMort + totalMorb
  if (total === 0) return null

  const combined = labels.map((_, i) => (mortValues[i] || 0) + (morbValues[i] || 0))
  const maxVal = Math.max(...combined)
  const maxIdx = combined.indexOf(maxVal)
  const topGroup = labels[maxIdx] || 'grupo de edad'
  const topPct = pct(maxVal, total)

  return `El rango etario con mayor frecuencia de eventos es ${topGroup} años, concentrando el ${topPct}% de los casos (${maxVal} pacientes). Este grupo representa el foco prioritario para estrategias de prevención preconcepcional y tamizaje temprano.`
}

// 3b. Distribución de Edad Gestacional
export function getEdadGestacionalAiInsight(
  data: { labels: string[]; valores: number[]; total: number } | null,
  evento: 'Morbilidad' | 'Mortalidad',
): string | null {
  if (!data || data.total === 0) return null

  const casosATermino = data.valores[2] || 0
  const casosFueraDeTermino = data.total - casosATermino
  const riesgoPct = pct(casosFueraDeTermino, data.total)

  return `El ${riesgoPct}% de los casos de ${evento.toLowerCase()} (${casosFueraDeTermino} de ${data.total} pacientes) tuvieron una gestación fuera del rango a término (37-41 semanas): parto pretérmino (antes de la semana 37) o postérmino (semana 42 en adelante).`
}

// 4. Momento de Muerte / Ocurrencia
export function getMomentoAiInsight(
  labels: string[],
  mortValues: number[],
  morbValues: number[],
): string | null {
  if (!labels || labels.length === 0) return null

  const combined = labels.map((_, i) => (mortValues[i] || 0) + (morbValues[i] || 0))
  const total = combined.reduce((a, b) => a + b, 0)
  if (total === 0) return null

  const maxVal = Math.max(...combined)
  const maxIdx = combined.indexOf(maxVal)
  const topMomento = labels[maxIdx] || 'etapa'
  const topPct = pct(maxVal, total)

  return `La etapa de mayor criticidad es "${topMomento}", donde se concentró el ${topPct}% de los eventos adversos (${maxVal} casos). Se destaca la necesidad de vigilancia intensiva durante este periodo clínico.`
}

// 5. Modelo de las 4 Demoras
export function getDemorasAiInsight(
  labels: string[],
  values: number[],
): string | null {
  if (!values || values.length === 0) return null

  const total = values.reduce((a, b) => a + b, 0)
  if (total === 0) return 'No se registraron demoras obstétricas en los casos seleccionados.'

  const maxVal = Math.max(...values)
  const maxIdx = values.indexOf(maxVal)
  const topDemora = labels[maxIdx] || 'Demora principal'
  const topPct = pct(maxVal, total)

  return `La barrera obstétrica más recurrente fue "${topDemora}" con ${maxVal} ocurrencias (${topPct}% del total de demoras identificadas), señalando el eslabón crítico a intervenir en la ruta de atención materna.`
}

// 6. Sankey Flujo de Atención
export function getSankeyAiInsight(data?: {
  nodos: string[]
  links: { source: number[]; target: number[]; value: number[] }
}): string | null {
  if (!data || !data.nodos || !data.links || data.links.value.length === 0) return null

  const totalFlow = data.links.value.reduce((a, b) => a + b, 0)
  if (totalFlow === 0) return null

  // Identificar el enlace con mayor volumen global
  const maxVal = Math.max(...data.links.value)
  const maxIdx = data.links.value.indexOf(maxVal)
  const sourceName = data.nodos[data.links.source[maxIdx]]?.replace(/^\[.*?\]\s*/, '') || ''
  const targetName = data.nodos[data.links.target[maxIdx]]?.replace(/^\[.*?\]\s*/, '') || ''
  const linkPct = pct(maxVal, totalFlow / 2) // flujo dividido en 2 etapas

  const isDesconocido =
    sourceName.toLowerCase().includes('desconocido') ||
    targetName.toLowerCase().includes('desconocido') ||
    sourceName.toLowerCase().includes('ignorado') ||
    targetName.toLowerCase().includes('ignorado')

  if (isDesconocido) {
    // Buscar la ruta conocida con mayor frecuencia
    let bestKnownVal = 0
    let bestKnownSource = ''
    let bestKnownTarget = ''

    data.links.value.forEach((val, idx) => {
      const s = data.nodos[data.links.source[idx]]?.replace(/^\[.*?\]\s*/, '') || ''
      const t = data.nodos[data.links.target[idx]]?.replace(/^\[.*?\]\s*/, '') || ''
      const sUnknown = s.toLowerCase().includes('desconocido') || s.toLowerCase().includes('ignorado')
      const tUnknown = t.toLowerCase().includes('desconocido') || t.toLowerCase().includes('ignorado')

      if (!sUnknown && !tUnknown && val > bestKnownVal) {
        bestKnownVal = val
        bestKnownSource = s
        bestKnownTarget = t
      }
    })

    if (bestKnownVal > 0) {
      const knownPct = pct(bestKnownVal, totalFlow / 2)
      return `Se evidencia una alta proporción de subregistro en la ficha: ${maxVal} casos (${linkPct}% de las transiciones) no tienen documentado el tipo de parto o nivel. Entre las rutas caracterizadas con dato completo, la principal conecta "${bestKnownSource}" con "${bestKnownTarget}" (${bestKnownVal} casos, ${knownPct}%). Se sugiere fortalecer la calidad del registro en las IPS notificadoras.`
    }

    return `Se evidencia una alta proporción de subregistro en la ficha: ${maxVal} casos (${linkPct}% de las transiciones) no cuentan con el tipo de parto o nivel de atención especificado. Se requiere auditoría de calidad sobre el diligenciamiento de la notificación epidemiológica.`
  }

  return `La trayectoria asistencial más transitada conecta "${sourceName}" con "${targetName}" (${maxVal} casos, representando el ${linkPct}% de las transiciones). Este patrón define la ruta clínica predominante en la red de atención.`
}

// 7. Heatmap Causas vs Demoras
export function getHeatmapAiInsight(data?: {
  causas: string[]
  demoras: string[]
  valores: number[][]
}): string | null {
  if (!data || !data.causas || !data.valores || data.valores.length === 0) return null

  let maxVal = -1
  let maxCausaIdx = 0
  let maxDemoraIdx = 0
  let totalCasosDemoras = 0

  data.demoras.forEach((_, yIdx) => {
    data.valores[yIdx]?.forEach((val, xIdx) => {
      totalCasosDemoras += val
      if (val > maxVal) {
        maxVal = val
        maxCausaIdx = xIdx
        maxDemoraIdx = yIdx
      }
    })
  })

  if (maxVal <= 0) return null

  const causaName = data.causas[maxCausaIdx]
  const demoraName = data.demoras[maxDemoraIdx]
  const impactPct = pct(maxVal, totalCasosDemoras)

  return `El cruce con mayor concentración de riesgo corresponde a la causa CIE-10 ${causaName} combinada con "${demoraName}", registrando ${maxVal} casos (${impactPct}% de las demoras acumuladas en el top de causas).`
}

// 8. Severidad y Fallas Orgánicas (Morbilidad)
export function getSeveridadFallasAiInsight(data?: {
  fallas: { nombre: string; casos: number; porcentaje?: number }[]
  total_con_falla?: number
  total_casos?: number
}): string | null {
  if (!data || !data.fallas || data.fallas.length === 0) return null

  const topFalla = data.fallas[0]
  if (!topFalla || topFalla.casos === 0) return null

  const totalFallas = data.fallas.reduce((a, b) => a + b.casos, 0)
  const topPct = pct(topFalla.casos, totalFallas)

  return `La disfunción orgánica predominante fue "${topFalla.nombre}" con ${topFalla.casos} casos (${topPct}% de las fallas documentadas). La presencia de fallo multiorgánico incrementa sustancialmente el requerimiento de UCI y soporte intensivo.`
}

// 9. Criterios de Inclusión (Morbilidad)
export function getCriteriosInclusionAiInsight(
  data?: { nombre: string; casos: number; porcentaje: number }[],
): string | null {
  if (!data || data.length === 0) return null

  const top = data[0]
  if (!top) return null

  const total = data.reduce((a, b) => a + b.casos, 0)
  const topPct = pct(top.casos, total)

  return `El criterio de inclusión más frecuente fue "${top.nombre}" (${top.casos} casos, ${topPct}% del total de criterios clínicos registrados en las pacientes con morbilidad extrema).`
}

// 10. Tiempo de Remisión (Morbilidad)
export function getTiempoRemisionAiInsight(data?: {
  median: number
  mean: number
  total: number
  q1: number
  q3: number
}): string | null {
  if (!data || !data.total || data.total === 0) return null

  const medHoras = intVal(data.median)
  const promHoras = intVal(data.mean)

  return `Se evaluaron ${data.total} traslados obstétricos con un tiempo mediano de remisión de ${medHoras} horas (promedio de ${promHoras} horas). Mantener el tiempo de traslado por debajo de este umbral es crítico para la supervivencia materna.`
}

// 11. Instituciones de Referencia
export function getInstitucionesAiInsight(data?: {
  instituciones: string[]
  conteos: number[]
  totalCasos: number
}): string | null {
  if (!data || !data.instituciones || data.instituciones.length === 0) return null

  const total = data.conteos.reduce((a, b) => a + b, 0)
  if (total === 0) return null

  const topInst = data.instituciones[0]
  const topVal = data.conteos[0] || 0
  const topPct = pct(topVal, total)

  return `La entidad hospitalaria con mayor recepción de remisiones fue "${topInst}" con ${topVal} pacientes recibidas (${topPct}% de la red de referencia analizada).`
}

// 12. Variables Obstétricas por Edad
export function getObstetricoEdadAiInsight(
  variables: { label: string; mort: { promedio: number } | null; morb: { promedio: number } | null }[],
): string | null {
  if (!variables || variables.length === 0) return null

  const cpnVar = variables.find((v) => v.label.toLowerCase().includes('control') || v.label.toLowerCase().includes('cpn'))
  const gestVar = variables.find((v) => v.label.toLowerCase().includes('gestaci'))

  const cpnProm = cpnVar?.mort?.promedio ?? cpnVar?.morb?.promedio ?? null
  const gestProm = gestVar?.mort?.promedio ?? gestVar?.morb?.promedio ?? null

  const cpnTxt = cpnProm != null ? `un promedio de ${intVal(cpnProm)} controles prenatales` : ''
  const gestTxt = gestProm != null ? `un promedio de ${intVal(gestProm)} gestaciones previas` : ''

  if (cpnTxt && gestTxt) {
    return `La población evaluada presentó ${cpnTxt} y ${gestTxt}. La captación precoz al control prenatal es el determinante más efectivo para reducir complicaciones tardías.`
  }

  return 'La correlación entre edad y paridad confirma mayor severidad en los extremos de la vida reproductiva (gestantes adolescentes y añosas).'
}

// 13. Indicadores de Severidad (Intervenciones MME)
export function getIndicadoresSeveridadAiInsight(
  severidad?: { nombre: string; casos: number }[],
  totalCasos?: number,
): string | null {
  if (!severidad || severidad.length === 0) return null

  const total = totalCasos && totalCasos > 0 ? totalCasos : severidad.reduce((a, b) => a + b.casos, 0)
  if (total === 0) return null

  const uci = severidad.find((s) => s.nombre.toLowerCase().includes('uci'))
  const cirugia = severidad.find((s) => s.nombre.toLowerCase().includes('cirug'))
  const transf = severidad.find((s) => s.nombre.toLowerCase().includes('transf'))

  const highlights: string[] = []
  if (uci && uci.casos > 0) highlights.push(`el ${pct(uci.casos, total)}% requirió ingreso a UCI (${uci.casos} casos)`)
  if (cirugia && cirugia.casos > 0) highlights.push(`el ${pct(cirugia.casos, total)}% necesitó cirugía adicional (${cirugia.casos} casos)`)
  if (transf && transf.casos > 0) highlights.push(`el ${pct(transf.casos, total)}% recibió transfusión (${transf.casos} casos)`)

  if (highlights.length === 0) return null

  return `En intervenciones de soporte vital: ${highlights.join(', ')}. Estas medidas reflejan el nivel de rescate obstétrico y requerimiento de recursos asistenciales.`
}

// 14. Modelos de Clustering (PCA)
export function getClusteringAiInsight(clusterData?: {
  n_clusters?: number
  n_samples?: number
  cluster_sizes?: number[]
  clusters?: number[]
  features_used?: string[]
  cluster_profiles?: { cluster_id: number; size: number; features: Record<string, number> }[]
} | null): string | null {
  if (!clusterData) return null

  let sizes = clusterData.cluster_sizes
  if ((!sizes || sizes.length === 0) && clusterData.clusters && clusterData.clusters.length > 0) {
    const counts: Record<number, number> = {}
    clusterData.clusters.forEach((c) => {
      counts[c] = (counts[c] || 0) + 1
    })
    sizes = Object.values(counts)
  }

  if (!sizes || sizes.length === 0) return null

  const nClusters = clusterData.n_clusters || sizes.length
  const nSamples = clusterData.n_samples || sizes.reduce((a, b) => a + b, 0)
  if (nSamples === 0) return null

  const maxSize = Math.max(...sizes)
  const maxIdx = sizes.indexOf(maxSize)
  const maxPct = pct(maxSize, nSamples)

  const featuresTxt =
    clusterData.features_used && clusterData.features_used.length > 0
      ? ` a partir de variables como ${clusterData.features_used.slice(0, 3).join(', ')}`
      : ''

  return `El análisis multivariado agrupó ${nSamples} casos en ${nClusters} conglomerados clínicos diferenciados${featuresTxt}. El Cluster ${maxIdx + 1} concentró la mayor proporción con ${maxSize} casos (${maxPct}% de la población), permitiendo estratificar perfiles de riesgo obstétrico homogéneos.`
}



