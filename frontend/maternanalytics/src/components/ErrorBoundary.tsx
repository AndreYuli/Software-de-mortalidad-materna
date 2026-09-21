import { Component, type ErrorInfo, type ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

/**
 * Evita la pantalla en blanco: si un componente lanza durante el render
 * se muestra un mensaje con opción de recargar.
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Error de renderizado no controlado:', error, info.componentStack)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <div
        role="alert"

      >
        <h1>Algo salió mal</h1>
        <p>Ocurrió un error inesperado al mostrar esta pantalla.</p>
        <button type="button" onClick={() => window.location.assign('/')}>
          Volver al inicio
        </button>
      </div>
    )
  }
}
