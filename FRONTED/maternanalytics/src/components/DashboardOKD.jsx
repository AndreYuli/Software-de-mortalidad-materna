import { useState, useEffect, useRef } from 'react'
import PropTypes from 'prop-types'
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

const ALIAS_COLUMNAS = {
  morbilidad: {
    'Nombres y apellidos': ['Nombre y apellidos', 'Nombres y Apellidos'],
    'Tipo de ID': ['Tipo ID', 'Tipo identificación', 'Tipo de identificación'],
    'N° identificación': ['No identificación', 'Nro identificación', 'Nº identificación', 'Número identificación', 'Numero identificacion'],
    'N° gestaciones': ['No gestaciones', 'Nro gestaciones', 'Nº gestaciones', 'Numero gestaciones'],
    'Partos vaginales': ['Partos Vaginales'],
    'Cesáreas': ['Cesareas'],
    'N° controles prenatales': ['No controles prenatales', 'Nro controles prenatales', 'Nº controles prenatales', 'Numero controles prenatales'],
    'Causa principal CIE-10': ['Causa principal cie10', 'Causa principal CIE10'],
    'Días estancia hospitalaria': ['Dias estancia hospitalaria'],
    'Días estancia UCI': ['Dias estancia UCI'],
  },
  mortalidad: {
    'B. Tipo ID': ['B. Tipo de ID', 'B Tipo ID'],
    'C. Número ID': ['C. Numero ID', 'C Número ID'],
    '8.1 No. CPN': ['8.1 N° CPN', '8.1 Nº CPN', '8.1 Numero CPN'],
  },
}

function normalizeHeader(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/n°|nº/g, 'n ')
    .replaceAll('no.', 'n ')
    .replace(/no\s+/g, 'n ')
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function buildAliasMap(requiredColumns, tipo) {
  const aliasMap = new Map(requiredColumns.map((column) => [normalizeHeader(column), column]))
  Object.entries(ALIAS_COLUMNAS[tipo] || {}).forEach(([canonical, aliases]) => {
    aliasMap.set(normalizeHeader(canonical), canonical)
    aliases.forEach((alias) => aliasMap.set(normalizeHeader(alias), canonical))
  })
  return aliasMap
}

function findHeaderRow(jsonData, requiredColumns, tipo) {
  const aliasMap = buildAliasMap(requiredColumns, tipo)
  let bestIndex = 0
  let bestScore = -1

  jsonData.slice(0, 5).forEach((row, index) => {
    const matchedHeaders = new Set(
      row
        .map((header) => aliasMap.get(normalizeHeader(header)))
        .filter(Boolean),
    )

    if (matchedHeaders.size > bestScore) {
      bestIndex = index
      bestScore = matchedHeaders.size
    }
  })

  return bestIndex
}

function findBestSheet(workbook, requiredColumns, tipo) {
  let bestSheet = workbook.SheetNames[0]
  let bestScore = -1

  workbook.SheetNames.forEach((sheetName) => {
    const sheet = workbook.Sheets[sheetName]
    const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1 })
    const headerRowIndex = findHeaderRow(jsonData, requiredColumns, tipo)
    const aliasMap = buildAliasMap(requiredColumns, tipo)
    const headers = (jsonData[headerRowIndex] || []).map((header) => String(header ?? '').trim())
    const matchedHeaders = new Set(
      headers
        .map((header) => aliasMap.get(normalizeHeader(header)))
        .filter(Boolean),
    )

    if (matchedHeaders.size > bestScore) {
      bestSheet = sheetName
      bestScore = matchedHeaders.size
    }
  })

  return bestSheet
}

async function validateColumns(file, requiredColumns, tipo) {
  try {
    const buffer = await file.arrayBuffer()
    const workbook = XLSX.read(new Uint8Array(buffer), { type: 'array' })
    const bestSheetName = findBestSheet(workbook, requiredColumns, tipo)
    const jsonData = XLSX.utils.sheet_to_json(workbook.Sheets[bestSheetName], { header: 1 })

    if (jsonData.length === 0) {
      return { valid: false, parseError: true }
    }

    const headerRowIndex = findHeaderRow(jsonData, requiredColumns, tipo)
    const headers = (jsonData[headerRowIndex] || []).map((header) => String(header ?? '').trim())
    const aliasMap = buildAliasMap(requiredColumns, tipo)
    const normalizedHeaders = new Set(
      headers
        .map((header) => aliasMap.get(normalizeHeader(header)))
        .filter(Boolean),
    )
    const missing = requiredColumns.filter(
      (column) => !normalizedHeaders.has(column),
    )

    return missing.length > 0
      ? { valid: false, missing, found: headers }
      : { valid: true }
  } catch {
    return { valid: false, parseError: true }
  }
}

