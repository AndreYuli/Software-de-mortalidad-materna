import { useState, useEffect } from 'react'
import PlotlyReact from 'react-plotly.js'
import * as XLSX from 'xlsx'
import './AnalisisView.css'

const Plot = PlotlyReact?.default ?? PlotlyReact

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

function AnalisisView({ analisisId, onBack }) {
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
      <div className="analisis-view">
        <div className="loading">
          <div className="spinner"></div>
          <p>Cargando análisis...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="analisis-view">
        <div className="error-view">
          <p>❌ {error}</p>
          <button onClick={onBack} className="btn-back">Volver</button>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="analisis-view">
      <div className="analisis-header">
        <button onClick={onBack} className="btn-back-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
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
          <h2>Análisis de Demoras</h2>
          <div className="demoras-grid">
            {Object.entries(data.demoras).map(([key, demora]) => (
              <div key={key} className="demora-card">
                <div className="demora-header">
                  <span className="demora-numero">{key.replace('demora_', 'Demora ')}</span>
                  <span className="demora-porcentaje">{demora.porcentaje.toFixed(1)}%</span>
                </div>
                <div className="demora-nombre">{demora.nombre}</div>
                <div className="demora-casos">{demora.casos_con_demora} casos con demora</div>
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
          const pats = patterns.map(p => normalizeText(p))
          return normalizedHeaders.findIndex(h => pats.some(p => p && h.includes(p)))
        }

        const candidates = [
          {
            kind: 'edad',
            title: 'Distribución por edad (si está disponible)'
          },
          {
            kind: 'departamento',
            title: 'Top departamentos con más casos (si está disponible)'
          },
          {
            kind: 'municipio',
            title: 'Top municipios con más casos (si está disponible)'
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
          municipio: ['municipio', 'mun'],
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
    const labels = items.map(d => d.nombre)
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
          title: 'Demoras en la atención (casos y %)',
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
      </div>
    )
  }

  return (
    <div className="charts-tab">
      <div className="chart-container">
        {getMomentoChart()}
      </div>

      {data.tipo === 'mortalidad' && (
        <>
          {getExtraChart()}
          <div className="chart-container">
            {getCausasChart()}
          </div>
          <div className="chart-container">
            {getDemorasChart()}
          </div>
        </>
      )}

      {data.tipo === 'morbilidad' && (
        <div className="chart-container">
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
          color: data.clusters,
          colorscale: 'Viridis',
          showscale: true,
          colorbar: { title: 'Cluster' },
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
          color: data.clusters,
          colorscale: 'Viridis',
          showscale: true,
          colorbar: { title: 'Cluster' },
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
                  <span className="profile-label">Cluster {profile.cluster_id}</span>
                  <span className="profile-size">{profile.size} casos</span>
                </div>
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
