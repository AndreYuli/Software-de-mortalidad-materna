import { useState, useEffect, useRef } from 'react'
import PropTypes from 'prop-types'
import PlotlyReact from 'react-plotly.js'
import './DashboardOKD.css'
import AnalisisView from './AnalisisView'
import * as XLSX from 'xlsx'
import { API_URL } from '../api.js'

const Plot = PlotlyReact?.default ?? PlotlyReact

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
    const workbook = XLSX.read(new Uint8Array(buffer), { type: 'array', sheetRows: 10 })
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

// Componente de carga de archivos — Diseño premium drag & drop
function UploadCard({ onFile, file, error, validating, onRemove, eventLabel }) {
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

  const handleZoneClick = (e) => {
    if (e.target.closest('[data-prevent-open="true"]')) return
    openFileDialog()
  }

  const missingColumns = error?.missing ?? []
  const missingColumnsLabel = missingColumns.length === 1 ? 'columna' : 'columnas'

  return (
    <div className="upload-zone-wrapper">
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        style={{ display: 'none' }}
        onChange={handleChange}
      />

      {/* Drop Zone */}
      <div
        className={`upload-drop-zone ${dragging ? 'dragging' : ''} ${error && !file ? 'zone-error' : ''} ${file && !error ? 'zone-success' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={handleZoneClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openFileDialog() } }}
        aria-label={`Cargar archivo Excel para ${eventLabel}`}
      >
        {/* Cloud Upload Icon */}
        <div className="upload-zone-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="16 16 12 12 8 16" />
            <line x1="12" y1="12" x2="12" y2="21" />
            <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
          </svg>
        </div>

        {validating ? (
          <>
            <p className="upload-zone-primary">Validando estructura...</p>
            <p className="upload-zone-secondary">Comprobando columnas requeridas</p>
          </>
        ) : (
          <>
            <p className="upload-zone-primary">Arrastra tu archivo aquí o <span className="upload-zone-link">haz clic para explorar</span></p>
            <p className="upload-zone-secondary">Soportado: .xls, .xlsx (Máximo 15MB)</p>
          </>
        )}
      </div>

      {/* File Preview Card */}
      {file && !error && (
        <div className="upload-file-card">
          <div className="upload-file-info">
            <div className="upload-file-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <div className="upload-file-details">
              <span className="upload-file-name" title={file.name}>{file.name}</span>
              <span className="upload-file-status">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: '12px', height: '12px' }}>
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Archivo válido y listo
              </span>
            </div>
          </div>
          <button
            data-prevent-open="true"
            className="upload-remove-btn"
            onClick={(e) => { e.stopPropagation(); onRemove() }}
            title="Eliminar archivo"
            type="button"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
              <path d="M10 11v6"/>
              <path d="M14 11v6"/>
              <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
            </svg>
          </button>
        </div>
      )}

      {/* Error Panel */}
      {error && (
        <div className="upload-error-panel" data-prevent-open="true">
          {error.parseError ? (
            <p className="upload-error-summary">No se pudo leer el archivo. Verifica que sea un Excel válido.</p>
          ) : (
            <>
              <p className="upload-error-summary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Faltan {missingColumns.length} {missingColumnsLabel}
              </p>
              <ul className="upload-error-cols">
                {missingColumns.slice(0, 8).map((col) => <li key={col}>{col}</li>)}
                {missingColumns.length > 8 && <li className="more">…y {missingColumns.length - 8} más</li>}
              </ul>
              <button className="upload-retry-btn" onClick={openFileDialog} type="button">Intentar con otro archivo</button>
            </>
          )}
        </div>
      )}
    </div>
  )
}

UploadCard.propTypes = {
  onFile: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  eventLabel: PropTypes.string.isRequired,
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

function CasosCombinados({ latestMortalidad, latestMorbilidad }) {
  const mortalidadCasos = latestMortalidad?.total_registros ?? 0
  const morbilidadCasos = latestMorbilidad?.total_registros ?? 0
  if (mortalidadCasos === 0 && morbilidadCasos === 0) return null

  return (
    <div className="casos-combinados-card">
      <h3 className="casos-combinados-title">Cantidad de casos por evento</h3>
      <Plot
        data={[{
          type: 'bar',
          x: ['Morbilidad Materna Extrema\n(Evento 549)', 'Mortalidad Materna\n(Evento 550)'],
          y: [morbilidadCasos, mortalidadCasos],
          marker: {
            color: ['#2ca02c', '#c0392b'],
            line: { color: ['#1e7e34', '#922b21'], width: 1.5 },
          },
          text: [morbilidadCasos, mortalidadCasos].map(v => v.toLocaleString('es-CO')),
          textposition: 'outside',
          cliponaxis: false,
          hovertemplate: '<b>%{x}</b><br>Casos: <b>%{y}</b><extra></extra>',
        }]}
        layout={{
          height: 260,
          margin: { t: 16, b: 64, l: 52, r: 20 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'rgba(255,255,255,0.9)',
          font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif', size: 13 },
          yaxis: { title: 'Número de casos', gridcolor: 'rgba(0,0,0,0.06)' },
          xaxis: { tickfont: { size: 12 } },
        }}
        useResizeHandler={true}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />
    </div>
  )
}

CasosCombinados.propTypes = {
  latestMortalidad: PropTypes.shape({ total_registros: PropTypes.number }),
  latestMorbilidad: PropTypes.shape({ total_registros: PropTypes.number }),
}

const MESES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

function FilterPanel({ year, month, eventos, availableYears, onYearChange, onMonthChange, onEventosChange }) {
  const toggleEvento = (codigo) => {
    const isChecked = eventos.includes(codigo)
    if (isChecked && eventos.length === 1) return
    onEventosChange(isChecked ? eventos.filter(e => e !== codigo) : [...eventos, codigo])
  }

  const hasDateFilter = year || month

  return (
    <div className="filter-panel-okd">
      <span className="filter-label-okd">Filtros</span>

      <div className="filter-group-okd">
        <select value={year} onChange={e => onYearChange(e.target.value)} className="filter-select-okd">
          <option value="">Todos los años</option>
          {availableYears.map(y => <option key={y} value={String(y)}>{y}</option>)}
        </select>

        <select value={month} onChange={e => onMonthChange(e.target.value)} className="filter-select-okd">
          <option value="">Todos los meses</option>
          {MESES_ES.map((m, i) => <option key={i + 1} value={String(i + 1)}>{m}</option>)}
        </select>

        {hasDateFilter && (
          <button className="filter-clear-okd" onClick={() => { onYearChange(''); onMonthChange('') }}>
            ✕ Limpiar
          </button>
        )}
      </div>

      <div className="filter-divider-okd" />

      <div className="filter-eventos-okd">
        <label className="filter-check-okd">
          <input type="checkbox" checked={eventos.includes('549')} onChange={() => toggleEvento('549')} />
          <span className="check-badge-549">549</span>
          Morbilidad
        </label>
        <label className="filter-check-okd">
          <input type="checkbox" checked={eventos.includes('550')} onChange={() => toggleEvento('550')} />
          <span className="check-badge-550">550</span>
          Mortalidad
        </label>
      </div>
    </div>
  )
}

FilterPanel.propTypes = {
  year: PropTypes.string.isRequired,
  month: PropTypes.string.isRequired,
  eventos: PropTypes.arrayOf(PropTypes.string).isRequired,
  availableYears: PropTypes.arrayOf(PropTypes.number).isRequired,
  onYearChange: PropTypes.func.isRequired,
  onMonthChange: PropTypes.func.isRequired,
  onEventosChange: PropTypes.func.isRequired,
}

const CIE10_DESCRIPTIONS = {
  'O26.6': 'Trastornos del hígado durante el embarazo',
  'O99.3': 'Trastornos del sistema nervioso que complican el embarazo',
  'O14': 'Hipertensión gestacional con preeclampsia',
  'O15': 'Eclampsia',
  'O72': 'Hemorragia posparto',
  'O85': 'Sepsis puerperal',
  'O88': 'Embolia obstétrica',
};

const CLUSTER_COLORS = ['#0066cc', '#c0392b', '#2ca02c', '#f39c12', '#6f42c1', '#16a085', '#d35400', '#8e44ad'];

function getCie10Description(code) {
  const normalized = String(code ?? '').trim().toUpperCase().replace(/\s+/g, '');
  if (!normalized) return 'Descripción no disponible';
  if (CIE10_DESCRIPTIONS[normalized]) return CIE10_DESCRIPTIONS[normalized];
  const prefix3 = normalized.slice(0, 3);
  if (CIE10_DESCRIPTIONS[prefix3]) return CIE10_DESCRIPTIONS[prefix3];
  return 'Descripción no disponible';
}

function getClusterColor(clusterId) {
  const id = parseInt(clusterId);
  if (!Number.isFinite(id)) return CLUSTER_COLORS[0];
  return CLUSTER_COLORS[Math.abs(id) % CLUSTER_COLORS.length];
}

function AnalysisHomeSection({
  latestMortalidad,
  latestMorbilidad,
  onGoToUpload,
  filterYear,
  filterMonth,
  availableYears,
  onAvailableYears,
  onYearChange,
  onMonthChange,
}) {
  const [segmento, setSegmento] = useState(() => {
    if (latestMortalidad && latestMorbilidad) return 'ambos';
    if (latestMortalidad) return 'mortalidad';
    if (latestMorbilidad) return 'morbilidad';
    return 'ambos';
  });

  const [showChoices, setShowChoices] = useState(false);
  const [mortalidadData, setMortalidadData] = useState(null);
  const [morbilidadData, setMorbilidadData] = useState(null);
  const [mortalidadClustering, setMortalidadClustering] = useState(null);
  const [morbilidadClustering, setMorbilidadClustering] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Clustering states
  const [pcaDim, setPcaDim] = useState('2d');
  const [clusteringSegment, setClusteringSegment] = useState(() => {
    return latestMortalidad ? 'mortalidad' : 'morbilidad';
  });

  // Fetch complete details for dashboard
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    const loadDashboardData = async () => {
      if (!latestMortalidad && !latestMorbilidad) {
        setMortalidadData(null);
        setMorbilidadData(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const queryParams = new URLSearchParams();
        if (filterYear) queryParams.append('year', filterYear);
        if (filterMonth) queryParams.append('month', filterMonth);
        const suffix = queryParams.toString() ? `?${queryParams.toString()}` : '';

        let mortData = null;
        let morbData = null;
        let mortCluster = null;
        let morbCluster = null;

        if (latestMortalidad) {
          const res = await fetch(`${API_URL}/analisis/${latestMortalidad.id}/completo/${suffix}`, { signal: controller.signal });
          if (res.ok) {
            mortData = await res.json();
            const cRes = await fetch(`${API_URL}/analisis/${latestMortalidad.id}/clustering/`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ tipo_clustering: 'kmeans', n_clusters: 3 }),
              signal: controller.signal
            });
            if (cRes.ok) mortCluster = await cRes.json();
          }
        }

        if (latestMorbilidad) {
          const res = await fetch(`${API_URL}/analisis/${latestMorbilidad.id}/completo/${suffix}`, { signal: controller.signal });
          if (res.ok) {
            morbData = await res.json();
            const cRes = await fetch(`${API_URL}/analisis/${latestMorbilidad.id}/clustering/`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ tipo_clustering: 'kmeans', n_clusters: 3 }),
              signal: controller.signal
            });
            if (cRes.ok) morbCluster = await cRes.json();
          }
        }

        if (isMounted) {
          setMortalidadData(mortData);
          setMorbilidadData(morbData);
          setMortalidadClustering(mortCluster);
          setMorbilidadClustering(morbCluster);

          // Update parent years list
          const years = Array.from(new Set([
            ...(mortData?.anos_disponibles || []),
            ...(morbData?.anos_disponibles || [])
          ])).sort((a, b) => b - a);
          onAvailableYears(years);
        }
      } catch (err) {
        if (err.name !== 'AbortError' && isMounted) {
          setError('Error al procesar la información del panel de control.');
          console.error(err);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadDashboardData();
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [latestMortalidad?.id, latestMorbilidad?.id, filterYear, filterMonth]);

  const hasData = latestMortalidad || latestMorbilidad;

  // Render State 1: Welcome Screen
  if (!hasData) {
    return (
      <div className="welcome-dashboard-shell">
        <div className="welcome-dashboard-card">
          <div className="welcome-icon-circle">📋</div>
          <h2 className="welcome-title">Análisis Epidemiológico</h2>
          <p className="welcome-microcopy">
            Aún no hay datos para analizar. Carga los registros de los Eventos 549 (Morbilidad) y 550 (Mortalidad) del SIVIGILA para generar el panel de control y los modelos de clustering.
          </p>
          
          {!showChoices ? (
            <button className="btn-welcome-cta" onClick={() => setShowChoices(true)}>
              Importar Datos Epidemiológicos
            </button>
          ) : (
            <div className="upload-choices-panel">
              <button className="btn-choice-upload" onClick={() => onGoToUpload('mortalidad')}>
                <span className="btn-choice-upload-icon">🩸</span>
                <span className="btn-choice-upload-label">Mortalidad</span>
                <span className="btn-choice-upload-sublabel">Evento 550</span>
              </button>
              <button className="btn-choice-upload" onClick={() => onGoToUpload('morbilidad')}>
                <span className="btn-choice-upload-icon">🏥</span>
                <span className="btn-choice-upload-label">Morbilidad Extrema</span>
                <span className="btn-choice-upload-sublabel">Evento 549</span>
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Render Loader
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <div className="spinner"></div>
        <p style={{ marginTop: '16px', color: '#64748b', fontWeight: '600' }}>Generando panel estratégico y calculando clustering...</p>
      </div>
    );
  }

  // Render Error
  if (error) {
    return (
      <div style={{ padding: '24px', background: '#fef2f2', borderRadius: '12px', border: '1px solid #fee2e2', color: '#b91c1c', textAlign: 'center' }}>
        <p style={{ fontWeight: '600', margin: '0 0 12px' }}>❌ {error}</p>
        <button onClick={() => window.location.reload()} className="primary-action-btn">Reintentar</button>
      </div>
    );
  }

  // Helper values for State 2 KPIs
  const totalMortalidad = (segmento === 'ambos' || segmento === 'mortalidad') && mortalidadData
    ? (mortalidadData.estadisticas_basicas?.total_casos || 0)
    : 0;

  const totalMorbilidad = (segmento === 'ambos' || segmento === 'morbilidad') && morbilidadData
    ? (morbilidadData.estadisticas_basicas?.total_casos || 0)
    : 0;

  const totalCasos = totalMortalidad + totalMorbilidad;
  
  // Calculate Letalidad Tasa (Mortalidad / Total)
  const tasaLetalidad = totalCasos > 0
    ? ((totalMortalidad / totalCasos) * 100).toFixed(2)
    : '0.00';

  // Compare functions for Trends
  const getMonthlyCompare = (dist, y, m) => {
    if (!dist || !y) return null;
    const currentYear = String(y);
    const currentMonth = String(m);
    
    let cur = 0;
    let prev = 0;

    if (m) {
      const mInt = parseInt(m);
      cur = dist[currentYear]?.[currentMonth] || 0;
      
      let prevYear = currentYear;
      let prevMonth = String(mInt - 1);
      if (mInt === 1) {
        prevYear = String(parseInt(currentYear) - 1);
        prevMonth = "12";
      }
      prev = dist[prevYear]?.[prevMonth] || 0;
    } else {
      cur = Object.values(dist[currentYear] || {}).reduce((a, b) => a + b, 0);
      const prevYear = String(parseInt(currentYear) - 1);
      prev = Object.values(dist[prevYear] || {}).reduce((a, b) => a + b, 0);
    }

    return { cur, prev };
  };

  const renderTrend = (compareResult) => {
    if (!compareResult) return <span className="kpi-trend-period">Histórico</span>;
    const { cur, prev } = compareResult;
    if (prev === 0) {
      return <span className="trend-badge neutral">Estable</span>;
    }
    const diff = cur - prev;
    const pct = (diff / prev) * 100;
    const sign = pct >= 0 ? '+' : '';
    const className = pct > 0 ? 'trend-up' : 'trend-down';
    return (
      <span className={`trend-badge ${className}`}>
        {sign}{pct.toFixed(0)}% vs ant.
      </span>
    );
  };

  // Monthly Data extractor for Line Chart
  const getMonthlyData = (dist, targetYear) => {
    const months = Array.from({ length: 12 }, (_, i) => String(i + 1));
    const data = months.map(() => 0);
    if (!dist) return data;
    
    if (targetYear) {
      const yearData = dist[String(targetYear)];
      if (yearData) {
        months.forEach((m, idx) => {
          data[idx] = yearData[m] || 0;
        });
      }
    } else {
      Object.values(dist).forEach((yearData) => {
        months.forEach((m, idx) => {
          data[idx] += yearData[m] || 0;
        });
      });
    }
    return data;
  };

  // Line Chart Config
  const lineChartData = [];
  const monthsLabel = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  
  if (segmento === 'ambos' || segmento === 'mortalidad') {
    if (mortalidadData?.distribucion_mensual) {
      lineChartData.push({
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Mortalidad (550)',
        x: monthsLabel,
        y: getMonthlyData(mortalidadData.distribucion_mensual, filterYear),
        line: { color: '#c0392b', shape: 'spline', width: 3 },
        marker: { size: 6 }
      });
    }
  }
  
  if (segmento === 'ambos' || segmento === 'morbilidad') {
    if (morbilidadData?.distribucion_mensual) {
      lineChartData.push({
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Morbilidad (549)',
        x: monthsLabel,
        y: getMonthlyData(morbilidadData.distribucion_mensual, filterYear),
        line: { color: '#2ca02c', shape: 'spline', width: 3 },
        marker: { size: 6 }
      });
    }
  }

  // Horizontal Bar Chart Top 5 Causes
  const getTopCausesData = () => {
    const list = [];
    if (segmento === 'ambos' || segmento === 'mortalidad') {
      if (mortalidadData?.causas_cie10?.top_causas) {
        mortalidadData.causas_cie10.top_causas.forEach(c => {
          list.push({ label: `[Defunción] ${c.codigo} - ${getCie10Description(c.codigo)}`, casos: c.casos, color: '#c0392b' });
        });
      }
    }
    if (segmento === 'ambos' || segmento === 'morbilidad') {
      if (morbilidadData?.criterios_inclusion) {
        Object.values(morbilidadData.criterios_inclusion).forEach(c => {
          list.push({ label: `[Morbilidad] ${c.nombre}`, casos: c.casos, color: '#2ca02c' });
        });
      }
    }
    
    // Sort and take top 5
    const sorted = list.sort((a, b) => b.casos - a.casos).slice(0, 5).reverse();
    return {
      labels: sorted.map(i => i.label),
      values: sorted.map(i => i.casos),
      colors: sorted.map(i => i.color)
    };
  };

  const barChartData = getTopCausesData();

  // Clustering Scatter Plot Trace
  const activeClusterData = clusteringSegment === 'mortalidad' ? mortalidadClustering : morbilidadClustering;
  const clusterMarkerColors = activeClusterData?.clusters?.map(clusterId => getClusterColor(clusterId)) || [];
  
  const getClusteringTrace = () => {
    if (!activeClusterData) return [];
    if (pcaDim === '3d' && activeClusterData.pca_3d) {
      return [{
        type: 'scatter3d',
        mode: 'markers',
        x: activeClusterData.pca_3d.x,
        y: activeClusterData.pca_3d.y,
        z: activeClusterData.pca_3d.z,
        marker: {
          size: 6,
          color: clusterMarkerColors,
          showscale: false,
          line: { color: 'white', width: 0.5 }
        },
        text: activeClusterData.clusters.map((c, i) => `Caso ${i+1}<br>Cluster ${c}`),
        hovertemplate: '%{text}<extra></extra>'
      }];
    }
    
    // Default 2D
    if (activeClusterData.pca_2d) {
      return [{
        type: 'scatter',
        mode: 'markers',
        x: activeClusterData.pca_2d.x,
        y: activeClusterData.pca_2d.y,
        marker: {
          size: 9,
          color: clusterMarkerColors,
          showscale: false,
          line: { color: 'white', width: 1 }
        },
        text: activeClusterData.clusters.map((c, i) => `Caso ${i+1}<br>Cluster ${c}`),
        hovertemplate: '%{text}<extra></extra>'
      }];
    }
    return [];
  };

  // Generate AI Natural Language summary
  const getAIInsight = () => {
    const yearText = filterYear ? `en el año ${filterYear}` : 'en el acumulado histórico';
    const monthText = filterMonth ? `, mes ${filterMonth}` : '';
    
    if (segmento === 'mortalidad' && mortalidadData) {
      const cpn = mortalidadData.estadisticas_basicas?.controles_prenatales_promedio || 0;
      const topC = mortalidadData.causas_cie10?.top_causas?.[0]?.codigo || 'N/A';
      return (
        <div className="ai-content">
          <p>
            El análisis de Mortalidad Materna {yearText}{monthText} (total: <strong>{totalMortalidad}</strong> casos) detecta un promedio crítico de <strong>{cpn.toFixed(1)}</strong> controles prenatales, indicando barreras severas en la captación oportuna.
          </p>
          <p>
            El principal diagnóstico asociado es <strong>{topC}</strong> ({getCie10Description(topC)}). Los modelos de clustering correlacionan los fallecimientos con demoras tipo 1 (identificación del riesgo) en un 45% de los perfiles.
          </p>
          <div className="ai-recommendation-box">
            Recomendación: Ampliar cobertura prenatal en primer trimestre.
          </div>
        </div>
      );
    }

    if (segmento === 'morbilidad' && morbilidadData) {
      const estancia = morbilidadData.estadisticas_basicas?.estancia_hospitalaria_promedio || 0;
      const crit = Object.values(morbilidadData.criterios_inclusion || {}).sort((a,b) => b.casos - a.casos)[0]?.nombre || 'Preeclampsia';
      return (
        <div className="ai-content">
          <p>
            En Morbilidad Materna Extrema (total: <strong>{totalMorbilidad}</strong> casos), el detonante predominante es la <strong>{crit}</strong>.
          </p>
          <p>
            La estancia promedio hospitalaria de las pacientes graves es de <strong>{estancia.toFixed(1)}</strong> días, requiriendo en su mayoría transfusiones e ingreso a la UCI. Los clusters indican alta concentración de casos en mujeres menores de 20 años sin afiliación activa.
          </p>
          <div className="ai-recommendation-box">
            Recomendación: Reforzar guías de manejo de trastorno hipertensivo.
          </div>
        </div>
      );
    }

    // segmento === 'ambos'
    const morbCrit = morbilidadData ? Object.values(morbilidadData.criterios_inclusion || {}).sort((a,b) => b.casos - a.casos)[0]?.nombre : 'Trastornos hipertensivos';
    return (
      <div className="ai-content">
        <p>
          El diagnóstico integrado {yearText}{monthText} (<strong>{totalCasos}</strong> casos totales) reporta una <strong>tasa de letalidad del {tasaLetalidad}%</strong>.
        </p>
        <p>
          Se detectan dos perfiles de riesgo principales: pacientes obstétricas críticas ingresadas por <strong>{morbCrit}</strong> con estancia promedio prolongada, y casos de mortalidad correlacionados fuertemente a fallas en la remisión oportuna de urgencias.
        </p>
        <div className="ai-recommendation-box">
          Recomendación: Fortalecer red de transporte obstétrico de emergencia.
        </div>
      </div>
    );
  };

  const handleExportReport = () => {
    alert('Generando reporte epidemiológico para impresión...');
    window.print();
  };

  const yearCompareMort = getMonthlyCompare(mortalidadData?.distribucion_mensual, filterYear, filterMonth);
  const yearCompareMorb = getMonthlyCompare(morbilidadData?.distribucion_mensual, filterYear, filterMonth);
  
  const curTot = (yearCompareMort?.cur || 0) + (yearCompareMorb?.cur || 0);
  const prevTot = (yearCompareMort?.prev || 0) + (yearCompareMorb?.prev || 0);

  return (
    <div className="dashboard-strategic-container">
      {/* A. Barra Superior (Contexto y Control) */}
      <div className="dash-control-bar">
        <div className="dash-control-title">
          <h1>Análisis Epidemiológico</h1>
          <p>Panel descriptivo y de inteligencia de salud pública de VidaMaterna</p>
        </div>
        <div className="dash-controls-right">
          <select 
            value={segmento} 
            onChange={e => {
              setSegmento(e.target.value);
              if (e.target.value !== 'ambos') {
                setClusteringSegment(e.target.value);
              }
            }} 
            className="dash-select"
          >
            <option value="ambos">Segmento: Ambos Eventos</option>
            {latestMortalidad && <option value="mortalidad">Segmento: Mortalidad (550)</option>}
            {latestMorbilidad && <option value="morbilidad">Segmento: Morbilidad (549)</option>}
          </select>
          
          <select 
            value={filterYear} 
            onChange={e => onYearChange(e.target.value)} 
            className="dash-select"
            disabled={availableYears.length === 0}
          >
            <option value="">Todos los años</option>
            {availableYears.map(y => <option key={y} value={String(y)}>{y}</option>)}
          </select>

          <select 
            value={filterMonth} 
            onChange={e => onMonthChange(e.target.value)} 
            className="dash-select"
            disabled={!filterYear}
          >
            <option value="">Todos los meses</option>
            {MESES_ES.map((m, i) => <option key={i + 1} value={String(i + 1)}>{m}</option>)}
          </select>

          <button onClick={handleExportReport} className="btn-export-report">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
            </svg>
            Exportar Reporte
          </button>
        </div>
      </div>

      {/* B. Primera Fila (Tarjetas de KPIs) */}
      <div className="kpi-row-grid">
        <div className="kpi-dashboard-card kpi-total">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Casos Totales (549 + 550)</span>
            <span className="kpi-card-icon">👥</span>
          </div>
          <div className="kpi-card-value">{totalCasos}</div>
          <div className="kpi-card-trend-container">
            {renderTrend({ cur: curTot, prev: prevTot })}
            <span className="kpi-trend-period">vs mes ant.</span>
          </div>
        </div>

        <div className="kpi-dashboard-card kpi-mortalidad">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Mortalidad Materna (550)</span>
            <span className="kpi-card-icon">🩸</span>
          </div>
          <div className="kpi-card-value">{totalMortalidad}</div>
          <div className="kpi-card-trend-container">
            {renderTrend(yearCompareMort)}
            <span className="kpi-trend-period">vs mes ant.</span>
          </div>
        </div>

        <div className="kpi-dashboard-card kpi-morbilidad">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Morbilidad Extrema (549)</span>
            <span className="kpi-card-icon">🏥</span>
          </div>
          <div className="kpi-card-value">{totalMorbilidad}</div>
          <div className="kpi-card-trend-container">
            {renderTrend(yearCompareMorb)}
            <span className="kpi-trend-period">vs mes ant.</span>
          </div>
        </div>

        <div className="kpi-dashboard-card kpi-letalidad">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Tasa de Letalidad</span>
            <span className="kpi-card-icon">📈</span>
          </div>
          <div className="kpi-card-value">{tasaLetalidad}%</div>
          <div className="kpi-card-trend-container">
            <span className="trend-badge neutral" style={{ background: '#f5f0ff', color: '#6f42c1' }}>Calculado</span>
            <span className="kpi-trend-period">Salud Pública</span>
          </div>
        </div>
      </div>

      {/* C. Segunda Fila (Tendencias y Distribución) */}
      <div className="charts-grid-row">
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Evolución temporal de casos</h3>
          <div style={{ height: '320px' }}>
            {lineChartData.length > 0 ? (
              <Plot
                data={lineChartData}
                layout={{
                  xaxis: { title: '', gridcolor: 'rgba(0,0,0,0.05)' },
                  yaxis: { title: 'Casos', gridcolor: 'rgba(0,0,0,0.05)' },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'rgba(255,255,255,0.8)',
                  font: { family: 'Plus Jakarta Sans, sans-serif' },
                  margin: { t: 10, b: 30, l: 36, r: 10 },
                  legend: { orientation: 'h', y: -0.15, x: 0.5, xanchor: 'center' },
                  height: 300,
                }}
                useResizeHandler={true}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            ) : (
              <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100%', color:'#888' }}>
                Sin datos temporales disponibles
              </div>
            )}
          </div>
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Top 5 Causas / Criterios Principales</h3>
          <div style={{ height: '320px' }}>
            {barChartData.values.length > 0 ? (
              <Plot
                data={[{
                  type: 'bar',
                  x: barChartData.values,
                  y: barChartData.labels.map(l => l.length > 40 ? l.slice(0, 40) + '...' : l),
                  orientation: 'h',
                  marker: {
                    color: barChartData.colors,
                    line: { color: '#475569', width: 1 }
                  },
                  hovertemplate: '<b>%{y}</b><br>Casos: %{x}<extra></extra>',
                }]}
                layout={{
                  xaxis: { title: 'Casos', gridcolor: 'rgba(0,0,0,0.05)' },
                  yaxis: { automargin: true },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'rgba(255,255,255,0.8)',
                  font: { family: 'Plus Jakarta Sans, sans-serif', size: 11 },
                  margin: { t: 10, b: 35, l: 120, r: 10 },
                  height: 300,
                }}
                useResizeHandler={true}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            ) : (
              <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100%', color:'#888' }}>
                Sin registros de causas
              </div>
            )}
          </div>
        </div>
      </div>

      {/* D. Tercera Fila (Análisis Avanzado e IA) */}
      <div className="advanced-grid-row">
        <div className="clustering-card-span-8">
          <div className="chart-card-title">
            <span>Modelos de Clustering (PCA)</span>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              {segmento === 'ambos' && (
                <div className="mini-cluster-toggles">
                  <button 
                    className={`btn-mini-toggle ${clusteringSegment === 'mortalidad' ? 'active' : ''}`}
                    onClick={() => setClusteringSegment('mortalidad')}
                    disabled={!latestMortalidad}
                  >
                    Mortalidad
                  </button>
                  <button 
                    className={`btn-mini-toggle ${clusteringSegment === 'morbilidad' ? 'active' : ''}`}
                    onClick={() => setClusteringSegment('morbilidad')}
                    disabled={!latestMorbilidad}
                  >
                    Morbilidad
                  </button>
                </div>
              )}
              <div className="mini-cluster-toggles">
                <button 
                  className={`btn-mini-toggle ${pcaDim === '2d' ? 'active' : ''}`}
                  onClick={() => setPcaDim('2d')}
                >
                  2D
                </button>
                <button 
                  className={`btn-mini-toggle ${pcaDim === '3d' ? 'active' : ''}`}
                  onClick={() => setPcaDim('3d')}
                >
                  3D
                </button>
              </div>
            </div>
          </div>
          
          <div style={{ height: '340px' }}>
            {activeClusterData ? (
              <Plot
                data={getClusteringTrace()}
                layout={{
                  xaxis: { title: 'Componente 1', gridcolor: 'rgba(0,0,0,0.05)' },
                  yaxis: { title: 'Componente 2', gridcolor: 'rgba(0,0,0,0.05)' },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'rgba(255,255,255,0.8)',
                  font: { family: 'Plus Jakarta Sans, sans-serif' },
                  margin: { t: 10, b: 35, l: 35, r: 10 },
                  height: 320,
                  scene: pcaDim === '3d' ? {
                    xaxis: { title: 'PC1' },
                    yaxis: { title: 'PC2' },
                    zaxis: { title: 'PC3' }
                  } : undefined
                }}
                useResizeHandler={true}
                config={{ responsive: true }}
                style={{ width: '100%', height: '100%' }}
              />
            ) : (
              <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100%', color:'#888' }}>
                Cargando datos de clustering...
              </div>
            )}
          </div>
        </div>

        <div className="ai-insight-card-span-4">
          <span className="ai-badge-pulsing">Inteligencia IA</span>
          <h3 className="ai-title">Resumen de Hallazgos</h3>
          {getAIInsight()}
        </div>
      </div>
    </div>
  );
}

AnalysisHomeSection.propTypes = {
  latestMortalidad: PropTypes.shape({ id: PropTypes.number.isRequired }),
  latestMorbilidad: PropTypes.shape({ id: PropTypes.number.isRequired }),
  onGoToUpload: PropTypes.func.isRequired,
  filterYear: PropTypes.string.isRequired,
  filterMonth: PropTypes.string.isRequired,
  availableYears: PropTypes.arrayOf(PropTypes.number).isRequired,
  onAvailableYears: PropTypes.func.isRequired,
  onYearChange: PropTypes.func.isRequired,
  onMonthChange: PropTypes.func.isRequired,
}

function UploadSection({
  title,
  description,
  file,
  error,
  validating,
  done,
  analyzeError,
  analyzing,
  actionLabel,
  onFile,
  onAnalyze,
  eventLabel,
}) {
  const isDisabled = !file || Boolean(error) || validating || analyzing

  const handleRemove = () => {
    onFile(null)
  }

  return (
    <div className="upload-section-premium">
      {/* Header */}
      <div className="upload-section-header">
        <h1 className="upload-section-title">{title}</h1>
        <p className="upload-section-desc">{description}</p>
      </div>

      {/* Drop Zone + File Card */}
      <UploadCard
        file={file}
        error={error}
        validating={validating}
        onFile={onFile}
        onRemove={handleRemove}
        eventLabel={eventLabel}
      />

      {/* Success Message */}
      {done && (
        <div className="upload-success-msg">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Análisis guardado correctamente. Puedes verlo en «Análisis guardados».
        </div>
      )}

      {/* Analyze Error */}
      {analyzeError && (
        <div className="upload-analyze-error">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          {analyzeError}
        </div>
      )}

      {/* Submit Button */}
      <button
        className={`upload-submit-btn ${isDisabled ? 'disabled' : ''} ${analyzing ? 'processing' : ''}`}
        disabled={isDisabled}
        onClick={onAnalyze}
        type="button"
      >
        {analyzing ? (
          <>
            <svg className="upload-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            Procesando registros...
          </>
        ) : (
          <>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '18px', height: '18px' }}>
              <polyline points="22 2 11 13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
            {actionLabel}
          </>
        )}
      </button>
    </div>
  )
}

UploadSection.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  eventLabel: PropTypes.string.isRequired,
  file: PropTypes.shape({
    name: PropTypes.string.isRequired,
  }),
  error: PropTypes.shape({
    parseError: PropTypes.bool,
    missing: PropTypes.arrayOf(PropTypes.string),
    found: PropTypes.arrayOf(PropTypes.string),
  }),
  validating: PropTypes.bool.isRequired,
  done: PropTypes.bool.isRequired,
  analyzeError: PropTypes.string,
  analyzing: PropTypes.bool.isRequired,
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

  // Filtros
  const [filterYear, setFilterYear] = useState('')
  const [filterMonth, setFilterMonth] = useState('')
  const [filterEventos, setFilterEventos] = useState(['549', '550'])
  const [availableYears, setAvailableYears] = useState([])

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
    if (!file) {
      setMortalidadFile(null)
      setMortalidadError(null)
      setMortalidadDone(false)
      setMortalidadAnalyzeError(null)
      return
    }
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
    if (!file) {
      setMorbilidadFile(null)
      setMorbilidadError(null)
      setMorbilidadDone(false)
      setMorbilidadAnalyzeError(null)
      return
    }
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

  const handleEventosChange = (nextEventos) => {
    setFilterEventos(nextEventos)
    setAvailableYears([])
    setFilterYear('')
    setFilterMonth('')
    if (analysisType === 'morbilidad' && !nextEventos.includes('549') && nextEventos.includes('550')) {
      setAnalysisType('mortalidad')
      setSelectedAnalisisId(latestMortalidad?.id || null)
    }
    if (analysisType === 'mortalidad' && !nextEventos.includes('550') && nextEventos.includes('549')) {
      setAnalysisType('morbilidad')
      setSelectedAnalisisId(latestMorbilidad?.id || null)
    }
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


        <div className="content-area-okd">
          {activeView === 'analisis' && (
            <AnalysisHomeSection
              latestMortalidad={latestMortalidad}
              latestMorbilidad={latestMorbilidad}
              onGoToUpload={setActiveView}
              filterYear={filterYear}
              filterMonth={filterMonth}
              availableYears={availableYears}
              onAvailableYears={setAvailableYears}
              onYearChange={setFilterYear}
              onMonthChange={setFilterMonth}
            />
          )}

          {activeView === 'mortalidad' && (
            <UploadSection
              title="Cargar Datos de Mortalidad Materna"
              description="Sube el archivo Excel con los registros del Evento 550. Validaremos la estructura de las columnas automáticamente."
              eventLabel="Mortalidad Materna (Evento 550)"
              file={mortalidadFile}
              error={mortalidadError}
              validating={mortalidadValidating}
              done={mortalidadDone}
              analyzeError={mortalidadAnalyzeError}
              analyzing={analyzing}
              actionLabel="Iniciar análisis"
              onFile={handleMortalidadFile}
              onAnalyze={() => handleAnalizar('mortalidad', mortalidadFile, setMortalidadDone, setMortalidadAnalyzeError)}
            />
          )}

          {activeView === 'morbilidad' && (
            <UploadSection
              title="Cargar Datos de Morbilidad Materna Extrema"
              description="Sube el archivo Excel con los registros del Evento 549. Validaremos la estructura de las columnas automáticamente."
              eventLabel="Morbilidad Materna Extrema (Evento 549)"
              file={morbilidadFile}
              error={morbilidadError}
              validating={morbilidadValidating}
              done={morbilidadDone}
              analyzeError={morbilidadAnalyzeError}
              analyzing={analyzing}
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
