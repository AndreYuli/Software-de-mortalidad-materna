// Tailwind no puede generar una clase a partir de un número calculado: se usa una tabla de
// clases literales (para que el escaneo las encuentre) y se elige el primer paso que cubre la altura.
const HEIGHT_STEPS: { px: number; className: string }[] = [
  { px: 320, className: 'h-80' },
  { px: 400, className: 'h-[400px]' },
  { px: 480, className: 'h-[480px]' },
  { px: 560, className: 'h-[560px]' },
  { px: 640, className: 'h-[640px]' },
  { px: 720, className: 'h-[720px]' },
  { px: 800, className: 'h-[800px]' },
  { px: 880, className: 'h-[880px]' },
  { px: 960, className: 'h-[960px]' },
  { px: 1040, className: 'h-[1040px]' },
  { px: 1120, className: 'h-[1120px]' },
  { px: 1200, className: 'h-[1200px]' },
  { px: 1280, className: 'h-[1280px]' },
]

/** Altura fija de las gráficas de edad (pocas barras verticales). */
export const CHART_HEIGHT_FIXED = 'h-[280px]'

/** Clase de altura para una gráfica que necesita `pixels` px; por encima del máximo devuelve el máximo. */
export function chartHeightClass(pixels: number): string {
  const step = HEIGHT_STEPS.find((s) => s.px >= pixels)
  return (step ?? HEIGHT_STEPS[HEIGHT_STEPS.length - 1]).className
}
