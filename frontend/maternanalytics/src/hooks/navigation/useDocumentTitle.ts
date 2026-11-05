import { useEffect } from 'react'

const BASE = 'VidaMaterna'

/** Pone "<titulo> · VidaMaterna" como título de la pestaña mientras el componente está montado. */
export function useDocumentTitle(titulo: string) {
  useEffect(() => {
    document.title = `${titulo} · ${BASE}`
    return () => {
      document.title = BASE
    }
  }, [titulo])
}
