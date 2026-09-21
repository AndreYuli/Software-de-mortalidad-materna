export interface CruceLabels {
  /** Título del gráfico: qué variables se están cruzando. */
  title: string
  /** Eje X (valores): qué cuenta la barra. */
  xAxis: string
  /** Eje Y (categorías): la variable sociodemográfica. */
  yAxis: string
  /** Leyenda (series): la variable clínica. */
  legend: string
}

/** Etiquetas del gráfico de cruce según las dos variables seleccionadas (DEC-002). */
export function getCruceLabels(varSocioLabel: string, varClinicaLabel: string): CruceLabels {
  return {
    title: `${varSocioLabel} según ${varClinicaLabel}`,
    xAxis: `Casos — ${varSocioLabel}`,
    yAxis: varSocioLabel,
    legend: varClinicaLabel,
  }
}
