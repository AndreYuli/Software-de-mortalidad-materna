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
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          height: '100vh',
          fontFamily: 'sans-serif',
          color: '#334155',
          textAlign: 'center',
          padding: '0 16px',
        }}
      >
        <h1 style={{ fontSize: '20px' }}>Algo salió mal</h1>
        <p>Ocurrió un error inesperado al mostrar esta pantalla.</p>
        <button type="button" onClick={() => window.location.assign('/')}>
          Volver al inicio
        </button>
      </div>
    )
  }
}
