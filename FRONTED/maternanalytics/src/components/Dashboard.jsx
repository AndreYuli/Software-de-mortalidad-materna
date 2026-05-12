import { useState, useRef, useEffect } from 'react'
import * as XLSX from 'xlsx'
import './Dashboard.css'
import AnalisisView from './AnalisisView'

const API_URL = 'http://localhost:8000/api'

// Columnas requeridas para Mortalidad Materna (Evento 550)
const COLUMNAS_MORTALIDAD = [
  'A. Nombres y Apellidos', 'B. Tipo ID', 'C. Número ID',
  '5.1 Sitio de Defunción', '6.1 Convivencia', '6.3 Escolaridad',
  '6.4 Regulación Fecundidad', '6.5 Gestaciones', '6.6 Partos Vaginales',
  '6.7 Cesáreas', '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
  '8.1 No. CPN', '8.2 Semana inicio CPN', '9.1 Momento de la muerte',
  '9.2 Semana gestación', '9.4 Tipo de parto', '10.1 Causa básica CIE-10',
  '10.3.1 Demora 1', '10.3.2 Demora 2', '10.3.3 Demora 3', '10.3.4 Demora 4',
]

// Columnas requeridas para Morbilidad Materna Extrema (Evento 549)
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
        const sheet = workbook.Sheets[workbook.SheetNames[0]]
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 })
        if (!rows.length) { resolve({ valid: false, missing: requiredColumns, found: [] }); return }
        const headers = rows[0].map((h) => String(h ?? '').trim())
        const missing = requiredColumns.filter(
          (col) => !headers.some((h) => h.toLowerCase() === col.toLowerCase())
        )
        resolve({ valid: missing.length === 0, missing, found: headers })
      } catch {
        resolve({ valid: false, missing: requiredColumns, found: [], parseError: true })
      }
    }
    reader.readAsArrayBuffer(file)
  })
}

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
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        style={{ display: 'none' }}
        onChange={handleChange}
      />
      <div className="upload-icon">{icon}</div>
      <h3 className="upload-title">{title}</h3>
      <p className="upload-desc">{description}</p>

      {validating && <div className="upload-hint"><small>Validando columnas...</small></div>}

      {!validating && file && !error && (
        <div className="upload-file-name">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {file.name}
        </div>
      )}

      {!validating && !file && !error && (
        <div className="upload-hint">
          Arrastra tu archivo aquí o <span>selecciona</span>
          <br /><small>.xlsx · .xls · .csv</small>
        </div>
      )}

      {!validating && error && (
        <div className="upload-error" onClick={(e) => e.stopPropagation()}>
          {error.parseError ? (
            <p className="error-summary">No se pudo leer el archivo. Verifica que sea un Excel válido.</p>
          ) : (
            <>
              <p className="error-summary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Faltan {error.missing.length} columna{error.missing.length !== 1 ? 's' : ''}
              </p>
              <ul className="error-cols">
                {error.missing.slice(0, 8).map((col) => <li key={col}>{col}</li>)}
                {error.missing.length > 8 && <li className="more">…y {error.missing.length - 8} más</li>}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [activeView, setActiveView] = useState('home')
  const [selectedAnalisisId, setSelectedAnalisisId] = useState(null)
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
  const [analisisList, setAnalisisList] = useState([])
  const [loadingList, setLoadingList] = useState(false)
  const [showDuplicates, setShowDuplicates] = useState(false)

  // Si hay un análisis seleccionado, mostrar la vista de análisis
  if (selectedAnalisisId) {
    return (
      <AnalisisView 
        analisisId={selectedAnalisisId} 
        onBack={() => setSelectedAnalisisId(null)} 
      />
    )
  }

  const fetchAnalisis = async () => {
    setLoadingList(true)
    try {
      const res = await fetch(`${API_URL}/analisis/`)
      if (res.ok) setAnalisisList(await res.json())
    } catch { /* backend puede no estar activo */ }
    finally { setLoadingList(false) }
  }

  // Deduplicar análisis por nombre de archivo (mantener solo el más reciente)
  const getUniqueAnalisis = (lista) => {
    if (showDuplicates) return lista
    const map = new Map()
    lista.forEach(a => {
      const key = `${a.tipo}-${a.nombre_archivo}`
      const existing = map.get(key)
      if (!existing || new Date(a.fecha_carga) > new Date(existing.fecha_carga)) {
        map.set(key, a)
      }
    })
    return Array.from(map.values()).sort((a, b) => 
      new Date(b.fecha_carga) - new Date(a.fecha_carga)
    )
  }

  const formatDateTime = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-CO', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  useEffect(() => { fetchAnalisis() }, [])

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
      const fd = new FormData()
      fd.append('tipo', tipo)
      fd.append('archivo', file)
      const res = await fetch(`${API_URL}/subir/`, { method: 'POST', body: fd })
      const data = await res.json()
      if (res.ok) {
        setDone(true)
        await fetchAnalisis()
      } else {
        setAnalyzeError(data.error || 'Error al enviar el archivo.')
      }
    } catch {
      setAnalyzeError('No se pudo conectar con el servidor. ¿Está el backend activo en localhost:8000?')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="dashboard">

      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <svg width="28" height="28" viewBox="0 0 64 64">
            <path d="M32 4 C52 4 58 20 58 34 C58 52 46 60 32 60 C18 60 6 52 6 34 C6 20 12 4 32 4Z" fill="none" stroke="#7aaee8" strokeWidth="1.5"/>
            <path d="M26 16 C18 24 16 34 22 44 C26 48 30 52 32 54" fill="none" stroke="#a8cdf0" strokeWidth="2" strokeLinecap="round"/>
            <path d="M38 14 C46 22 48 34 42 44 C38 48 34 52 32 54" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
            <circle cx="32" cy="36" r="4" fill="none" stroke="#a8cdf0" strokeWidth="1.2"/>
            <circle cx="32" cy="36" r="1.5" fill="#a8cdf0"/>
          </svg>
          <span>VidaMaterna</span>
        </div>

        <nav className="sidebar-nav">
          <p className="sidebar-section-label">Menú</p>

          <button
            className={`nav-item ${activeView === 'home' ? 'active' : ''}`}
            onClick={() => setActiveView('home')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            Inicio
          </button>

          <button
            className={`nav-item ${activeView === 'analisis' ? 'active' : ''}`}
            onClick={() => setActiveView('analisis')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            Análisis guardados
          </button>

          <p className="sidebar-section-label" style={{marginTop:'24px'}}>Cargar datos</p>

          <button
            className={`nav-item nav-upload nav-mortalidad ${activeView === 'mortalidad' ? 'active' : ''}`}
            onClick={() => setActiveView('mortalidad')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
            <span>
              Mortalidad Materna
              <small>Evento 550</small>
            </span>
            {mortalidadFile && !mortalidadError && (
              <span className="nav-badge ok">✓</span>
            )}
            {mortalidadError && (
              <span className="nav-badge err">!</span>
            )}
          </button>

          <button
            className={`nav-item nav-upload nav-morbilidad ${activeView === 'morbilidad' ? 'active' : ''}`}
            onClick={() => setActiveView('morbilidad')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="3"/>
              <path d="M3 9h18M3 15h18M9 3v18"/>
            </svg>
            <span>
              Morbilidad Extrema
              <small>Evento 549</small>
            </span>
            {morbilidadFile && !morbilidadError && (
              <span className="nav-badge ok">✓</span>
            )}
            {morbilidadError && (
              <span className="nav-badge err">!</span>
            )}
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">A</div>
            <div className="user-info">
              <p className="user-name">Analista</p>
              <p className="user-email">vidamaterna.gov.co</p>
            </div>
          </div>
          <button className="btn-logout" onClick={onLogout} title="Cerrar sesión">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="dash-main">

        {/* HOME */}
        {(activeView === 'home' || activeView === 'analisis') && (
          <div className="view-content">
            <div className="view-header">
              <h1>{activeView === 'analisis' ? 'Análisis guardados' : 'Inicio'}</h1>
              <p>Archivos procesados y sus estadísticas de análisis.</p>
            </div>
            {loadingList ? (
              <div className="empty-state"><span>Cargando análisis...</span></div>
            ) : analisisList.length === 0 ? (
              <div className="empty-state">
                <svg viewBox="0 0 64 64" fill="none">
                  <rect x="8" y="16" width="48" height="36" rx="4" stroke="#a8cdf0" strokeWidth="2"/>
                  <path d="M8 24h48" stroke="#a8cdf0" strokeWidth="2"/>
                  <rect x="16" y="32" width="10" height="12" rx="2" fill="#dceeff"/>
                  <rect x="30" y="28" width="10" height="16" rx="2" fill="#a8cdf0"/>
                  <rect x="44" y="34" width="8" height="10" rx="2" fill="#7aaee8"/>
                </svg>
                <p>Aún no hay análisis guardados.</p>
                <span>Carga un archivo Excel desde el menú lateral para comenzar.</span>
              </div>
            ) : (() => {
              const displayList = getUniqueAnalisis(analisisList)
              const allEmpty = displayList.every(a => a.total_registros === 0)
              const hasDuplicates = analisisList.length > displayList.length

              return (
                <>
                  {hasDuplicates && (
                    <div style={{ marginBottom: '12px', padding: '10px 14px', background: '#fff3cd', borderRadius: '8px', fontSize: '13px', color: '#856404', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <svg style={{ width: '16px', height: '16px', flexShrink: 0 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                      <span style={{ flex: 1 }}>
                        {analisisList.length - displayList.length} duplicado(s) oculto(s). Mostrando solo versión más reciente.
                      </span>
                      <button 
                        onClick={() => setShowDuplicates(!showDuplicates)}
                        style={{ padding: '4px 10px', background: '#ffc107', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '12px', fontWeight: '600', whiteSpace: 'nowrap' }}
                      >
                        {showDuplicates ? 'Ocultar' : 'Ver todos'}
                      </button>
                    </div>
                  )}
                  {allEmpty && (
                    <div style={{ marginBottom: '12px', padding: '10px 14px', background: '#f8d7da', borderRadius: '8px', fontSize: '13px', color: '#721c24', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <svg style={{ width: '16px', height: '16px', flexShrink: 0 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
                      </svg>
                      Todos los archivos tienen 0 registros. Verifica que contengan datos válidos.
                    </div>
                  )}
                  <div className="analisis-list">
                    {displayList.map((a) => (
                      <div 
                        key={a.id} 
                        className="analisis-card" 
                        onClick={() => setSelectedAnalisisId(a.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <span className={`analisis-tag tag-${a.tipo}`}>
                          {a.tipo === 'mortalidad' ? 'MORTALIDAD — EVENTO 550' : 'MORBILIDAD — EVENTO 549'}
                        </span>
                        <p className="analisis-filename" title={a.nombre_archivo}>{a.nombre_archivo}</p>
                        <div className="analisis-meta">
                          <span className={a.total_registros === 0 ? 'registros-empty' : ''}>
                            {a.total_registros} {a.total_registros === 1 ? 'registro' : 'registros'}
                          </span>
                          <span title={formatDateTime(a.fecha_carga)}>
                            {new Date(a.fecha_carga).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                            {' · '}
                            {new Date(a.fecha_carga).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )
            })()}
          </div>
        )}

        {/* MORTALIDAD UPLOAD */}
        {activeView === 'mortalidad' && (
          <div className="view-content">
            <div className="view-header">
              <h1>Mortalidad Materna — Evento 550</h1>
              <p>Sube el archivo Excel con los registros de mortalidad materna. Se validarán las columnas requeridas.</p>
            </div>
            <div className="single-upload">
              <UploadCard
                title="Mortalidad Materna"
                description="Evento 550 — Registros de mortalidad materna"
                color="card-mortalidad"
                file={mortalidadFile}
                error={mortalidadError}
                validating={mortalidadValidating}
                onFile={handleMortalidadFile}
                icon={
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                  </svg>
                }
              />
              <div className="upload-actions">
                {mortalidadDone && (
                  <p className="success-msg">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    Análisis guardado correctamente.
                  </p>
                )}
                {mortalidadAnalyzeError && (
                  <p className="analyze-error">{mortalidadAnalyzeError}</p>
                )}
                <button
                  className="btn-analizar"
                  disabled={!mortalidadFile || !!mortalidadError || mortalidadValidating || analyzing}
                  onClick={() => handleAnalizar('mortalidad', mortalidadFile, setMortalidadDone, setMortalidadAnalyzeError)}
                >
                  {analyzing ? 'Procesando...' : 'Iniciar análisis'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MORBILIDAD UPLOAD */}
        {activeView === 'morbilidad' && (
          <div className="view-content">
            <div className="view-header">
              <h1>Morbilidad Materna Extrema — Evento 549</h1>
              <p>Sube el archivo Excel con los registros de morbilidad materna extrema. Se validarán las columnas requeridas.</p>
            </div>
            <div className="single-upload">
              <UploadCard
                title="Morbilidad Materna Extrema"
                description="Evento 549 — Registros de morbilidad materna extrema"
                color="card-morbilidad"
                file={morbilidadFile}
                error={morbilidadError}
                validating={morbilidadValidating}
                onFile={handleMorbilidadFile}
                icon={
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="3"/>
                    <path d="M3 9h18M3 15h18M9 3v18"/>
                  </svg>
                }
              />
              <div className="upload-actions">
                {morbilidadDone && (
                  <p className="success-msg">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    Análisis guardado correctamente.
                  </p>
                )}
                {morbilidadAnalyzeError && (
                  <p className="analyze-error">{morbilidadAnalyzeError}</p>
                )}
                <button
                  className="btn-analizar"
                  disabled={!morbilidadFile || !!morbilidadError || morbilidadValidating || analyzing}
                  onClick={() => handleAnalizar('morbilidad', morbilidadFile, setMorbilidadDone, setMorbilidadAnalyzeError)}
                >
                  {analyzing ? 'Procesando...' : 'Iniciar análisis'}
                </button>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
