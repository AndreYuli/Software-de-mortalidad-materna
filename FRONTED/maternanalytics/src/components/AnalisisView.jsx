import { useState, useEffect } from 'react'
import PlotlyReact from 'react-plotly.js'
import './AnalisisView.css'

const Plot = PlotlyReact?.default ?? PlotlyReact

const API_URL = 'http://localhost:8000/api'

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

  // Gráfico de momento de muerte/ocurrencia
  const getMomentoChart = () => {
    const distribucion = data.momento_muerte?.distribucion || data.momento_ocurrencia?.distribucion
    if (!distribucion) return null

    const labels = Object.keys(distribucion)
    const values = Object.values(distribucion)

    return (
      <Plot
        data={[{
          type: 'bar',
          x: labels,
          y: values,
          marker: {
            color: ['#4d7fd4', '#7aaee8', '#a8cdf0', '#dceeff'],
            line: { color: '#2a5298', width: 1.5 }
          },
          text: values.map(v => v.toString()),
          textposition: 'outside',
        }]}
        layout={{
          title: data.tipo === 'mortalidad' ? 'Momento de la Muerte' : 'Momento de Ocurrencia',
          xaxis: { title: '' },
          yaxis: { title: 'Número de Casos' },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'rgba(255,255,255,0.9)',
          font: { family: 'Plus Jakarta Sans, sans-serif' },
          height: 400,
          margin: { t: 50, b: 100, l: 60, r: 40 }
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />
    )
  }

  // Gráfico de causas CIE-10 (solo mortalidad)
  const getCausasChart = () => {
    if (!data.causas_cie10?.top_causas) return null

    const causas = data.causas_cie10.top_causas.slice(0, 10)
    const labels = causas.map(c => c.codigo)
    const values = causas.map(c => c.casos)

    return (
      <Plot
        data={[{
          type: 'bar',
          x: values,
          y: labels,
          orientation: 'h',
          marker: {
            color: values,
            colorscale: [
              [0, '#f0f7ff'],
              [0.5, '#7aaee8'],
              [1, '#2a5298']
            ],
            line: { color: '#1e3a5f', width: 1 }
          },
          text: values.map(v => v.toString()),
          textposition: 'outside',
        }]}
        layout={{
          title: 'Top 10 Causas Básicas (CIE-10)',
          xaxis: { title: 'Número de Casos' },
          yaxis: { title: '', automargin: true },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'rgba(255,255,255,0.9)',
          font: { family: 'Plus Jakarta Sans, sans-serif' },
          height: 500,
          margin: { t: 50, l: 120, r: 40, b: 60 }
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />
    )
  }

  // Gráfico de demoras (solo mortalidad)
  const getDemorasChart = () => {
    if (!data.demoras) return null

    const labels = Object.values(data.demoras).map(d => d.nombre)
    const values = Object.values(data.demoras).map(d => d.porcentaje)

    return (
      <Plot
        data={[{
          type: 'pie',
          labels: labels,
          values: values,
          hole: 0.4,
          marker: {
            colors: ['#c0392b', '#e74c3c', '#f39c12', '#f1c40f']
          },
          text: values.map(v => `${v.toFixed(1)}%`),
          textposition: 'inside',
          textfont: { color: 'white', size: 13, weight: 'bold' }
        }]}
        layout={{
          title: 'Distribución de Demoras (%)',
          paper_bgcolor: 'transparent',
          font: { family: 'Plus Jakarta Sans, sans-serif' },
          height: 450,
          showlegend: true,
          legend: { orientation: 'v', x: 1, y: 0.5 }
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />
    )
  }

  return (
    <div className="charts-tab">
      <div className="chart-container">
        {getMomentoChart()}
      </div>

      {data.tipo === 'mortalidad' && (
        <>
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
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%' }}
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
