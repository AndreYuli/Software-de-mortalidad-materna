import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'

/* ───── Types ───── */
export interface SeveridadFallasData {
  fallas: { nombre: string; casos: number }[]
  severidad: { nombre: string; casos: number }[]
  total_casos: number
}

export interface MorbKpis {
  totalCasos: number
  edadPromedio: number | null
  estanciaHospitalaria: number | null
  estanciaUci: number | null
  criteriosPromedio: number | null
}

export interface CriterioItem {
  nombre: string
  casos: number
  porcentaje: number
}

export interface MomentoItem {
  label: string
  count: number
}

export interface TiempoRemision {
  valores: number[]
  min: number
  q1: number
  median: number
  mean: number
  q3: number
  max: number
  total: number
}

export interface SeveridadFallasMorbilidadProps {
  data: SeveridadFallasData | undefined
  morbKpis: MorbKpis | null
  criteriosInclusion: CriterioItem[] | null
  momentoOcurrencia: MomentoItem[] | null
  tiempoRemision: TiempoRemision | null
}

/* ───── Helpers ───── */
const FALLA_ICONS: Record<string, string> = {
  cardiaca: '❤️', cardíaca: '❤️',
  vascular: '🩸', renal: '🫘',
  hepática: '🟤', hepatica: '🟤',
  metabólica: '⚗️', metabolica: '⚗️',
  cerebral: '🧠', respiratoria: '🫁',
  coagulación: '🩹', coagulacion: '🩹',
}

const SEVERITY_ICONS: Record<string, { icon: string; gradient: string }> = {
  'Ingreso UCI': { icon: '🏥', gradient: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)' },
  'Cirugía Adicional': { icon: '🔪', gradient: 'linear-gradient(135deg, #ea580c 0%, #9a3412 100%)' },
  'Transfusión': { icon: '💉', gradient: 'linear-gradient(135deg, #d97706 0%, #92400e 100%)' },
}

const MOMENTO_COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe']

const CRITERIO_COLORS: Record<string, string> = {
  'Hemorragia': '#dc2626',
  'Eclampsia': '#ea580c',
  'Preeclampsia severa': '#d97706',
  'Sepsis': '#059669',
  'Ruptura uterina': '#7c3aed',
}

function getFallaIcon(nombre: string): string {
  const lower = nombre.toLowerCase()
  for (const [key, icon] of Object.entries(FALLA_ICONS)) {
    if (lower.includes(key)) return icon
  }
  return '⚠️'
}

/* ───── Sub-components ───── */

const MorbKpiRow: React.FC<{ kpis: MorbKpis }> = ({ kpis }) => {
  const cards = [
    { title: 'Total Casos MME', value: kpis.totalCasos, suffix: '', icon: '🏥', accent: '#0066cc' },
    { title: 'Edad Promedio', value: kpis.edadPromedio, suffix: ' años', icon: '👩', accent: '#7c3aed' },
    { title: 'Estancia Hospitalaria', value: kpis.estanciaHospitalaria, suffix: ' días', icon: '🛏️', accent: '#059669' },
    { title: 'Estancia UCI', value: kpis.estanciaUci, suffix: ' días', icon: '💊', accent: '#dc2626' },
  ]

  return (
    <div className="morb-kpi-row">
      {cards.map((c, i) => (
        <div className="morb-kpi-card" key={i} style={{ '--accent': c.accent } as React.CSSProperties}>
          <div className="morb-kpi-header">
            <span className="morb-kpi-title">{c.title}</span>
            <span className="morb-kpi-icon">{c.icon}</span>
          </div>
          <div className="morb-kpi-value">
            {c.value != null ? `${c.value}${c.suffix}` : '—'}
          </div>
        </div>
      ))}
    </div>
  )
}

