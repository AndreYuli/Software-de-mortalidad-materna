import { useEffect, useState } from 'react'

/** Devuelve si la consulta CSS (p. ej. `(max-width: 640px)`) se cumple y se actualiza al redimensionar. */
export function useMediaQuery(query: string): boolean {
  const [coincide, setCoincide] = useState(() => window.matchMedia?.(query).matches ?? false)

  useEffect(() => {
    const mql = window.matchMedia?.(query)
    if (!mql) return
    const alCambiar = () => setCoincide(mql.matches)
    alCambiar()
    mql.addEventListener('change', alCambiar)
    return () => mql.removeEventListener('change', alCambiar)
  }, [query])

  return coincide
}
