import { useState, useEffect } from 'react'
import PlotlyReact from 'react-plotly.js'
import * as XLSX from 'xlsx'
import './AnalisisView.css'

const Plot = PlotlyReact?.default ?? PlotlyReact

const BARRERAS_LABELS = {
  demora_1: 'Identificación del riesgo',
  demora_2: 'Decisión de buscar ayuda',
  demora_3: 'Llegada al servicio de salud',
  demora_4: 'Atención oportuna y de calidad',
}

const API_URL = 'http://localhost:8000/api'

const CHART_COLORS = {
  blue: '#4d7fd4',
  purple: '#6f42c1',
  orange: '#f39c12',
  red: '#c0392b',
  green: '#2ca02c',
  slate: '#1e3a5f',
  grid: 'rgba(42, 82, 152, 0.08)'
}

const CLUSTER_COLORS = ['#4d7fd4', '#c0392b', '#2ca02c', '#f39c12', '#6f42c1', '#16a085', '#d35400', '#8e44ad']

const CIE10_DESCRIPTIONS = {
  'O26.6': 'Trastornos del hígado durante el embarazo',
  'O99.3': 'Trastornos del sistema nervioso que complican el embarazo',
  'O14': 'Hipertensión gestacional con proteinuria significativa (preeclampsia)',
  'O15': 'Eclampsia',
  'O72': 'Hemorragia posparto',
  'O85': 'Sepsis puerperal',
  'O88': 'Embolia obstétrica',
}

function normalizeText(value) {
  return (value ?? '')
    .toString()
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
}

function tokenizeHeader(value) {
  return normalizeText(value)
    .replace(/[^a-z0-9]+/g, ' ')
    .split(' ')
    .filter(Boolean)
}

function headerMatchesPattern(header, pattern) {
  const normalizedHeader = normalizeText(header)
  const normalizedPattern = normalizeText(pattern)
  if (!normalizedHeader || !normalizedPattern) return false

  if (normalizedHeader === normalizedPattern) return true

  const headerTokens = tokenizeHeader(header)
  const patternTokens = tokenizeHeader(pattern)

  if (!patternTokens.length) return false

  if (patternTokens.length === 1) {
    return headerTokens.includes(patternTokens[0])
  }

  return normalizedHeader.includes(normalizedPattern)
}

function normalizeCie10(code) {
  const raw = (code ?? '').toString().trim().toUpperCase()
  return raw.replace(/\s+/g, '')
}

function getCie10Description(code) {
  const normalized = normalizeCie10(code)
  if (!normalized) return 'Descripción no disponible'

  if (CIE10_DESCRIPTIONS[normalized]) return CIE10_DESCRIPTIONS[normalized]

  // Intentar match por 3 caracteres (ej. O14.1 -> O14)
  const prefix3 = normalized.slice(0, 3)
  if (CIE10_DESCRIPTIONS[prefix3]) return CIE10_DESCRIPTIONS[prefix3]

  return 'Descripción no disponible'
}

function formatCie10Label(code) {
  const normalized = normalizeCie10(code)
  const desc = getCie10Description(normalized)
  return normalized ? `${normalized} - ${desc}` : `Sin código - ${desc}`
}

function buildPercentLabels(values, totalOverride) {
  const safeValues = (values || []).map(v => (Number.isFinite(Number(v)) ? Number(v) : 0))
  const total = Number.isFinite(Number(totalOverride)) ? Number(totalOverride) : safeValues.reduce((a, b) => a + b, 0)
  return safeValues.map(v => {
    const pct = total > 0 ? (v / total) * 100 : 0
    return `${v} (${pct.toFixed(1)}%)`
  })
}

function ChartExplanation({ title, text }) {
  return (
    <div className="chart-explanation">
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  )
}

function getClusterColor(clusterId) {
  const normalized = Number(clusterId)
  if (!Number.isFinite(normalized)) return CLUSTER_COLORS[0]
  return CLUSTER_COLORS[Math.abs(normalized) % CLUSTER_COLORS.length]
}

function getReadableFeatureName(featureName) {
  const normalized = normalizeText(featureName)

  if (normalized.includes('controles prenatales') || normalized.includes('no. cpn')) return 'controles prenatales'
  if (normalized.includes('semana gestacion') || normalized.includes('edad gestacional')) return 'edad gestacional'
  if (normalized.includes('estancia hospitalaria')) return 'estancia hospitalaria'
  if (normalized.includes('total criterios')) return 'criterios de gravedad'
  if (normalized.includes('gestaciones')) return 'gestaciones'
  if (normalized.includes('partos vaginales')) return 'partos vaginales'
  if (normalized.includes('cesareas') || normalized.includes('cesáreas')) return 'cesareas'
  if (normalized.includes('abortos')) return 'abortos'

  return featureName.replace(/^[\d.]+\s*/, '').toLowerCase()
}

