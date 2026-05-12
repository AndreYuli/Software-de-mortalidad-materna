import { useState, useEffect, useRef } from 'react'
import './DashboardOKD.css'
import AnalisisView from './AnalisisView'
import * as XLSX from 'xlsx'

const API_URL = 'http://localhost:8000/api'

// Columnas requeridas (alineadas con BACKEND/api/views.py)
const COLUMNAS_MORTALIDAD = [
  'A. Nombres y Apellidos', 'B. Tipo ID', 'C. Número ID',
  '5.1 Sitio de Defunción', '6.1 Convivencia', '6.3 Escolaridad',
  '6.4 Regulación Fecundidad', '6.5 Gestaciones', '6.6 Partos Vaginales',
  '6.7 Cesáreas', '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
  '8.1 No. CPN', '8.2 Semana inicio CPN', '9.1 Momento de la muerte',
  '9.2 Semana gestación', '9.4 Tipo de parto', '10.1 Causa básica CIE-10',
  '10.3.1 Demora 1', '10.3.2 Demora 2', '10.3.3 Demora 3', '10.3.4 Demora 4',
]

const COLUMNAS_MORBILIDAD = [
  'Nombres y apellidos', 'Tipo de ID', 'N° identificación',
  'N° gestaciones', 'Partos vaginales', 'Cesáreas', 'Abortos',
  'N° controles prenatales', 'Semanas inicio CPN',
  'Edad gestacional ocurrencia (sem)', 'Momento ocurrencia',
  'Eclampsia', 'Sepsis sistémica severa', 'Hemorragia obstétrica severa',
  'Preeclampsia', 'Ruptura uterina', 'Ingreso UCI', 'Cirugía adicional',
  'Transfusión', 'Total criterios', 'Causa principal CIE-10',
  'Días estancia hospitalaria', 'Días estancia UCI',
]

async function validateColumns(file, requiredColumns) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const workbook = XLSX.read(data, { type: 'array' })
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
        const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })
        
        if (jsonData.length === 0) {
          resolve({ valid: false, parseError: true })
          return
        }

        const headers = jsonData[0].map((h) => String(h ?? '').trim())
        const headersLower = headers.map((h) => h.toLowerCase())
        const missing = requiredColumns.filter((col) => !headersLower.includes(String(col).trim().toLowerCase()))

        if (missing.length > 0) {
          resolve({ valid: false, missing, found: headers })
        } else {
          resolve({ valid: true })
        }
      } catch {
        resolve({ valid: false, parseError: true })
      }
    }
    reader.readAsArrayBuffer(file)
  })
}