const FallasOrganicasSection: React.FC<{ fallas: SeveridadFallasData['fallas']; totalCasos: number }> = ({ fallas, totalCasos }) => {
  const sorted = useMemo(() => [...fallas].sort((a, b) => b.casos - a.casos), [fallas])
  const maxCasos = sorted.length > 0 ? sorted[0].casos : 1

  return (
    <div className="morb-fallas-section">
      <div className="morb-fallas-ranking">
        <h3 className="chart-card-title">
          <span>Ranking de Fallas</span>
          <span className="morb-badge-count">{sorted.length} tipos</span>
        </h3>
        <div className="morb-fallas-list">
          {sorted.map((f, i) => {
            const pct = totalCasos > 0 ? ((f.casos / totalCasos) * 100).toFixed(1) : '0'
            const barWidth = maxCasos > 0 ? (f.casos / maxCasos) * 100 : 0
            return (
              <div className="morb-falla-item" key={i} style={{ animationDelay: `${i * 80}ms` }}>
                <div className="morb-falla-info">
                  <span className="morb-falla-rank">#{i + 1}</span>
                  <span className="morb-falla-icon">{getFallaIcon(f.nombre)}</span>
                  <span className="morb-falla-name">{f.nombre.replace(/^Falla\s*/i, '')}</span>
                </div>
                <div className="morb-falla-bar-container">
                  <div
                    className="morb-falla-bar"
                    style={{ width: `${barWidth}%`, animationDelay: `${i * 80 + 200}ms` }}
                  />
                </div>
                <div className="morb-falla-stats">
                  <span className="morb-falla-count">{f.casos}</span>
                  <span className="morb-falla-pct">{pct}%</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

const SeveridadIndicatorsSection: React.FC<{ severidad: SeveridadFallasData['severidad']; totalCasos: number }> = ({ severidad, totalCasos }) => {
  return (
    <div className="morb-severity-cards">
      <h3 className="chart-card-title">
        <span>Indicadores de Severidad</span>
        <span className="morb-badge-severity">Intervenciones</span>
      </h3>
      <div className="morb-severity-grid">
        {severidad.map((s, i) => {
          const meta = SEVERITY_ICONS[s.nombre] || { icon: '⚕️', gradient: 'linear-gradient(135deg, #475569, #1e293b)' }
          const pct = totalCasos > 0 ? ((s.casos / totalCasos) * 100) : 0
          return (
            <div className="morb-severity-card" key={i} style={{ animationDelay: `${i * 120}ms` }}>
              <div className="morb-severity-icon-circle" style={{ background: meta.gradient }}>
                <span>{meta.icon}</span>
              </div>
              <div className="morb-severity-info">
                <span className="morb-severity-name">{s.nombre}</span>
                <div className="morb-severity-progress-track">
                  <div
                    className="morb-severity-progress-fill"
                    style={{
                      width: `${Math.min(pct, 100)}%`,
                      background: meta.gradient,
                      animationDelay: `${i * 120 + 300}ms`,
                    }}
                  />
                </div>
                <div className="morb-severity-numbers">
                  <span className="morb-severity-count">{s.casos} casos</span>
                  <span className="morb-severity-pct">{pct.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

const CriteriosInclusionSection: React.FC<{ criterios: CriterioItem[] }> = ({ criterios }) => {
  const option = useMemo(() => {
    const maxCasos = criterios.length > 0 ? Math.max(...criterios.map((c) => c.casos)) : 1
    return {
      textStyle: echartsBaseTextStyle(),
      grid: { top: 10, left: 140, right: 90, bottom: 20, containLabel: true },
      xAxis: { type: 'value' as const, max: maxCasos * 1.3, splitLine: { lineStyle: { color: '#f1f5f9' } } },
      yAxis: {
        type: 'category' as const,
        data: criterios.map((c) => c.nombre),
        axisLabel: { fontSize: 12, fontWeight: 600 },
      },
      series: [
        {
          type: 'bar' as const,
          data: criterios.map((c) => ({ value: c.casos, itemStyle: { color: CRITERIO_COLORS[c.nombre] || '#6366f1' } })),
          barCategoryGap: '35%',
          label: {
            show: true,
            position: 'right' as const,
            fontSize: 11,
            fontWeight: 700,
            color: '#334155',
            formatter: (params: { dataIndex: number }) => {
              const c = criterios[params.dataIndex]
              return `${c.casos} (${c.porcentaje.toFixed(1)}%)`
            },
          },
        },
      ],
    }
  }, [criterios])

  return (
    <div className="morb-criterios-section">
      <h3 className="chart-card-title">
        <span>Criterios de Inclusión MME</span>
        <span className="morb-badge-criterios">Diagnósticos</span>
      </h3>
      <ReactECharts option={option} style={{ height: '260px', width: '100%' }} notMerge={true} />
    </div>
  )
}

const MomentoOcurrenciaSection: React.FC<{ data: MomentoItem[] }> = ({ data }) => {
  const total = data.reduce((sum, d) => sum + d.count, 0)

  const option = useMemo(
    () => ({
      textStyle: echartsBaseTextStyle(),
      color: MOMENTO_COLORS.slice(0, data.length),
      tooltip: { trigger: 'item' as const, formatter: '{b}<br/>{c} casos ({d}%)' },
      legend: { bottom: 0, textStyle: { fontSize: 10, color: '#475569' } },
      graphic: [
        {
          type: 'text' as const,
          left: 'center' as const,
          top: 'center' as const,
          style: { text: `${total}\ncasos`, textAlign: 'center' as const, fontSize: 22, fontWeight: 700, fill: '#0f172a' },
        },
      ],
      series: [
        {
          type: 'pie' as const,
          radius: ['55%', '80%'],
          center: ['50%', '45%'],
          data: data.map((d) => ({ name: d.label, value: d.count })),
          label: { show: true, position: 'inside' as const, formatter: '{d}%', fontSize: 12, fontWeight: 700, color: '#fff' },
          itemStyle: { borderColor: '#fff', borderWidth: 2 },
        },
      ],
    }),
    [data, total],
  )

  return (
    <div className="morb-momento-section">
      <h3 className="chart-card-title">
        <span>Momento de Ocurrencia</span>
        <span className="morb-badge-momento">Clínico</span>
      </h3>
      <ReactECharts option={option} style={{ height: '280px', width: '100%' }} notMerge={true} />
    </div>
  )
}

const TiempoRemisionSection: React.FC<{ data: TiempoRemision }> = ({ data }) => {
  const option = useMemo(
    () => ({
      textStyle: echartsBaseTextStyle(),
      grid: { top: 20, left: 60, right: 20, bottom: 30 },
      xAxis: { type: 'category' as const, data: ['Tiempo (h)'] },
      yAxis: {
        type: 'value' as const,
        name: 'Horas',
        nameTextStyle: { fontSize: 11, color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      series: [
        {
          type: 'boxplot' as const,
          data: [[data.min, data.q1, data.median, data.q3, data.max]],
          itemStyle: { color: 'rgba(99, 102, 241, 0.15)', borderColor: '#4f46e5' },
        },
      ],
    }),
    [data],
  )

  return (
    <div className="morb-remision-section">
      <h3 className="chart-card-title">
        <span>Tiempo de Remisión</span>
        <span className="morb-badge-remision">Horas</span>
      </h3>
      <ReactECharts option={option} style={{ height: '220px', width: '100%' }} notMerge={true} />
      <div className="morb-remision-stats">
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">Mediana</span>
          <span className="morb-remision-stat-value">{data.median.toFixed(1)}h</span>
        </div>
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">Promedio</span>
          <span className="morb-remision-stat-value">{data.mean.toFixed(1)}h</span>
        </div>
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">Q1–Q3</span>
          <span className="morb-remision-stat-value">{data.q1.toFixed(1)}–{data.q3.toFixed(1)}h</span>
        </div>
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">n</span>
          <span className="morb-remision-stat-value">{data.total}</span>
        </div>
      </div>
    </div>
  )
}

/* ───── Main Component ───── */

export const SeveridadFallasMorbilidad: React.FC<SeveridadFallasMorbilidadProps> = ({
  data,
  morbKpis,
  criteriosInclusion,
  momentoOcurrencia,
  tiempoRemision,
}) => {
  const hasAnyData = (data && (data.fallas.length > 0 || data.severidad.length > 0)) ||
    morbKpis || criteriosInclusion || momentoOcurrencia || tiempoRemision

  if (!hasAnyData) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '60px 40px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.4 }}>🏥</div>
        <h3 className="chart-card-title" style={{ justifyContent: 'center' }}>Análisis de Morbilidad Materna Extrema</h3>
        <p style={{ color: '#64748b', fontSize: '14px', maxWidth: '400px', margin: '0 auto' }}>
          No hay datos suficientes de morbilidad para generar este análisis. Cargue un archivo de evento 549.
        </p>
      </div>
    )
  }

  return (
    <div className="morb-tab-container">
      {morbKpis && <MorbKpiRow kpis={morbKpis} />}

      {data && data.fallas.length > 0 && (
        <FallasOrganicasSection fallas={data.fallas} totalCasos={data.total_casos} />
      )}

      <div className="morb-severity-criterios-row">
        {data && data.severidad.length > 0 && (
          <SeveridadIndicatorsSection severidad={data.severidad} totalCasos={data.total_casos} />
        )}
        {criteriosInclusion && criteriosInclusion.length > 0 && (
          <CriteriosInclusionSection criterios={criteriosInclusion} />
        )}
      </div>

      <div className="morb-momento-remision-row">
        {momentoOcurrencia && momentoOcurrencia.length > 0 && (
          <MomentoOcurrenciaSection data={momentoOcurrencia} />
        )}
        {tiempoRemision && (
          <TiempoRemisionSection data={tiempoRemision} />
        )}
      </div>
    </div>
  )
}