function buildClusterDescriptor(profile, allProfiles) {
  const entries = Object.entries(profile?.features || {})
  if (!entries.length) {
    return {
      title: `Perfil ${profile?.cluster_id ?? ''}`.trim(),
      subtitle: 'Grupo de casos con un patron similar en las variables analizadas.'
    }
  }

  const scored = entries.map(([featureName, value]) => {
    const comparableValues = allProfiles
      .map(otherProfile => Number(otherProfile?.features?.[featureName]))
      .filter(number => Number.isFinite(number))

    const baseline = comparableValues.length
      ? comparableValues.reduce((sum, number) => sum + number, 0) / comparableValues.length
      : 0

    const safeBaseline = Math.abs(baseline) > 0.001 ? Math.abs(baseline) : 1
    const relativeDeviation = (Number(value) - baseline) / safeBaseline

    return {
      featureName,
      readableName: getReadableFeatureName(featureName),
      relativeDeviation,
    }
  })

  const positiveSignals = scored
    .filter(item => item.relativeDeviation > 0.15)
    .sort((left, right) => right.relativeDeviation - left.relativeDeviation)

  if (!positiveSignals.length) {
    return {
      title: 'Perfil intermedio',
      subtitle: 'Grupo con valores mas equilibrados frente a los demas clusters.'
    }
  }

  const mainSignals = positiveSignals.slice(0, 2).map(item => item.readableName)
  const title = mainSignals.length === 1
    ? `Perfil con mayor ${mainSignals[0]}`
    : `Perfil con mayor ${mainSignals[0]} y ${mainSignals[1]}`

  return {
    title,
    subtitle: 'Nombre descriptivo generado a partir de los promedios del grupo; no corresponde a un diagnostico clinico.'
  }
}

function AnalisisView({ analisisId, onBack, showBackButton = true, embedded = false }) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [clusteringData, setClusteringData] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [clusterCount, setClusterCount] = useState(3)

  useEffect(() => {
    let isMounted = true
    const controller = new AbortController()

    const cargar = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await fetch(`${API_URL}/analisis/${analisisId}/completo/`, { signal: controller.signal })
        const result = await response.json().catch(() => null)
        if (!response.ok) throw new Error(result?.error || 'Error al cargar análisis')
        if (isMounted) {
          setData(result)
        }
      } catch (err) {
        if (err?.name === 'AbortError') return
        if (isMounted) {
          setError(err?.message || 'Error al cargar análisis')
          setData(null)
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    cargar()
    return () => {
      isMounted = false
      controller.abort()
    }
  }, [analisisId])

  const cargarClustering = async (tipo = 'kmeans') => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/analisis/${analisisId}/clustering/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tipo_clustering: tipo, n_clusters: clusterCount })
      })
      if (!response.ok) throw new Error('Error al generar clustering')
      const result = await response.json()
      setClusteringData(result)
      setLoading(false)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className={`analisis-view${embedded ? ' embedded' : ''}`}>
        <div className="loading">
          <div className="spinner"></div>
          <p>Cargando análisis...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`analisis-view${embedded ? ' embedded' : ''}`}>
        <div className="error-view">
          <p>❌ {error}</p>
          {showBackButton && onBack && <button onClick={onBack} className="btn-back">Volver</button>}
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className={`analisis-view${embedded ? ' embedded' : ''}`}>
      <div className="analisis-header">
        {showBackButton && onBack && (
          <button onClick={onBack} className="btn-back-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </button>
        )}
        <div className="header-info">
          <h1>{data.tipo === 'mortalidad' ? 'Mortalidad Materna' : 'Morbilidad Materna Extrema'}</h1>
          <p className="filename">{data.nombre_archivo}</p>
        </div>
      </div>

      <div className="analisis-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''} 
          onClick={() => setActiveTab('overview')}
        >
          📊 Resumen
        </button>
        <button 
          className={activeTab === 'charts' ? 'active' : ''} 
          onClick={() => setActiveTab('charts')}
        >
          📈 Gráficos
        </button>
        <button 
          className={activeTab === 'clustering' ? 'active' : ''} 
          onClick={() => { setActiveTab('clustering'); if (!clusteringData) cargarClustering(); }}
        >
          🎯 Clustering
        </button>
      </div>

      <div className="analisis-content">
        {activeTab === 'overview' && <OverviewTab data={data} />}
        {activeTab === 'charts' && <ChartsTab data={data} analisisId={analisisId} />}
        {activeTab === 'clustering' && (
          <ClusteringTab 
            data={clusteringData} 
            loading={loading}
            onGenerate={cargarClustering}
            clusterCount={clusterCount}
            setClusterCount={setClusterCount}
          />
        )}
      </div>
    </div>
  )
}

