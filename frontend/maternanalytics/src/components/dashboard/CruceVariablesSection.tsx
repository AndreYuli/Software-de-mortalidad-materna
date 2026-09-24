import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { Scale } from 'chart.js'
import { BAR_STYLE_GROUPED, CATEGORICAL_PALETTE, CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { wrapLabel } from '../../utils/causasChartLabels'
import { calculateGroupedChartHeight, chartHeightClass } from '../../utils/chartHeight'
import { describeMatrix } from '../../utils/chartA11y'
import { getCruceAiInsight } from '../../utils/aiChartInsights'
import { getCruceLabels } from '../../utils/cruceLabels'
import { useCruceVariables } from '../../hooks/dashboard/useCruceVariables'

const LABEL_CLASS = 'mb-1 block text-xs font-medium text-slate-500'
const SELECT_CLASS =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-magenta focus:ring-2 focus:ring-brand-magenta/30'

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

  const formatCruceSerieLabel = (valor: string | number) => `${valor} ${varClinicaLabel}`
  const formatCruceTooltipLabel = (valor: string | number, casos: number) => `${casos} casos con ${valor} ${varClinicaLabel}`

  return (
    <ChartCard
      title={`Cruce de Variables (${evento})`}
      description="Compare una variable sociodemográfica con una clínica para identificar combinaciones de mayor riesgo."
      insight={!loading && !error && data && data.total > 0 ? insight : null}
    >
      <div className="mb-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label className={LABEL_CLASS} htmlFor={`cruce-socio-${evento}`}>
            Variable sociodemográfica
          </label>
          <select
            id={`cruce-socio-${evento}`}
            className={SELECT_CLASS}
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

        <div>
          <label className={LABEL_CLASS} htmlFor={`cruce-clinica-${evento}`}>
            Variable clínica
          </label>
          <select
            id={`cruce-clinica-${evento}`}
            className={SELECT_CLASS}
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

      {loading && (
        <p role="status" className="text-sm text-slate-500">
          Calculando cruce…
        </p>
      )}

      {!loading && error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}

      {!loading && !error && (!data || data.total === 0) && (
        <p className="text-sm text-slate-500">
          No hay suficientes datos con ambas variables registradas para este cruce.
        </p>
      )}

      {!loading && !error && data && data.total > 0 && (
        <div className={chartHeightClass(calculateGroupedChartHeight(data.categorias_socio, data.categorias_clinica.length))}>
          <Bar
            role="img"
            aria-label={describeMatrix(labels.title, data.categorias_socio, data.categorias_clinica, data.matriz)}
            data={{
              labels: data.categorias_socio.map((l) => wrapLabel(l)),
              datasets: data.categorias_clinica.map((cat, j) => ({
                label: formatCruceSerieLabel(cat),
                data: data.categorias_socio.map((_, i) => data.matriz[i][j]),
                backgroundColor: CATEGORICAL_PALETTE[j % CATEGORICAL_PALETTE.length],
                ...BAR_STYLE_GROUPED,
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
                  labels: {
                    font: { family: CHART_FONT_FAMILY },
                    generateLabels(chart) {
                      return chart.data.datasets.map((dataset, index) => ({
                        text: dataset.label ?? String(index),
                        fillStyle: Array.isArray(dataset.backgroundColor)
                          ? dataset.backgroundColor[index % dataset.backgroundColor.length]
                          : dataset.backgroundColor,
                        strokeStyle: Array.isArray(dataset.backgroundColor)
                          ? dataset.backgroundColor[index % dataset.backgroundColor.length]
                          : dataset.backgroundColor,
                        lineWidth: 0,
                        datasetIndex: index,
                        hidden: false,
                        index,
                      }))
                    },
                  },
                },
                tooltip: {
                  callbacks: {
                    label(context) {
                      const valor = context.parsed.x ?? context.parsed.y ?? 0
                      const categoria = context.dataset.label ?? context.label ?? ''
                      const labelBase = categoria.replace(new RegExp(`\\s*${varClinicaLabel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`), '')
                      return formatCruceTooltipLabel(labelBase, valor)
                    },
                  },
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
      )}
    </ChartCard>
  )
}
