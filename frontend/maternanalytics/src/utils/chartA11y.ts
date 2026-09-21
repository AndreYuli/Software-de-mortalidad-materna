/** Texto para el `aria-label` de un canvas: el título seguido de cada categoría y su valor. */
export function describeSeries(title: string, labels: string[], values: number[]): string {
  const pares = labels.map((label, i) => `${label}: ${values[i] ?? 0}`)
  return pares.length > 0 ? `${title}. ${pares.join('; ')}` : title
}

/** Igual que `describeSeries` para una matriz filas × columnas (cruce de variables). */
export function describeMatrix(title: string, filas: string[], columnas: string[], matriz: number[][]): string {
  const partes = filas.map((fila, i) => {
    const celdas = columnas.map((columna, j) => `${columna}: ${matriz[i]?.[j] ?? 0}`)
    return `${fila} (${celdas.join(', ')})`
  })
  return partes.length > 0 ? `${title}. ${partes.join('; ')}` : title
}
