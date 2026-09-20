import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import Register from './components/Register'
import ErrorBoundary from './components/ErrorBoundary'

const DashboardOKD = lazy(() => import('./components/DashboardOKD'))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const hasSession = Boolean(localStorage.getItem('token'))
  if (!hasSession) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const hasSession = Boolean(localStorage.getItem('token'))
  if (hasSession) {
    return <Navigate to="/dashboard" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
      <Suspense
        fallback={
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100vh',
              fontFamily: 'sans-serif',
              color: '#64748b',
            }}
          >
            Cargando VidaMaterna...
          </div>
        }
      >
        <Routes>
          {/* Rutas Públicas */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicOnlyRoute>
                <Register />
              </PublicOnlyRoute>
            }
          />

          {/* Rutas Protegidas del Dashboard */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardOKD />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardOKD />
              </ProtectedRoute>
            }
          />
          <Route
            path="/cargar-mortalidad"
            element={
              <ProtectedRoute>
                <DashboardOKD />
              </ProtectedRoute>
            }
          />
          <Route
            path="/cargar-morbilidad"
            element={
              <ProtectedRoute>
                <DashboardOKD />
              </ProtectedRoute>
            }
          />
          <Route
            path="/historial"
            element={
              <ProtectedRoute>
                <DashboardOKD />
              </ProtectedRoute>
            }
          />

          {/* Redirección ante ruta desconocida */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App