// Componente de carga de archivos
function UploadCard({ title, description, color, icon, onFile, file, error, validating }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const openFileDialog = () => inputRef.current?.click()

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }

  const handleChange = (e) => {
    if (e.target.files[0]) onFile(e.target.files[0])
  }

  const handleCardClick = (e) => {
    if (e.target.closest('[data-prevent-open="true"]')) return
    openFileDialog()
  }

  const handleCardKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      openFileDialog()
    }
  }

  const missingColumns = error?.missing ?? []
  const missingColumnsLabel = missingColumns.length === 1 ? 'columna' : 'columnas'

  return (
    <div className={`upload-card-shell ${error ? 'has-error' : ''}`}>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        style={{ display: 'none' }}
        onChange={handleChange}
      />
      <button
        type="button"
        className={`upload-card ${color} ${dragging ? 'dragging' : ''} ${error ? 'has-error' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={handleCardClick}
        onKeyDown={handleCardKeyDown}
        style={{ cursor: 'pointer', minHeight: '250px', padding: '24px' }}
      >
        <span style={{ display: 'block', fontSize: '48px', marginBottom: '16px' }}>{icon}</span>
        <span style={{ display: 'block', fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#151515' }}>{title}</span>
        <span style={{ display: 'block', fontSize: '14px', color: '#666', marginBottom: '16px' }}>{description}</span>

        {validating && <span style={{ color: '#0066cc', marginTop: '12px', display: 'block' }}><small>Validando columnas...</small></span>}

        {!validating && file && !error && (
          <span style={{ marginTop: '12px', padding: '12px', background: '#e7f5e7', borderRadius: '4px', color: '#2d7a2d', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span style={{ fontSize: '13px' }}>{file.name}</span>
          </span>
        )}

        {!validating && !file && !error && (
          <span style={{ marginTop: '12px', color: '#999', fontSize: '13px', display: 'block' }}>
            Arrastra tu archivo aquí o <span style={{ color: '#0066cc', fontWeight: '600' }}>selecciona</span>
            <br /><small>.xlsx · .xls · .csv</small>
          </span>
        )}
      </button>

      {!validating && error && (
        <div
          data-prevent-open="true"
          style={{ marginTop: '12px', padding: '16px', background: '#fef2f2', borderRadius: '4px', color: '#991b1b', fontSize: '13px' }}
        >
          {error.parseError ? (
            <p>No se pudo leer el archivo. Verifica que sea un Excel válido.</p>
          ) : (
            <>
              <p style={{ fontWeight: '600', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Faltan {missingColumns.length} {missingColumnsLabel}
              </p>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                {missingColumns.slice(0, 6).map((column) => <li key={column} style={{ marginBottom: '4px' }}>{column}</li>)}
                {missingColumns.length > 6 && <li style={{ color: '#dc2626', fontWeight: '600' }}>…y {missingColumns.length - 6} más</li>}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  )
}

UploadCard.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  color: PropTypes.string.isRequired,
  icon: PropTypes.string.isRequired,
  onFile: PropTypes.func.isRequired,
  file: PropTypes.shape({
    name: PropTypes.string.isRequired,
  }),
  error: PropTypes.shape({
    parseError: PropTypes.bool,
    missing: PropTypes.arrayOf(PropTypes.string),
    found: PropTypes.arrayOf(PropTypes.string),
  }),
  validating: PropTypes.bool.isRequired,
}

function AnalysisHomeSection({
  analysisType,
  currentAnalysisId,
  latestMortalidad,
  latestMorbilidad,
  onSelectAnalysisType,
  onGoToUpload,
}) {
  return (
    <div className="analysis-home">
      <div className="analysis-switcher">
        <button
          className={`analysis-switch-btn ${analysisType === 'mortalidad' ? 'active' : ''}`}
          onClick={() => onSelectAnalysisType('mortalidad')}
        >
          <span>Mortalidad</span>
          <small>{latestMortalidad ? latestMortalidad.nombre_archivo : 'Sin análisis cargado'}</small>
        </button>
        <button
          className={`analysis-switch-btn ${analysisType === 'morbilidad' ? 'active' : ''}`}
          onClick={() => onSelectAnalysisType('morbilidad')}
        >
          <span>Morbilidad</span>
          <small>{latestMorbilidad ? latestMorbilidad.nombre_archivo : 'Sin análisis cargado'}</small>
        </button>
      </div>

      {!currentAnalysisId && (
        <div className="analysis-empty-state okd-card">
          <h2>{analysisType === 'mortalidad' ? 'Aún no hay análisis de mortalidad' : 'Aún no hay análisis de morbilidad'}</h2>
          <p>
            {analysisType === 'mortalidad'
              ? 'Carga el archivo de mortalidad para ver aquí las gráficas, el resumen y el clustering.'
              : 'Carga el archivo de morbilidad para ver aquí las gráficas, el resumen y el clustering.'}
          </p>
          <button className="primary-action-btn" onClick={() => onGoToUpload(analysisType)}>
            {analysisType === 'mortalidad' ? 'Cargar archivo de mortalidad' : 'Cargar archivo de morbilidad'}
          </button>
        </div>
      )}

      {currentAnalysisId && (
        <AnalisisView
          analisisId={currentAnalysisId}
          showBackButton={false}
          embedded={true}
        />
      )}
    </div>
  )
}

AnalysisHomeSection.propTypes = {
  analysisType: PropTypes.oneOf(['mortalidad', 'morbilidad']).isRequired,
  currentAnalysisId: PropTypes.number,
  latestMortalidad: PropTypes.shape({
    nombre_archivo: PropTypes.string.isRequired,
  }),
  latestMorbilidad: PropTypes.shape({
    nombre_archivo: PropTypes.string.isRequired,
  }),
  onSelectAnalysisType: PropTypes.func.isRequired,
  onGoToUpload: PropTypes.func.isRequired,
}

function UploadSection({
  title,
  description,
  uploadTitle,
  uploadDescription,
  color,
  file,
  error,
  validating,
  done,
  analyzeError,
  analyzing,
  icon,
  actionLabel,
  onFile,
  onAnalyze,
}) {
  const isDisabled = !file || Boolean(error) || validating || analyzing

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '8px', color: '#151515' }}>{title}</h2>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '32px' }}>{description}</p>

      <UploadCard
        title={uploadTitle}
        description={uploadDescription}
        color={color}
        file={file}
        error={error}
        validating={validating}
        onFile={onFile}
        icon={icon}
      />

      <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {done && (
          <div style={{ padding: '12px', background: '#e7f5e7', borderRadius: '4px', color: '#2d7a2d', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span style={{ fontSize: '14px' }}>Análisis guardado correctamente.</span>
          </div>
        )}
        {analyzeError && (
          <div style={{ padding: '12px', background: '#fef2f2', borderRadius: '4px', color: '#991b1b', fontSize: '14px' }}>
            {analyzeError}
          </div>
        )}
        <button
          style={{
            padding: '12px 24px',
            background: isDisabled ? '#e0e0e0' : '#0066cc',
            color: isDisabled ? '#999' : '#fff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: isDisabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s'
          }}
          disabled={isDisabled}
          onClick={onAnalyze}
        >
          {analyzing ? 'Procesando...' : actionLabel}
        </button>
      </div>
    </div>
  )
}

UploadSection.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  uploadTitle: PropTypes.string.isRequired,
  uploadDescription: PropTypes.string.isRequired,
  color: PropTypes.string.isRequired,
  file: PropTypes.shape({
    name: PropTypes.string.isRequired,
  }),
  error: UploadCard.propTypes.error,
  validating: PropTypes.bool.isRequired,
  done: PropTypes.bool.isRequired,
  analyzeError: PropTypes.string,
  analyzing: PropTypes.bool.isRequired,
  icon: PropTypes.string.isRequired,
  actionLabel: PropTypes.string.isRequired,
  onFile: PropTypes.func.isRequired,
  onAnalyze: PropTypes.func.isRequired,
}

export default function DashboardOKD({ onLogout }) {
  const [activeView, setActiveView] = useState('analisis')
  const [analysisType, setAnalysisType] = useState('mortalidad')
  const [selectedAnalisisId, setSelectedAnalisisId] = useState(null)
  const [hasAutoOpenedLatest, setHasAutoOpenedLatest] = useState(false)
  const [analisisList, setAnalisisList] = useState([])

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

  const fetchAnalisis = async (autoOpenLatest = false) => {
    try {
      const res = await fetch(`${API_URL}/analisis/`)
      if (res.ok) {
        const data = await res.json()
        setAnalisisList(data)

        const latestMortalidad = data.find((item) => item.tipo === 'mortalidad')
        const latestMorbilidad = data.find((item) => item.tipo === 'morbilidad')

        if (autoOpenLatest && !hasAutoOpenedLatest && !selectedAnalisisId && data.length > 0) {
          const preferredAnalysis = latestMortalidad || latestMorbilidad || data[0]
          setSelectedAnalisisId(preferredAnalysis.id)
          setAnalysisType(preferredAnalysis.tipo)
          setActiveView('analisis')
          setHasAutoOpenedLatest(true)
        } else if (autoOpenLatest && data.length === 0) {
          setActiveView('analisis')
        }
      }
    } catch { /* backend puede no estar activo */ }
  }

  useEffect(() => {
    const t = setTimeout(() => { fetchAnalisis(true) }, 0)
    return () => clearTimeout(t)
  }, [])

  // Manejo de archivos
  const handleMortalidadFile = async (file) => {
    setMortalidadFile(file)
    setMortalidadError(null)
    setMortalidadDone(false)
    setMortalidadAnalyzeError(null)
    setMortalidadValidating(true)
    const result = await validateColumns(file, COLUMNAS_MORTALIDAD, 'mortalidad')
    setMortalidadValidating(false)
    if (!result.valid) setMortalidadError(result)
  }

  const handleMorbilidadFile = async (file) => {
    setMorbilidadFile(file)
    setMorbilidadError(null)
    setMorbilidadDone(false)
    setMorbilidadAnalyzeError(null)
    setMorbilidadValidating(true)
    const result = await validateColumns(file, COLUMNAS_MORBILIDAD, 'morbilidad')
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
        const createdAnalysis = await res.json()
        setDone(true)
        await fetchAnalisis(false)
        setTimeout(() => {
          setActiveView('analisis')
          setAnalysisType(tipo)
          if (createdAnalysis?.id) {
            setSelectedAnalisisId(createdAnalysis.id)
          }
        }, 1500)
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

  const latestMortalidad = analisisList.find((item) => item.tipo === 'mortalidad') || null
  const latestMorbilidad = analisisList.find((item) => item.tipo === 'morbilidad') || null
  const currentAnalysisForType = analysisType === 'mortalidad' ? latestMortalidad : latestMorbilidad
  const selectedAnalysisForType = analisisList.find(
    (item) => item.id === selectedAnalisisId && item.tipo === analysisType,
  ) || null
  const currentAnalysisId = selectedAnalysisForType?.id || currentAnalysisForType?.id || null

  const handleSelectAnalysisType = (tipo) => {
    setAnalysisType(tipo)
    setActiveView('analisis')

    const nextAnalysis = tipo === 'mortalidad' ? latestMortalidad : latestMorbilidad
    setSelectedAnalisisId(nextAnalysis?.id || null)
  }

  const pageTitle = {
    analisis: 'Análisis epidemiológicos',
    mortalidad: 'Cargar Mortalidad Materna',
    morbilidad: 'Cargar Morbilidad Materna Extrema',
  }[activeView]

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
          <p className="sidebar-section-label-okd">ANALISIS</p>
          <button
            className={`nav-item-okd ${activeView === 'analisis' ? 'active' : ''}`}
            onClick={() => setActiveView('analisis')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            Ver análisis
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
        <div className="page-header-okd">
          <h1>{pageTitle}</h1>
        </div>

        <div className="content-area-okd">
          {activeView === 'analisis' && (
            <AnalysisHomeSection
              analysisType={analysisType}
              currentAnalysisId={currentAnalysisId}
              latestMortalidad={latestMortalidad}
              latestMorbilidad={latestMorbilidad}
              onSelectAnalysisType={handleSelectAnalysisType}
              onGoToUpload={setActiveView}
            />
          )}

          {activeView === 'mortalidad' && (
            <UploadSection
              title="Mortalidad Materna — Evento 550"
              description="Sube el archivo Excel con los registros de mortalidad materna. Se validarán las columnas requeridas."
              uploadTitle="Mortalidad Materna"
              uploadDescription="Evento 550 — Registros de mortalidad materna"
              color="card-mortalidad"
              file={mortalidadFile}
              error={mortalidadError}
              validating={mortalidadValidating}
              done={mortalidadDone}
              analyzeError={mortalidadAnalyzeError}
              analyzing={analyzing}
              icon="📋"
              actionLabel="Iniciar análisis"
              onFile={handleMortalidadFile}
              onAnalyze={() => handleAnalizar('mortalidad', mortalidadFile, setMortalidadDone, setMortalidadAnalyzeError)}
            />
          )}

          {activeView === 'morbilidad' && (
            <UploadSection
              title="Morbilidad Materna Extrema — Evento 549"
              description="Sube el archivo Excel con los registros de morbilidad materna extrema. Se validarán las columnas requeridas."
              uploadTitle="Morbilidad Materna Extrema"
              uploadDescription="Evento 549 — Registros de morbilidad materna extrema"
              color="card-morbilidad"
              file={morbilidadFile}
              error={morbilidadError}
              validating={morbilidadValidating}
              done={morbilidadDone}
              analyzeError={morbilidadAnalyzeError}
              analyzing={analyzing}
              icon="📊"
              actionLabel="Iniciar análisis"
              onFile={handleMorbilidadFile}
              onAnalyze={() => handleAnalizar('morbilidad', morbilidadFile, setMorbilidadDone, setMorbilidadAnalyzeError)}
            />
          )}
        </div>
      </main>
    </div>
  )
}

DashboardOKD.propTypes = {
  onLogout: PropTypes.func.isRequired,
}
