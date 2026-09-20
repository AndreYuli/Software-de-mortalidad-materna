import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/auth/Login'
import Register from './components/auth/Register'
import ErrorBoundary from './components/ErrorBoundary'
import { DashboardViewRoute } from './components/dashboard/DashboardViewRoute'

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

          {/* Rutas Protegidas: DashboardOKD es el layout; las vistas son rutas hijas */}
          <Route
            element={
              <ProtectedRoute>
                <DashboardOKD />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardViewRoute view="analisis" />} />
            <Route path="dashboard" element={<DashboardViewRoute view="analisis" />} />
            <Route path="cargar-mortalidad" element={<DashboardViewRoute view="mortalidad" />} />
            <Route path="cargar-morbilidad" element={<DashboardViewRoute view="morbilidad" />} />
            <Route path="historial" element={<DashboardViewRoute view="historial" />} />
          </Route>

          {/* Redirección ante ruta desconocida */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App
