import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/auth/Login'
import Register from './components/auth/Register'
import { ProtectedRoute, PublicOnlyRoute } from './components/auth/RouteGuards'
import ErrorBoundary from './components/ErrorBoundary'
import { DashboardViewRoute } from './components/dashboard/DashboardViewRoute'

const DashboardOKD = lazy(() => import('./components/DashboardOKD'))

function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <ErrorBoundary>
        <Suspense fallback={<div>Cargando VidaMaterna...</div>}>
          <Routes>
            <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
            <Route path="/register" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>} />

            {/* DashboardOKD es el layout; las vistas son rutas hijas */}
            <Route element={<ProtectedRoute><DashboardOKD /></ProtectedRoute>}>
              <Route index element={<DashboardViewRoute view="analisis" />} />
              <Route path="dashboard" element={<DashboardViewRoute view="analisis" />} />
              <Route path="cargar-mortalidad" element={<DashboardViewRoute view="mortalidad" />} />
              <Route path="cargar-morbilidad" element={<DashboardViewRoute view="morbilidad" />} />
              <Route path="historial" element={<DashboardViewRoute view="historial" />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App
