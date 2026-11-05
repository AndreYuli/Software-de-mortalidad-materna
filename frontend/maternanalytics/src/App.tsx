import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute, PublicOnlyRoute } from "./components/auth/RouteGuards";
import ErrorBoundary from "./components/ErrorBoundary";
import { DashboardViewRoute } from "./components/dashboard/DashboardViewRoute";
import { PageSkeleton } from "./components/dashboard/PageSkeleton";

const Login = lazy(() => import("./components/auth/Login"));
const Register = lazy(() => import("./components/auth/Register"));
const DashboardOKD = lazy(() => import("./components/DashboardOKD"));

function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <ErrorBoundary>
        <Suspense fallback={<PageSkeleton />}>
          <Routes>
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

            {/* DashboardOKD es el layout; las vistas son rutas hijas */}
            <Route
              element={
                <ProtectedRoute>
                  <DashboardOKD />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardViewRoute view="analisis" />} />
              <Route
                path="dashboard"
                element={<DashboardViewRoute view="analisis" />}
              />
              <Route
                path="cargar-mortalidad"
                element={<DashboardViewRoute view="mortalidad" />}
              />
              <Route
                path="cargar-morbilidad"
                element={<DashboardViewRoute view="morbilidad" />}
              />
              <Route
                path="historial"
                element={<DashboardViewRoute view="historial" />}
              />
              <Route
                path="contexto"
                element={<DashboardViewRoute view="contexto" />}
              />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
