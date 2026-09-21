import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

const hasSession = () => Boolean(localStorage.getItem('token'))

export function ProtectedRoute({ children }: { children: ReactNode }) {
  return hasSession() ? <>{children}</> : <Navigate to="/login" replace />
}

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  return hasSession() ? <Navigate to="/dashboard" replace /> : <>{children}</>
}