function OverviewTab({ data }) {
  const stats = data.estadisticas_basicas

  return (
    <div className="overview-tab">
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-value">{stats.total_casos}</div>
          <div className="stat-label">Total de Casos</div>
        </div>

        {stats.gestaciones_promedio && (
          <div className="stat-card">
            <div className="stat-icon">🤰</div>
            <div className="stat-value">{stats.gestaciones_promedio.toFixed(1)}</div>
            <div className="stat-label">Gestaciones Promedio</div>
          </div>
        )}

        {stats.controles_prenatales_promedio && (
          <div className="stat-card">
            <div className="stat-icon">🏥</div>
            <div className="stat-value">{stats.controles_prenatales_promedio.toFixed(1)}</div>
            <div className="stat-label">Controles Prenatales</div>
          </div>
        )}

        {stats.estancia_hospitalaria_promedio && (
          <div className="stat-card">
            <div className="stat-icon">🛏️</div>
            <div className="stat-value">{stats.estancia_hospitalaria_promedio.toFixed(1)}</div>
            <div className="stat-label">Días de Estancia</div>
          </div>
        )}
      </div>

      {data.demoras && (
        <div className="section">
          <h2>Barreras en la atención</h2>
          <div className="demoras-grid">
            {Object.entries(data.demoras).map(([key, demora]) => (
              <div key={key} className="demora-card">
                <div className="demora-header">
                  <span className="demora-numero">{BARRERAS_LABELS[key] || demora.nombre}</span>
                  <span className="demora-porcentaje">{demora.porcentaje.toFixed(1)}%</span>
                </div>
                <div className="demora-nombre">{demora.nombre}</div>
                <div className="demora-casos">{demora.casos_con_demora} casos reportaron esta barrera</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.criterios_inclusion && (
        <div className="section">
          <h2>Criterios de Inclusión</h2>
          <div className="criterios-grid">
            {Object.values(data.criterios_inclusion).map((criterio, idx) => (
              <div key={idx} className="criterio-card">
                <div className="criterio-nombre">{criterio.nombre}</div>
                <div className="criterio-stats">
                  <span className="criterio-casos">{criterio.casos} casos</span>
                  <span className="criterio-porcentaje">{criterio.porcentaje.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ChartsTab({ data, analisisId }) {
  const [heatmapData, setHeatmapData] = useState(null)
  const [heatmapLoading, setHeatmapLoading] = useState(false)
  const [heatmapError, setHeatmapError] = useState(null)

  const [extraChart, setExtraChart] = useState(null)
  const [extraChartLoading, setExtraChartLoading] = useState(false)
  const [extraChartError, setExtraChartError] = useState(null)

  useEffect(() => {
    if (data?.tipo !== 'morbilidad') return

    let isMounted = true
    const controller = new AbortController()

    const cargarHeatmap = async () => {
      setHeatmapLoading(true)
      setHeatmapError(null)
      try {
        const response = await fetch(`${API_URL}/analisis/${analisisId}/heatmap/`, { signal: controller.signal })
        const payload = await response.json().catch(() => ({}))

        if (!response.ok) {
          const backendMsg = payload?.error || 'No se pudo generar el heatmap.'
          throw new Error(backendMsg)
        }

        if (payload?.error) {
          throw new Error(payload.error)
        }

        if (isMounted) {
          setHeatmapData(payload)
        }
      } catch (err) {
        if (err?.name === 'AbortError') return
        if (isMounted) {
          setHeatmapError(err?.message || 'Error al cargar heatmap.')
          setHeatmapData(null)
        }
      } finally {
        if (isMounted) setHeatmapLoading(false)
      }
    }

    cargarHeatmap()

    return () => {
      isMounted = false
      controller.abort()
    }
  }, [analisisId, data?.tipo])

  useEffect(() => {
    if (data?.tipo !== 'mortalidad') return

    let isMounted = true
    const controller = new AbortController()

    const detectarDistribucion = async () => {
      setExtraChartLoading(true)
      setExtraChartError(null)
      try {
        // 1) Obtener URL del archivo guardado
        const detailRes = await fetch(`${API_URL}/analisis/${analisisId}/`, { signal: controller.signal })
        const detail = await detailRes.json().catch(() => null)
        if (!detailRes.ok) throw new Error(detail?.error || 'No se pudo leer el análisis.')

        const archivoUrl = detail?.archivo
        if (!archivoUrl) {
          if (isMounted) setExtraChart(null)
          return
        }

        const absoluteUrl = archivoUrl.startsWith('http') ? archivoUrl : `http://localhost:8000${archivoUrl}`
        const fileRes = await fetch(absoluteUrl, { signal: controller.signal })
        if (!fileRes.ok) throw new Error('No se pudo descargar el Excel asociado al análisis.')

        // 2) Leer Excel en el frontend para detectar columnas adicionales
        const buf = await fileRes.arrayBuffer()
        const wb = XLSX.read(buf, { type: 'array' })
        const sheetName = wb.SheetNames?.[0]
        const ws = sheetName ? wb.Sheets[sheetName] : null
        if (!ws) {
          if (isMounted) setExtraChart(null)
          return
        }

        const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: null })
        if (!rows || rows.length < 2) {
          if (isMounted) setExtraChart(null)
          return
        }

        const headers = (rows[0] || []).map(h => (h ?? '').toString().trim())
        const normalizedHeaders = headers.map(h => normalizeText(h))

        const findIndex = (patterns) => {
          return headers.findIndex(h => patterns.some(pattern => headerMatchesPattern(h, pattern)))
        }

        const candidates = [
          {
            kind: 'municipio',
            title: 'Top municipios con más casos (si está disponible)'
          },
          {
            kind: 'departamento',
            title: 'Top departamentos con más casos (si está disponible)'
          },
          {
            kind: 'edad',
            title: 'Distribución por edad (si está disponible)'
          },
          {
            kind: 'regimen',
            title: 'Distribución por régimen (si está disponible)'
          },
          {
            kind: 'eps',
            title: 'Top EPS con más casos (si está disponible)'
          },
        ]

        const kindToPatterns = {
          edad: ['edad', 'edad (anos)', 'edad (años)', 'edad anos', 'edad años'],
          departamento: ['departamento', 'depto', 'dpto'],
          municipio: ['municipio'],
          regimen: ['regimen', 'régimen', 'afiliacion', 'afiliación'],
          eps: ['eps', 'entidad promotora', 'aseguradora'],
        }

        let chosen = null
        for (const c of candidates) {
          const idx = findIndex(kindToPatterns[c.kind] || [])
          if (idx >= 0) {
            chosen = { kind: c.kind, idx, title: c.title, header: headers[idx] }
            break
          }
        }

        if (!chosen) {
          if (isMounted) setExtraChart(null)
          return
        }

        const dataRows = rows.slice(1)

        const cleanCell = (v) => {
          const s = (v ?? '').toString().trim()
          if (!s) return null
          const lowered = normalizeText(s)
          if (lowered === 'nan' || lowered === 'null' || lowered === 'none' || lowered === 'sin dato') return null
          return s
        }

        if (chosen.kind === 'edad') {
          const edades = dataRows
            .map(r => r?.[chosen.idx])
            .map(v => {
              const n = typeof v === 'number' ? v : Number.parseFloat((v ?? '').toString().replace(',', '.'))
              return Number.isFinite(n) ? n : null
            })
            .filter(n => n !== null && n >= 0 && n <= 120)

          if (edades.length < 3) {
            if (isMounted) setExtraChart(null)
            return
          }

          const buckets = [
            { label: '<15', min: 0, max: 14.999 },
            { label: '15-19', min: 15, max: 19.999 },
            { label: '20-24', min: 20, max: 24.999 },
            { label: '25-29', min: 25, max: 29.999 },
            { label: '30-34', min: 30, max: 34.999 },
            { label: '35-39', min: 35, max: 39.999 },
            { label: '40+', min: 40, max: 120 },
          ]

          const counts = buckets.map(b => edades.filter(e => e >= b.min && e <= b.max).length)
          const total = counts.reduce((a, b) => a + b, 0)
          if (total <= 0) {
            if (isMounted) setExtraChart(null)
            return
          }

          if (isMounted) {
            setExtraChart({
              type: 'bar',
              orientation: 'v',
              title: 'Distribución por edad',
              subtitle: `Columna detectada: ${chosen.header}`,
              labels: buckets.map(b => b.label),
              values: counts,
              total,
              xTitle: 'Rango de edad (años)',
              yTitle: 'Casos'
            })
          }
          return
        }

        // Categorías (departamento/municipio/régimen/EPS)
        const cats = dataRows
          .map(r => cleanCell(r?.[chosen.idx]))
          .filter(Boolean)

        if (cats.length < 3) {
          if (isMounted) setExtraChart(null)
          return
        }

        const countsMap = new Map()
        for (const v of cats) {
          const key = v.toString().trim()
          countsMap.set(key, (countsMap.get(key) || 0) + 1)
        }

        const sorted = Array.from(countsMap.entries()).sort((a, b) => b[1] - a[1])
        const top = sorted.slice(0, 10)
        const rest = sorted.slice(10)
        const otherCount = rest.reduce((sum, [, c]) => sum + c, 0)
        const labels = top.map(([k]) => k)
        const values = top.map(([, c]) => c)
        if (otherCount > 0) {
          labels.push('Otros')
          values.push(otherCount)
        }

        const total = values.reduce((a, b) => a + b, 0)
        const titleMap = {
          departamento: 'Top departamentos',
          municipio: 'Top municipios',
          regimen: 'Distribución por régimen',
          eps: 'Top EPS'
        }

        if (isMounted) {
          setExtraChart({
            type: 'bar',
            orientation: 'h',
            title: titleMap[chosen.kind] || 'Distribución',
            subtitle: `Columna detectada: ${chosen.header}`,
            labels,
            values,
            total,
            xTitle: 'Casos',
            yTitle: ''
          })
        }
      } catch (err) {
        if (err?.name === 'AbortError') return
        if (isMounted) {
          setExtraChart(null)
          setExtraChartError(err?.message || 'No se pudo generar el gráfico adicional.')
        }
      } finally {
        if (isMounted) setExtraChartLoading(false)
      }
    }

    detectarDistribucion()

    return () => {
      isMounted = false
      controller.abort()
    }
  }, [analisisId, data?.tipo])

  // Gráfico de momento de muerte/ocurrencia
  const getMomentoChart = () => {
    const distribucion = data.momento_muerte?.distribucion || data.momento_ocurrencia?.distribucion
    if (!distribucion) return null

    const labels = Object.keys(distribucion)
    const values = Object.values(distribucion)
    const text = buildPercentLabels(values)

    const barColors = [
      CHART_COLORS.blue,
      CHART_COLORS.purple,
      CHART_COLORS.orange,
      CHART_COLORS.green,
      CHART_COLORS.red,
    ].slice(0, values.length)

    return (
      <Plot
        data={[{
          type: 'bar',
          x: labels,
          y: values,
          marker: {
            color: barColors,
            line: { color: CHART_COLORS.slate, width: 1.2 }
          },
          text,
          textposition: 'outside',
          cliponaxis: false,
          hovertemplate: '<b>%{x}</b><br>Casos: %{y}<br>%{text}<extra></extra>',
        }]}
        layout={{
          title: data.tipo === 'mortalidad' ? 'Momento de la Muerte' : 'Momento de Ocurrencia',
          xaxis: { title: '' },
          yaxis: { title: 'Número de Casos' },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'rgba(255,255,255,0.9)',
          font: { family: 'Plus Jakarta Sans, sans-serif' },
          height: 380,
          margin: { t: 56, b: 96, l: 60, r: 30 },
        }}
        useResizeHandler={true}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '100%' }}
      />
    )
  }

  // Gráfico de causas CIE-10 (solo mortalidad)
  const getCausasChart = () => {
    if (!data.causas_cie10?.top_causas) return null

    const causas = data.causas_cie10.top_causas.slice(0, 10)
    const codes = causas.map(c => normalizeCie10(c.codigo))
    const values = causas.map(c => c.casos)
    const tickText = codes.map(c => formatCie10Label(c))
    const text = buildPercentLabels(values)

    const palette = [
      CHART_COLORS.blue,
      CHART_COLORS.purple,
      CHART_COLORS.orange,
      CHART_COLORS.red,
      CHART_COLORS.green,
    ]
    const barColors = values.map((_, i) => palette[i % palette.length])

    return (
      <Plot
        data={[{
          type: 'bar',
          x: values,
          y: codes,
          orientation: 'h',
          marker: {
            color: barColors,
            line: { color: CHART_COLORS.slate, width: 1 }
          },
          text,
          textposition: 'outside',
          cliponaxis: false,
          hovertemplate:
            '<b>%{y}</b><br>' +
            'Casos: %{x}<br>' +
            '%{text}<extra></extra>'
        }]}
        layout={{
          title: 'Top 10 Causas Básicas (CIE-10)',
          xaxis: { title: 'Número de Casos' },
          yaxis: {
            title: '',
            automargin: true,
            tickmode: 'array',
            tickvals: codes,
            ticktext: tickText,
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'rgba(255,255,255,0.9)',
          font: { family: 'Plus Jakarta Sans, sans-serif' },
          height: 500,
          margin: { t: 50, l: 120, r: 40, b: 60 }
        }}
        useResizeHandler={true}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '100%' }}
      />
    )
  }

  // Gráfico de demoras (solo mortalidad)
  const getDemorasChart = () => {
    if (!data.demoras) return null

    const items = Object.values(data.demoras)
    const labels = Object.entries(data.demoras).map(([key, demora]) => BARRERAS_LABELS[key] || demora.nombre)
    const percentages = items.map(d => d.porcentaje)
    const counts = items.map(d => d.casos_con_demora)
    const text = labels.map((_, i) => `${counts[i]} casos (${percentages[i].toFixed(1)}%)`)

    const palette = [CHART_COLORS.red, CHART_COLORS.orange, CHART_COLORS.purple, CHART_COLORS.blue]
    const barColors = labels.map((_, i) => palette[i % palette.length])

    return (
      <Plot
        data={[{
          type: 'bar',
          x: percentages,
          y: labels,
          orientation: 'h',
          marker: {
            color: barColors,
            line: { color: CHART_COLORS.slate, width: 1 }
          },
          text,
          textposition: 'outside',
          cliponaxis: false,
          hovertemplate: '<b>%{y}</b><br>%{text}<extra></extra>',
        }]}
        layout={{
          title: 'Barreras identificadas en la atención (casos y %)',
          xaxis: {
            title: 'Porcentaje de casos',
            ticksuffix: '%',
            rangemode: 'tozero',
            gridcolor: CHART_COLORS.grid,
          },
          yaxis: {
            title: '',
            automargin: true,
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'rgba(255,255,255,0.9)',
          font: { family: 'Plus Jakarta Sans, sans-serif' },
          height: 420,
          margin: { t: 56, l: 120, r: 30, b: 60 },
        }}
        useResizeHandler={true}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '100%' }}
      />
    )
  }

  const getExtraChart = () => {
    if (data?.tipo !== 'mortalidad') return null

    if (extraChartLoading) {
      return (
        <div className="chart-container">
          <div className="loading" style={{ padding: '40px 20px' }}>
            <div className="spinner"></div>
            <p>Analizando columna adicional (edad/departamento/municipio/régimen/EPS)...</p>
          </div>
        </div>
      )
    }

    if (!extraChartLoading && extraChartError) {
      return (
        <div className="chart-container">
          <div className="error-view" style={{ padding: '30px 20px' }}>
            <p>⚠️ {extraChartError}</p>
          </div>
        </div>
      )
    }

    if (!extraChartLoading && !extraChartError && !extraChart) return null

    const text = buildPercentLabels(extraChart.values, extraChart.total)
    const palette = [CHART_COLORS.blue, CHART_COLORS.purple, CHART_COLORS.orange, CHART_COLORS.red, CHART_COLORS.green]
    const barColors = extraChart.values.map((_, i) => palette[i % palette.length])

    const trace = extraChart.orientation === 'h'
      ? {
          type: 'bar',
          x: extraChart.values,
          y: extraChart.labels,
          orientation: 'h',
          marker: { color: barColors, line: { color: CHART_COLORS.slate, width: 1 } },
          text,
          textposition: 'outside',
          cliponaxis: false,
          hovertemplate: '<b>%{y}</b><br>Casos: %{x}<br>%{text}<extra></extra>',
        }
      : {
          type: 'bar',
          x: extraChart.labels,
          y: extraChart.values,
          orientation: 'v',
          marker: { color: barColors, line: { color: CHART_COLORS.slate, width: 1 } },
          text,
          textposition: 'outside',
          cliponaxis: false,
          hovertemplate: '<b>%{x}</b><br>Casos: %{y}<br>%{text}<extra></extra>',
        }

    return (
      <div className="chart-container">
        <h3 className="chart-title">{extraChart.title}</h3>
        <div className="chart-meta">
          <div className="chart-subtitle">{extraChart.subtitle}</div>
        </div>
        <Plot
          data={[trace]}
          layout={{
            title: extraChart.title,
            xaxis: {
              title: extraChart.orientation === 'h' ? extraChart.xTitle : extraChart.xTitle,
              automargin: true,
              gridcolor: CHART_COLORS.grid,
            },
            yaxis: {
              title: extraChart.yTitle,
              automargin: true,
              gridcolor: CHART_COLORS.grid,
            },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'rgba(255,255,255,0.9)',
            font: { family: 'Plus Jakarta Sans, sans-serif' },
            height: extraChart.orientation === 'h' ? 520 : 420,
            margin: extraChart.orientation === 'h'
              ? { t: 56, b: 70, l: 160, r: 30 }
              : { t: 56, b: 90, l: 60, r: 30 },
          }}
          useResizeHandler={true}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%', height: '100%' }}
        />
        <ChartExplanation
          title="Que significa esta distribucion"
          text="Esta grafica resume la variable complementaria detectada automaticamente en el archivo. Sirve para ver si una categoria concentra la mayor parte de los casos y comparar rapidamente la diferencia entre grupos."
        />
      </div>
    )
  }

  return (
    <div className="charts-tab">
      <div className="chart-container">
        <h3 className="chart-title">
          {data.tipo === 'mortalidad' ? 'Momento de la muerte' : 'Momento de ocurrencia'}
        </h3>
        {getMomentoChart()}
        <ChartExplanation
          title="Que muestra esta grafica"
          text={
            data.tipo === 'mortalidad'
              ? 'Compara en que momento ocurrio la muerte materna. Las barras mas altas indican los momentos que concentran mas casos dentro del archivo analizado.'
              : 'Compara en que momento ocurrio el evento reportado. Las barras mas altas indican las etapas en las que el evento aparece con mayor frecuencia.'
          }
        />
      </div>

      {data.tipo === 'mortalidad' && (
        <>
          {getExtraChart()}
          <div className="chart-container">
            <h3 className="chart-title">Top 10 causas basicas (CIE-10)</h3>
            {getCausasChart()}
            <ChartExplanation
              title="Como interpretar los codigos CIE-10"
              text="Cada barra representa una causa basica registrada en los casos analizados. El codigo identifica el diagnostico y la cantidad muestra cuantas veces aparece en el archivo cargado."
            />
          </div>
          <div className="chart-container">
            <h3 className="chart-title">Barreras identificadas en la atencion</h3>
            {getDemorasChart()}
            <ChartExplanation
              title="Como interpretar estas barreras"
              text="Muestran en que etapa de la atencion se reportaron dificultades. El porcentaje indica que proporcion de los casos presento esa barrera y el numero de casos muestra cuantas personas fueron afectadas."
            />
          </div>
        </>
      )}

      {data.tipo === 'morbilidad' && (
        <div className="chart-container">
          <h3 className="chart-title">Heatmap de correlacion</h3>
          {heatmapLoading && (
            <div className="loading" style={{ padding: '40px 20px' }}>
              <div className="spinner"></div>
              <p>Generando heatmap de correlación...</p>
            </div>
          )}

          {!heatmapLoading && heatmapError && (
            <div className="error-view" style={{ padding: '30px 20px' }}>
              <p>⚠️ {heatmapError}</p>
            </div>
          )}

          {!heatmapLoading && !heatmapError && heatmapData?.correlation_matrix && heatmapData?.columns && (
            <>
              <Plot
                data={[{
                  type: 'heatmap',
                  x: heatmapData.columns,
                  y: heatmapData.columns,
                  z: heatmapData.correlation_matrix,
                  zmin: -1,
                  zmax: 1,
                  zmid: 0,
                  colorscale: [
                    [0.0, '#1e3a5f'],
                    [0.5, '#f0f7ff'],
                    [1.0, '#c0392b']
                  ],
                  colorbar: {
                    title: { text: 'Correlación', side: 'right' },
                    ticksuffix: '',
                    tickvals: [-1, -0.5, 0, 0.5, 1],
                  },
                  hovertemplate:
                    '<b>%{y}</b> vs <b>%{x}</b><br>' +
                    'Correlación: %{z:.2f}<extra></extra>'
                }]}
                layout={{
                  title: 'Heatmap de correlación (variables epidemiológicas)',
                  xaxis: {
                    title: '',
                    tickangle: -35,
                    automargin: true,
                    gridcolor: 'rgba(42, 82, 152, 0.08)',
                  },
                  yaxis: {
                    title: '',
                    automargin: true,
                    gridcolor: 'rgba(42, 82, 152, 0.08)',
                  },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'rgba(255,255,255,0.9)',
                  font: { family: 'Plus Jakarta Sans, sans-serif' },
                  height: 650,
                  margin: { t: 60, b: 140, l: 140, r: 60 },
                }}
                useResizeHandler={true}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
              <ChartExplanation
                title="Como leer este mapa"
                text="Ayuda a identificar que variables tienden a aparecer juntas. Los tonos mas intensos indican relaciones mas fuertes; los colores cercanos al centro claro muestran relaciones debiles o casi nulas."
              />
            </>
          )}

          {!heatmapLoading && !heatmapError && (!heatmapData || heatmapData?.error) && (
            <div style={{ color: 'var(--text-light)', fontSize: '13px' }}>
              No hay datos suficientes para generar el heatmap.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ClusteringTab({ data, loading, onGenerate, clusterCount, setClusterCount }) {
  if (loading) {
    return (
      <div className="clustering-loading">
        <div className="spinner"></div>
        <p>Generando clustering...</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="clustering-empty">
        <h2>Análisis de Clustering</h2>
        <p>Agrupa casos similares para identificar patrones y perfiles de riesgo</p>
        
        <div className="clustering-controls">
          <label>
            Número de clusters:
            <input 
              type="number" 
              min="2" 
              max="10" 
              value={clusterCount}
              onChange={(e) => setClusterCount(parseInt(e.target.value))}
            />
          </label>
          
          <button onClick={() => onGenerate('kmeans')} className="btn-generate">
            Generar Clustering K-means
          </button>
          
          <button onClick={() => onGenerate('jerarquico')} className="btn-generate">
            Clustering Jerárquico
          </button>
        </div>
      </div>
    )
  }

  if (data.error) {
    return (
      <div className="clustering-error">
        <p>⚠️ {data.error}</p>
        <button onClick={() => onGenerate('kmeans')} className="btn-generate">
          Reintentar
        </button>
      </div>
    )
  }

  const clusterMarkerColors = data?.clusters?.map(clusterId => getClusterColor(clusterId)) || []
  const clusterLegend = data?.cluster_profiles?.map(profile => ({
    id: profile.cluster_id,
    size: profile.size,
    color: getClusterColor(profile.cluster_id),
    descriptor: buildClusterDescriptor(profile, data?.cluster_profiles || []),
  })) || []

  // Gráfico 2D
  const scatter2D = data.pca_2d && (
    <Plot
      data={[{
        type: 'scatter',
        mode: 'markers',
        x: data.pca_2d.x,
        y: data.pca_2d.y,
        marker: {
          size: 10,
          color: clusterMarkerColors,
          showscale: false,
          line: { color: 'white', width: 1 }
        },
        text: data.clusters.map((c, i) => `Caso ${i+1}<br>Cluster ${c}`),
        hovertemplate: '%{text}<extra></extra>'
      }]}
      layout={{
        title: `Clustering 2D (PCA - ${(data.pca_2d.variance_explained * 100).toFixed(1)}% varianza)`,
        xaxis: { title: 'Componente Principal 1' },
        yaxis: { title: 'Componente Principal 2' },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'rgba(255,255,255,0.9)',
        font: { family: 'Plus Jakarta Sans, sans-serif' },
        height: 500
      }}
      config={{ responsive: true }}
      style={{ width: '100%' }}
    />
  )

  // Gráfico 3D
  const scatter3D = data.pca_3d && (
    <Plot
      data={[{
        type: 'scatter3d',
        mode: 'markers',
        x: data.pca_3d.x,
        y: data.pca_3d.y,
        z: data.pca_3d.z,
        marker: {
          size: 6,
          color: clusterMarkerColors,
          showscale: false,
          line: { color: 'white', width: 0.5 }
        },
        text: data.clusters.map((c, i) => `Caso ${i+1}<br>Cluster ${c}`),
        hovertemplate: '%{text}<extra></extra>'
      }]}
      layout={{
        title: `Clustering 3D (PCA - ${(data.pca_3d.variance_explained * 100).toFixed(1)}% varianza)`,
        scene: {
          xaxis: { title: 'PC1' },
          yaxis: { title: 'PC2' },
          zaxis: { title: 'PC3' }
        },
        paper_bgcolor: 'transparent',
        font: { family: 'Plus Jakarta Sans, sans-serif' },
        height: 600
      }}
      config={{ responsive: true }}
      style={{ width: '100%' }}
    />
  )

  return (
    <div className="clustering-tab">
      <div className="clustering-info">
        <h2>Resultados del Clustering</h2>
        <div className="cluster-stats">
          <span><strong>{data.n_clusters}</strong> clusters identificados</span>
          <span><strong>{data.n_samples}</strong> casos analizados</span>
        </div>
        {clusterLegend.length > 0 && (
          <div className="cluster-legend">
            {clusterLegend.map((cluster) => (
              <div key={cluster.id} className="cluster-legend-item">
                <span className="cluster-legend-dot" style={{ backgroundColor: cluster.color }}></span>
                <span>{cluster.descriptor.title}</span>
                <span className="cluster-legend-size">{cluster.size} casos</span>
              </div>
            ))}
          </div>
        )}
        <p className="cluster-help-text">
          Cada color representa un grupo distinto de casos similares. El color no indica gravedad ni prioridad; solo sirve para diferenciar visualmente cada cluster.
        </p>
      </div>

      <div className="chart-container">
        {scatter2D}
      </div>

      <div className="chart-container">
        {scatter3D}
      </div>

      {data.cluster_profiles && (
        <div className="cluster-profiles">
          <h3>Perfiles de Clusters</h3>
          <div className="profiles-grid">
            {data.cluster_profiles.map((profile) => (
              <div key={profile.cluster_id} className="profile-card">
                <div className="profile-header">
                  <div>
                    <span className="profile-label">{buildClusterDescriptor(profile, data.cluster_profiles).title}</span>
                    <div className="profile-subtitle">Cluster {profile.cluster_id}</div>
                  </div>
                  <span className="profile-size">{profile.size} casos</span>
                </div>
                <p className="profile-description">{buildClusterDescriptor(profile, data.cluster_profiles).subtitle}</p>
                <div className="profile-features">
                  {Object.entries(profile.features).map(([key, value]) => (
                    <div key={key} className="feature-item">
                      <span className="feature-name">{key.replace(/^[\d.]+\s/, '')}</span>
                      <span className="feature-value">{value.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="clustering-controls">
        <button onClick={() => onGenerate('kmeans')} className="btn-generate">
          Regenerar con {clusterCount} clusters
        </button>
      </div>
    </div>
  )
}

export default AnalisisView
