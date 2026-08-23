import React, { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import '../../constants/chartTheme'

/* ───── Types ───── */
export interface AtencionKpis {
  cpnPromedio: number | null
  gestacionesPromedio: number | null
  estanciaHospitalaria: number | null
  estanciaUci: number | null
  totalMort: number
  totalMorb: number
}

export interface InstitucionReferenciaData {
  instituciones: string[]
  conteos: number[]
  con_uci?: number[]
  con_cirugia?: number[]
  totalConDato: number
  totalCasos: number
}

export interface ObstetricoData {
  nombre: string
  valoresEje: number[]
  conteos: number[]
  porEdad: Record<string, number[]>
  promedio: number
  total: number
}

export interface AtencionOportunidadProps {
  kpis: AtencionKpis | null
  institucionReferencia: InstitucionReferenciaData | null
  obstetricoEdad: { label: string; mort: ObstetricoData | null; morb: ObstetricoData | null }[] | null
}

/* ───── Sub-components ───── */

const AtencionKpiRow: React.FC<{ kpis: AtencionKpis }> = ({ kpis }) => {
  const cards = [
    { title: 'Controles Prenatales Prom.', value: kpis.cpnPromedio, suffix: '', icon: '🩺', accent: '#0284c7' },
    { title: 'Gestaciones Promedio', value: kpis.gestacionesPromedio, suffix: '', icon: '🤰', accent: '#c026d3' },
    { title: 'Estancia Hospitalaria (Morbilidad)', value: kpis.estanciaHospitalaria, suffix: ' días', icon: '🛏️', accent: '#059669' },
    { title: 'Estancia UCI (Morbilidad)', value: kpis.estanciaUci, suffix: ' días', icon: '🏥', accent: '#dc2626' },
  ]

  return (
    <div className="atencion-kpi-row">
      {cards.map((c, i) => (
        <div className="atencion-kpi-card" key={i} style={{ '--accent': c.accent } as React.CSSProperties}>
          <div className="atencion-kpi-header">
            <span className="atencion-kpi-title">{c.title}</span>
            <span className="atencion-kpi-icon">{c.icon}</span>
          </div>
          <div className="atencion-kpi-value">
            {c.value != null ? `${c.value}${c.suffix}` : '—'}
          </div>
        </div>
      ))}
    </div>
  )
}

const InstitucionReferenciaSection: React.FC<{ data: InstitucionReferenciaData }> = ({ data }) => {
  const yLabels = useMemo(
    () => data.instituciones.map((inst) => (inst.length > 30 ? inst.substring(0, 27) + '...' : inst)),
    [data.instituciones],
  )

  const datasets = useMemo(() => {
    if (data.con_uci && data.con_cirugia) {
      return [
        { label: 'Total', data: data.conteos, backgroundColor: '#0ea5e9' },
        { label: 'UCI', data: data.con_uci, backgroundColor: '#dc2626' },
        { label: 'Cirugía', data: data.con_cirugia, backgroundColor: '#ea580c' },
      ]
    }
    return [{ label: 'Total Casos', data: data.conteos, backgroundColor: '#0ea5e9' }]
  }, [data])

  return (
    <div className="atencion-instituciones-section">
      <h3 className="chart-card-title">
        <span>Instituciones de Referencia (Morbilidad)</span>
        <span className="atencion-badge-inst">Top 15</span>
      </h3>
      <div style={{ height: `${Math.max(300, data.instituciones.length * 40)}px` }}>
        <Bar
          data={{ labels: yLabels, datasets }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y' as const,
            plugins: { legend: { position: 'bottom' as const } },
            scales: {
              x: { beginAtZero: true, grid: { color: '#f1f5f9' } },
              y: { grid: { display: false } },
            },
          }}
        />
      </div>
      <div className="atencion-instituciones-stats">
        <span className="text-sm text-slate-500">Datos disponibles en {data.totalConDato} de {data.totalCasos} casos de morbilidad.</span>
      </div>
    </div>
  )
}

const ObstetricoEdadSection: React.FC<{ variables: NonNullable<AtencionOportunidadProps['obstetricoEdad']> }> = ({ variables }) => {
  return (
    <div className="atencion-obstetrico-section">
      <h3 className="chart-card-title">
        <span>Variables Obstétricas por Edad</span>
        <span className="atencion-badge-obs">Comparativa</span>
      </h3>

      <div className="atencion-obstetrico-grid">
        {variables.map((v, i) => {
          const labels = (v.mort?.valoresEje ?? v.morb?.valoresEje ?? []).map(String)
          const datasets = []

          if (v.mort) {
            datasets.push({
              label: `Mortalidad (${v.mort.promedio.toFixed(1)} prom)`,
              data: v.mort.conteos,
              backgroundColor: '#ef4444',
            })
          }
          if (v.morb) {
            datasets.push({
              label: `Morbilidad (${v.morb.promedio.toFixed(1)} prom)`,
              data: v.morb.conteos,
              backgroundColor: '#3b82f6',
            })
          }

          return (
            <div key={i} className="atencion-obs-chart-container" style={{ height: '250px' }}>
              <Bar
                data={{ labels, datasets }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    title: { display: true, text: v.label, font: { size: 14 } },
                    legend: { position: 'bottom' as const },
                  },
                  scales: {
                    x: { ticks: { autoSkip: false } },
                  },
                }}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ───── Main Component ───── */

export const AtencionOportunidad: React.FC<AtencionOportunidadProps> = ({
  kpis,
  institucionReferencia,
  obstetricoEdad,
}) => {
  const hasAnyData = kpis || institucionReferencia || obstetricoEdad

  if (!hasAnyData) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '60px 40px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.4 }}>🚑</div>
        <h3 className="chart-card-title" style={{ justifyContent: 'center' }}>Atención y Oportunidad</h3>
        <p style={{ color: '#64748b', fontSize: '14px', maxWidth: '400px', margin: '0 auto' }}>
          No hay datos suficientes para generar este análisis.
        </p>
      </div>
    )
  }

  return (
    <div className="atencion-tab-container">
      {kpis && <AtencionKpiRow kpis={kpis} />}

      <div className="atencion-main-row">
        {institucionReferencia && institucionReferencia.instituciones.length > 0 && (
          <div className="atencion-left-col">
            <InstitucionReferenciaSection data={institucionReferencia} />
          </div>
        )}

        {obstetricoEdad && obstetricoEdad.length > 0 && (
          <div className="atencion-right-col">
            <ObstetricoEdadSection variables={obstetricoEdad} />
          </div>
        )}
      </div>
    </div>
  )
}
