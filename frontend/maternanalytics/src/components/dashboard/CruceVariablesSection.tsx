import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { Scale } from 'chart.js'
import { CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { wrapLabel } from '../../utils/causasChartLabels'
import { getCruceAiInsight } from '../../utils/aiChartInsights'
import { getCruceLabels } from '../../utils/cruceLabels'
import { useCruceVariables } from '../../hooks/dashboard/useCruceVariables'

const CRUCE_PALETTE = ['#6366f1', '#f472b6', '#34d399', '#fbbf24', '#38bdf8', '#fb923c', '#a78bfa', '#f87171']

const VARIABLES_SOCIO = [
  { key: 'zona_residencia', label: 'Zona de residencia' },
  { key: 'poblacion_vulnerable', label: 'Población vulnerable' },
  { key: 'etnia', label: 'Etnia' },
  { key: 'tipo_afiliacion', label: 'Tipo de afiliación' },
]

const VARIABLES_CLINICAS_MORTALIDAD = [
  { key: 'gestaciones', label: 'N° de gestaciones' },
  { key: 'partos_vaginales', label: 'Partos vaginales' },
  { key: 'cesareas', label: 'Cesáreas' },
  { key: 'tipo_parto', label: 'Tipo de parto' },
  { key: 'semana_gestacion_muerte', label: 'Semana de gestación (al momento del evento)' },
]

const VARIABLES_CLINICAS_MORBILIDAD = [
  { key: 'num_gestaciones', label: 'N° de gestaciones' },
  { key: 'partos_vaginales', label: 'Partos vaginales' },
  { key: 'cesareas', label: 'Cesáreas' },
  { key: 'terminacion_gestacion', label: 'Terminación de la gestación' },
  { key: 'edad_gestacional_sem', label: 'Edad gestacional (semanas)' },
  { key: 'falla_hepatica', label: 'Falla hepática' },
  { key: 'falla_renal', label: 'Falla renal' },
  { key: 'falla_coagulacion', label: 'Falla de coagulación' },
]

export interface CruceVariablesSectionProps {
  analisisId: number | null
  evento: 'Mortalidad' | 'Morbilidad'
}

export function CruceVariablesSection({ analisisId, evento }: CruceVariablesSectionProps) {
  const variablesClinicas = evento === 'Mortalidad' ? VARIABLES_CLINICAS_MORTALIDAD : VARIABLES_CLINICAS_MORBILIDAD

  const { varSocio, varClinica, setVarSocio, setVarClinica, data, loading, error } = useCruceVariables(
    analisisId,
    VARIABLES_SOCIO[0].key,
    variablesClinicas[0].key,
  )

  const varSocioLabel = VARIABLES_SOCIO.find((v) => v.key === varSocio)?.label ?? varSocio
  const varClinicaLabel = variablesClinicas.find((v) => v.key === varClinica)?.label ?? varClinica

  const insight = useMemo(
    () => getCruceAiInsight(data ?? undefined, varSocioLabel, varClinicaLabel),
    [data, varSocioLabel, varClinicaLabel],
  )

  const labels = useMemo(() => getCruceLabels(varSocioLabel, varClinicaLabel), [varSocioLabel, varClinicaLabel])

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Cruce de Variables ({evento})</h3>
      <p>
        Compare una variable sociodemográfica con una clínica para identificar combinaciones de mayor riesgo.
      </p>

      <div>
        <div>
          <label className="field-label" htmlFor={`cruce-socio-${evento}`}>
            Variable sociodemográfica
          </label>
          <div className="custom-select-wrapper">
            <select
              id={`cruce-socio-${evento}`}
              className="sidebar-select"
              value={varSocio}
              onChange={(e) => setVarSocio(e.target.value)}
            >
              {VARIABLES_SOCIO.map((v) => (
                <option key={v.key} value={v.key}>
                  {v.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="field-label" htmlFor={`cruce-clinica-${evento}`}>
            Variable clínica
          </label>
          <div className="custom-select-wrapper">
            <select
              id={`cruce-clinica-${evento}`}
              className="sidebar-select"
              value={varClinica}
              onChange={(e) => setVarClinica(e.target.value)}
            >
              {variablesClinicas.map((v) => (
                <option key={v.key} value={v.key}>
                  {v.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && <p>Calculando cruce…</p>}

      {!loading && error && <p>{error}</p>}

      {!loading && !error && (!data || data.total === 0) && (
        <p>
          No hay suficientes datos con ambas variables registradas para este cruce.
        </p>
      )}

      {!loading && !error && data && data.total > 0 && (
        <>
          <div>
            <Bar
              data={{
                labels: data.categorias_socio.map((l) => wrapLabel(l)),
                datasets: data.categorias_clinica.map((cat, j) => ({
                  label: cat,
                  data: data.categorias_socio.map((_, i) => data.matriz[i][j]),
                  backgroundColor: CRUCE_PALETTE[j % CRUCE_PALETTE.length],
                  borderColor: '#475569',
                  borderWidth: 1,
                })),
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y' as const,
                plugins: {
                  title: { display: true, text: labels.title, font: { family: CHART_FONT_FAMILY } },
                  legend: {
                    display: true,
                    position: 'bottom',
                    title: { display: true, text: labels.legend, font: { family: CHART_FONT_FAMILY } },
                    labels: { font: { family: CHART_FONT_FAMILY } },
                  },
                },
                scales: {
                  x: {
                    title: { display: true, text: labels.xAxis, font: { family: CHART_FONT_FAMILY } },
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: 'rgba(0,0,0,0.05)' },
                  },
                  y: {
                    title: { display: true, text: labels.yAxis, font: { family: CHART_FONT_FAMILY } },
                    grid: { display: false },
                    afterFit: (scale: Scale) => {
                      scale.width += 70
                    },
                  },
                },
              }}
            />
          </div>
          <ChartAiInsight insight={insight} />
        </>
      )}
    </div>
  )
}