// Componente de carga de archivos
function UploadCard({ title, description, color, icon, onFile, file, error, validating }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }

  const handleChange = (e) => {
    if (e.target.files[0]) onFile(e.target.files[0])
  }

  return (
    <div
      className={`upload-card ${color} ${dragging ? 'dragging' : ''} ${error ? 'has-error' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
      style={{ cursor: 'pointer', minHeight: '250px', padding: '24px' }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        style={{ display: 'none' }}
        onChange={handleChange}
      />
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>{icon}</div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#151515' }}>{title}</h3>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '16px' }}>{description}</p>

      {validating && <div style={{ color: '#0066cc', marginTop: '12px' }}><small>Validando columnas...</small></div>}

      {!validating && file && !error && (
        <div style={{ marginTop: '12px', padding: '12px', background: '#e7f5e7', borderRadius: '4px', color: '#2d7a2d', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span style={{ fontSize: '13px' }}>{file.name}</span>
        </div>
      )}

      {!validating && !file && !error && (
        <div style={{ marginTop: '12px', color: '#999', fontSize: '13px' }}>
          Arrastra tu archivo aquí o <span style={{ color: '#0066cc', fontWeight: '600' }}>selecciona</span>
          <br /><small>.xlsx · .xls · .csv</small>
        </div>
      )}

      {!validating && error && (
        <div style={{ marginTop: '12px', padding: '16px', background: '#fef2f2', borderRadius: '4px', color: '#991b1b', fontSize: '13px' }} onClick={(e) => e.stopPropagation()}>
          {error.parseError ? (
            <p>No se pudo leer el archivo. Verifica que sea un Excel válido.</p>
          ) : (
            <>
              <p style={{ fontWeight: '600', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Faltan {error.missing.length} columna{error.missing.length !== 1 ? 's' : ''}
              </p>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                {error.missing.slice(0, 6).map((col) => <li key={col} style={{ marginBottom: '4px' }}>{col}</li>)}
                {error.missing.length > 6 && <li style={{ color: '#dc2626', fontWeight: '600' }}>…y {error.missing.length - 6} más</li>}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// Componente de Gauge Circular
function CircularGauge({ percentage, label, color }) {
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (percentage / 100) * circumference

  return (
    <div className="gauge-container">
      <svg className="gauge-svg" viewBox="0 0 100 100">
        <circle
          className="gauge-background"
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="#e9ecef"
          strokeWidth="10"
        />
        <circle
          className="gauge-progress"
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
        />
        <text x="50" y="50" className="gauge-percentage" textAnchor="middle" dy=".3em">
          {percentage}%
        </text>
        <text x="50" y="65" className="gauge-label" textAnchor="middle">
          {label}
        </text>
      </svg>
    </div>
  )
}

export default function DashboardOKD({ onLogout }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [activeView, setActiveView] = useState('dashboard')
  const [selectedAnalisisId, setSelectedAnalisisId] = useState(null)
  const [analisisList, setAnalisisList] = useState([])
  const [loadingList, setLoadingList] = useState(false)
  const [stats, setStats] = useState({
    totalAnalisis: 0,
    totalMortalidad: 0,
    totalMorbilidad: 0,
    totalRegistros: 0,
    ultimaActualizacion: null
  })

  // Estados para carga de archivos
  const [mortalidadFile, setMortalidadFile] = useState(null)
  const [morbilidadFile, setMorbilidadFile] = useState(null)
  const [mortalidadError, setMortalidadError] = useState(null)
  const [morbilidadError, setMorbilidadError] = useState(null)
  const [mortalidadValidating, setMortalidadValidating] = useState(false)
  const [morbilidadValidating, setMorbilidadValidating] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [mortalidadDone, setMortalidadDone] = useState(false)
  const [morbilidadDone, setMorbilidadDone] = useState(false)
  const [mortalidadAnalyzeError, setMortalidadAnalyzeError] = useState(null)
  const [morbilidadAnalyzeError, setMorbilidadAnalyzeError] = useState(null)

  const fetchAnalisis = async () => {
    setLoadingList(true)
    try {
      const res = await fetch(`${API_URL}/analisis/`)
      if (res.ok) {
        const data = await res.json()
        setAnalisisList(data)
        
        // Calcular estadísticas
        const totalMortalidad = data.filter(a => a.tipo === 'mortalidad').length
        const totalMorbilidad = data.filter(a => a.tipo === 'morbilidad').length
        const totalRegistros = data.reduce((sum, a) => sum + (a.total_registros || 0), 0)
        const ultimaActualizacion = data.length > 0 
          ? new Date(Math.max(...data.map(a => new Date(a.fecha_carga))))
          : null

        setStats({
          totalAnalisis: data.length,
          totalMortalidad,
          totalMorbilidad,
          totalRegistros,
          ultimaActualizacion
        })
      }
    } catch { /* backend puede no estar activo */ }
    finally { setLoadingList(false) }
  }

  useEffect(() => {
    const t = setTimeout(() => { fetchAnalisis() }, 0)
    return () => clearTimeout(t)
  }, [])

  // Si hay un análisis seleccionado, mostrar la vista de análisis
  if (selectedAnalisisId) {
    return (
      <AnalisisView 
        analisisId={selectedAnalisisId} 
        onBack={() => setSelectedAnalisisId(null)} 
      />
    )
  }

  // Manejo de archivos
  const handleMortalidadFile = async (file) => {
    setMortalidadFile(file)
    setMortalidadError(null)
    setMortalidadDone(false)
    setMortalidadAnalyzeError(null)
    setMortalidadValidating(true)
    const result = await validateColumns(file, COLUMNAS_MORTALIDAD)
    setMortalidadValidating(false)
    if (!result.valid) setMortalidadError(result)
  }

  const handleMorbilidadFile = async (file) => {
    setMorbilidadFile(file)
    setMorbilidadError(null)
    setMorbilidadDone(false)
    setMorbilidadAnalyzeError(null)
    setMorbilidadValidating(true)
    const result = await validateColumns(file, COLUMNAS_MORBILIDAD)
    setMorbilidadValidating(false)
    if (!result.valid) setMorbilidadError(result)
  }

  const handleAnalizar = async (tipo, file, setDone, setAnalyzeError) => {
    setAnalyzing(true)
    setDone(false)
    setAnalyzeError(null)
    try {
      const formData = new FormData()
      formData.append('archivo', file)
      formData.append('tipo', tipo)
      const res = await fetch(`${API_URL}/analisis/`, { method: 'POST', body: formData })
      if (res.ok) {
        setDone(true)
        await fetchAnalisis()
        setTimeout(() => setActiveView('dashboard'), 1500)
      } else {
        const err = await res.json()
        if (Array.isArray(err.columnas_faltantes) && err.columnas_faltantes.length) {
          setAnalyzeError(`Faltan columnas requeridas: ${err.columnas_faltantes.slice(0, 6).join(', ')}${err.columnas_faltantes.length > 6 ? '…' : ''}`)
        } else {
          setAnalyzeError(err.error || 'Error al procesar el archivo.')
        }
      }
    } catch {
      setAnalyzeError('No se pudo conectar con el servidor.')
    } finally {
      setAnalyzing(false)
    }
  }

  // Calcular porcentajes para los gauges
  const cpuUsage = stats.totalAnalisis > 0 ? Math.min((stats.totalAnalisis / 20) * 100, 100) : 0
  const memoryUsage = stats.totalRegistros > 0 ? Math.min((stats.totalRegistros / 1000) * 100, 100) : 0
  const storageUsage = stats.totalMortalidad > 0 ? Math.min((stats.totalMortalidad / 10) * 100, 100) : 0
  const networkUsage = stats.totalMorbilidad > 0 ? Math.min((stats.totalMorbilidad / 10) * 100, 100) : 0

  const recentEvents = analisisList
    .sort((a, b) => new Date(b.fecha_carga) - new Date(a.fecha_carga))
    .slice(0, 5)
    .map(a => ({
      id: a.id,
      tipo: a.tipo,
      nombre: a.nombre_archivo,
      registros: a.total_registros,
      fecha: new Date(a.fecha_carga),
      tiempoTranscurrido: getTimeAgo(new Date(a.fecha_carga))
    }))

  return (
    <div className="dashboard-okd">
      {/* SIDEBAR */}
      <aside className="sidebar-okd">
        <div className="sidebar-logo-okd">
          <svg width="32" height="32" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#0066cc" opacity="0.1"/>
            <path d="M32 8 L52 24 L52 44 L32 56 L12 44 L12 24 Z" fill="none" stroke="#0066cc" strokeWidth="2"/>
            <circle cx="32" cy="32" r="8" fill="#0066cc"/>
          </svg>
          <span>VidaMaterna</span>
        </div>

        <nav className="sidebar-nav-okd">
          <p className="sidebar-section-label-okd">MENÚ</p>
          <button 
            className={`nav-item-okd ${activeView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveView('dashboard')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            Dashboards
          </button>
          <button 
            className={`nav-item-okd ${activeView === 'analisis' ? 'active' : ''}`}
            onClick={() => setActiveView('analisis')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            Análisis
          </button>
          
          <p className="sidebar-section-label-okd" style={{ marginTop: '24px' }}>CARGAR DATOS</p>
          <button 
            className={`nav-item-okd ${activeView === 'mortalidad' ? 'active' : ''}`}
            onClick={() => setActiveView('mortalidad')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
            <div style={{ flex: 1, textAlign: 'left' }}>
              Mortalidad Materna
              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>Evento 550</div>
            </div>
            {mortalidadFile && !mortalidadError && (
              <span style={{ padding: '2px 6px', background: '#52c41a', borderRadius: '3px', fontSize: '10px' }}>✓</span>
            )}
            {mortalidadError && (
              <span style={{ padding: '2px 6px', background: '#ff4d4f', borderRadius: '3px', fontSize: '10px' }}>!</span>
            )}
          </button>
          <button 
            className={`nav-item-okd ${activeView === 'morbilidad' ? 'active' : ''}`}
            onClick={() => setActiveView('morbilidad')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="3"/>
              <path d="M3 9h18M3 15h18M9 3v18"/>
            </svg>
            <div style={{ flex: 1, textAlign: 'left' }}>
              Morbilidad Extrema
              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>Evento 549</div>
            </div>
            {morbilidadFile && !morbilidadError && (
              <span style={{ padding: '2px 6px', background: '#52c41a', borderRadius: '3px', fontSize: '10px' }}>✓</span>
            )}
            {morbilidadError && (
              <span style={{ padding: '2px 6px', background: '#ff4d4f', borderRadius: '3px', fontSize: '10px' }}>!</span>
            )}
          </button>
        </nav>

        <div className="sidebar-footer-okd">
          <div className="avatar-okd">
            {(localStorage.getItem('username') || 'U').charAt(0).toUpperCase()}
          </div>
          <div className="user-info-okd">
            <div className="user-name-okd">{localStorage.getItem('username') || 'Usuario'}</div>
            <div className="user-email-okd">VidaMaterna Analytics</div>
          </div>
          <button className="btn-logout-okd" onClick={onLogout} title="Cerrar sesión">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
              <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main-content-okd">
        {/* Header con título */}
        <div className="page-header-okd">
          <h1>
            {activeView === 'dashboard' && 'Dashboards'}
            {activeView === 'analisis' && 'Análisis guardados'}
            {activeView === 'mortalidad' && 'Cargar Mortalidad Materna'}
            {activeView === 'morbilidad' && 'Cargar Morbilidad Materna Extrema'}
          </h1>
        </div>

        {/* Tabs - solo mostrar en vista dashboard */}
        {activeView === 'dashboard' && (
          <div className="tabs-okd">
            <button 
              className={`tab-okd ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button 
              className={`tab-okd ${activeTab === 'storage' ? 'active' : ''}`}
              onClick={() => setActiveTab('storage')}
            >
              Storage
            </button>
          </div>
        )}

        {/* Content Area */}
        <div className="content-area-okd">
          {/* Vista Dashboard */}
          {activeView === 'dashboard' && activeTab === 'overview' && (
            <div className="overview-grid">
              {/* Details Section */}
              <div className="okd-card details-card">
                <h3 className="card-title-okd">Details</h3>
                <div className="details-grid">
                  <div className="detail-item">
                    <span className="detail-label">Name</span>
                    <span className="detail-value">VidaMaterna Analytics</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Provider</span>
                    <span className="detail-value">Django + React</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Version</span>
                    <span className="detail-value">v1.0</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">OpenShift version</span>
                    <span className="detail-value">v4.0</span>
                  </div>
                </div>
              </div>

              {/* Health Section */}
              <div className="okd-card health-card">
                <div className="card-header-with-link">
                  <h3 className="card-title-okd">Health</h3>
                  <a href="#" className="see-all-link">See all</a>
                </div>
                <div className="health-status">
                  <svg className="health-icon" viewBox="0 0 24 24" fill="none" stroke="#52c41a" strokeWidth="2">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                  <span className="health-text">Cluster is healthy</span>
                </div>
              </div>

              {/* Compliance Section */}
              <div className="okd-card compliance-card">
                <div className="card-header-with-info">
                  <h3 className="card-title-okd">Compliance</h3>
                  <button className="info-btn" title="Información">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="12" y1="16" x2="12" y2="12"/>
                      <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                  </button>
                </div>
                <div className="health-status">
                  <svg className="health-icon" viewBox="0 0 24 24" fill="none" stroke="#52c41a" strokeWidth="2">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                  <span className="health-text">Cluster is compliant</span>
                </div>
              </div>

              {/* Capacity Section */}
              <div className="okd-card capacity-card">
                <h3 className="card-title-okd">Capacity</h3>
                <div className="capacity-grid">
                  <div className="capacity-item">
                    <CircularGauge percentage={Math.round(cpuUsage)} label="Used" color="#0066cc" />
                    <div className="capacity-label">CPU</div>
                    <div className="capacity-details">{stats.totalAnalisis} análisis</div>
                  </div>
                  <div className="capacity-item">
                    <CircularGauge percentage={Math.round(memoryUsage)} label="Used" color="#0066cc" />
                    <div className="capacity-label">Memory</div>
                    <div className="capacity-details">{stats.totalRegistros} registros</div>
                  </div>
                  <div className="capacity-item">
                    <CircularGauge percentage={Math.round(storageUsage)} label="Used" color="#0066cc" />
                    <div className="capacity-label">Storage</div>
                    <div className="capacity-details">{stats.totalMortalidad} mortalidad</div>
                  </div>
                  <div className="capacity-item">
                    <CircularGauge percentage={Math.round(networkUsage)} label="Used" color="#0066cc" />
                    <div className="capacity-label">Network</div>
                    <div className="capacity-details">{stats.totalMorbilidad} morbilidad</div>
                  </div>
                </div>
              </div>

              {/* Inventory Section */}
              <div className="okd-card inventory-card">
                <h3 className="card-title-okd">Inventory</h3>
                <div className="inventory-list">
                  <div className="inventory-item">
                    <span className="inventory-count">{stats.totalAnalisis}</span>
                    <span className="inventory-label">Análisis</span>
                  </div>
                  <div className="inventory-item">
                    <span className="inventory-count">{stats.totalMortalidad}</span>
                    <span className="inventory-label">Mortalidad (550)</span>
                  </div>
                  <div className="inventory-item">
                    <span className="inventory-count">{stats.totalMorbilidad}</span>
                    <span className="inventory-label">Morbilidad (549)</span>
                  </div>
                  <div className="inventory-item">
                    <span className="inventory-count">{stats.totalRegistros}</span>
                    <span className="inventory-label">Registros totales</span>
                  </div>
                </div>
              </div>

              {/* Top Consumers Section */}
              <div className="okd-card top-consumers-card">
                <div className="card-header-with-link">
                  <h3 className="card-title-okd">Top consumers</h3>
                  <select className="consumers-filter">
                    <option>Pods & VMs</option>
                  </select>
                  <select className="consumers-sort">
                    <option>By CPU</option>
                  </select>
                </div>
                <div className="consumers-list">
                  {recentEvents.slice(0, 5).map((event) => (
                    <div key={event.id} className="consumer-item" onClick={() => setSelectedAnalisisId(event.id)}>
                      <div className="consumer-name">{event.nombre}</div>
                      <div className="consumer-bar">
                        <div 
                          className="consumer-bar-fill" 
                          style={{ width: `${Math.min((event.registros / 100) * 100, 100)}%` }}
                        ></div>
                      </div>
                      <div className="consumer-percentage">{event.registros} registros</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Events Section */}
              <div className="okd-card events-card">
                <div className="card-header-with-link">
                  <h3 className="card-title-okd">Events</h3>
                  <a href="#" className="see-all-link">View all</a>
                </div>
                <div className="events-list">
                  {recentEvents.map((event) => (
                    <div key={event.id} className="event-item" onClick={() => setSelectedAnalisisId(event.id)}>
                      <div className="event-time">{event.tiempoTranscurrido}</div>
                      <div className="event-badge">{event.tipo === 'mortalidad' ? 'MM' : 'MBD'}</div>
                      <div className="event-details">
                        <div className="event-title">{event.nombre}</div>
                        <div className="event-description">
                          {event.tipo === 'mortalidad' ? 'Mortalidad Materna' : 'Morbilidad Extrema'} - {event.registros} registros procesados
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeView === 'dashboard' && activeTab === 'storage' && (
            <div className="storage-view">
              <div className="okd-card">
                <h3 className="card-title-okd">Storage Overview</h3>
                <p style={{ color: '#666', marginTop: '12px' }}>Storage metrics and analysis storage details will appear here.</p>
              </div>
            </div>
          )}

          {/* Vista Análisis */}
          {activeView === 'analisis' && (
            <div style={{ padding: '20px' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px', color: '#151515' }}>Análisis guardados</h2>
              {loadingList ? (
                <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>Cargando análisis...</div>
              ) : analisisList.length === 0 ? (
                <div className="okd-card" style={{ textAlign: 'center', padding: '60px 40px' }}>
                  <p style={{ fontSize: '16px', color: '#666', marginBottom: '8px' }}>Aún no hay análisis guardados.</p>
                  <p style={{ fontSize: '14px', color: '#999' }}>Carga un archivo Excel desde el menú lateral para comenzar.</p>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                  {analisisList.map((a) => (
                    <div 
                      key={a.id} 
                      className="okd-card" 
                      style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                      onClick={() => setSelectedAnalisisId(a.id)}
                      onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'}
                      onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                        <div style={{ 
                          padding: '8px', 
                          background: a.tipo === 'mortalidad' ? '#e7f5ff' : '#fff3e0', 
                          borderRadius: '6px',
                          color: a.tipo === 'mortalidad' ? '#0066cc' : '#ff9800'
                        }}>
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            {a.tipo === 'mortalidad' ? (
                              <><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></>
                            ) : (
                              <><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M3 15h18M9 3v18"/></>
                            )}
                          </svg>
                        </div>
                        <div style={{ flex: 1 }}>
                          <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#151515', marginBottom: '4px' }}>
                            {a.nombre_archivo}
                          </h4>
                          <p style={{ fontSize: '12px', color: '#999' }}>
                            {a.tipo === 'mortalidad' ? 'Evento 550' : 'Evento 549'}
                          </p>
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid #f0f0f0' }}>
                        <span style={{ fontSize: '12px', color: '#666' }}>{a.total_registros} registros</span>
                        <span style={{ fontSize: '11px', color: '#999' }}>
                          {new Date(a.fecha_carga).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Vista Cargar Mortalidad */}
          {activeView === 'mortalidad' && (
            <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '8px', color: '#151515' }}>Mortalidad Materna — Evento 550</h2>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '32px' }}>Sube el archivo Excel con los registros de mortalidad materna. Se validarán las columnas requeridas.</p>
              
              <UploadCard
                title="Mortalidad Materna"
                description="Evento 550 — Registros de mortalidad materna"
                color="card-mortalidad"
                file={mortalidadFile}
                error={mortalidadError}
                validating={mortalidadValidating}
                onFile={handleMortalidadFile}
                icon="📋"
              />
              
              <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {mortalidadDone && (
                  <div style={{ padding: '12px', background: '#e7f5e7', borderRadius: '4px', color: '#2d7a2d', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span style={{ fontSize: '14px' }}>Análisis guardado correctamente.</span>
                  </div>
                )}
                {mortalidadAnalyzeError && (
                  <div style={{ padding: '12px', background: '#fef2f2', borderRadius: '4px', color: '#991b1b', fontSize: '14px' }}>
                    {mortalidadAnalyzeError}
                  </div>
                )}
                <button
                  style={{
                    padding: '12px 24px',
                    background: (!mortalidadFile || !!mortalidadError || mortalidadValidating || analyzing) ? '#e0e0e0' : '#0066cc',
                    color: (!mortalidadFile || !!mortalidadError || mortalidadValidating || analyzing) ? '#999' : '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: (!mortalidadFile || !!mortalidadError || mortalidadValidating || analyzing) ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s'
                  }}
                  disabled={!mortalidadFile || !!mortalidadError || mortalidadValidating || analyzing}
                  onClick={() => handleAnalizar('mortalidad', mortalidadFile, setMortalidadDone, setMortalidadAnalyzeError)}
                >
                  {analyzing ? 'Procesando...' : 'Iniciar análisis'}
                </button>
              </div>
            </div>
          )}

          {/* Vista Cargar Morbilidad */}
          {activeView === 'morbilidad' && (
            <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '8px', color: '#151515' }}>Morbilidad Materna Extrema — Evento 549</h2>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '32px' }}>Sube el archivo Excel con los registros de morbilidad materna extrema. Se validarán las columnas requeridas.</p>
              
              <UploadCard
                title="Morbilidad Materna Extrema"
                description="Evento 549 — Registros de morbilidad materna extrema"
                color="card-morbilidad"
                file={morbilidadFile}
                error={morbilidadError}
                validating={morbilidadValidating}
                onFile={handleMorbilidadFile}
                icon="📊"
              />
              
              <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {morbilidadDone && (
                  <div style={{ padding: '12px', background: '#e7f5e7', borderRadius: '4px', color: '#2d7a2d', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span style={{ fontSize: '14px' }}>Análisis guardado correctamente.</span>
                  </div>
                )}
                {morbilidadAnalyzeError && (
                  <div style={{ padding: '12px', background: '#fef2f2', borderRadius: '4px', color: '#991b1b', fontSize: '14px' }}>
                    {morbilidadAnalyzeError}
                  </div>
                )}
                <button
                  style={{
                    padding: '12px 24px',
                    background: (!morbilidadFile || !!morbilidadError || morbilidadValidating || analyzing) ? '#e0e0e0' : '#0066cc',
                    color: (!morbilidadFile || !!morbilidadError || morbilidadValidating || analyzing) ? '#999' : '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: (!morbilidadFile || !!morbilidadError || morbilidadValidating || analyzing) ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s'
                  }}
                  disabled={!morbilidadFile || !!morbilidadError || morbilidadValidating || analyzing}
                  onClick={() => handleAnalizar('morbilidad', morbilidadFile, setMorbilidadDone, setMorbilidadAnalyzeError)}
                >
                  {analyzing ? 'Procesando...' : 'Iniciar análisis'}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function getTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000)
  if (seconds < 60) return `${seconds} seconds ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  const days = Math.floor(hours / 24)
  return `${days} day${days > 1 ? 's' : ''} ago`
}
