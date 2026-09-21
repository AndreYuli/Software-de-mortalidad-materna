import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Lock, Mail } from 'lucide-react'
import { API_URL, describeNetworkError, extractErrorMessage, fetchWithTimeout } from '../../api'
import { loginSchema } from '../../validation/loginSchema'
import AuthCard from './AuthCard'
import AuthField from './AuthField'
import AuthNotice from './AuthNotice'
import { authButtonClass, authLinkClass } from './authStyles'

interface LoginProps {
  onLogin?: () => void
  onRegister?: () => void
}
interface LoginResponse {
  access_token: string
  token_type: string
  id: number
  nombre: string
  email: string
  detail?: string
  error?: string
}

export default function Login({ onLogin, onRegister }: LoginProps = {}) {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [infoMsg, setInfoMsg] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ email: string; password: string }>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: { email: string; password: string }) => {
    setError('')
    setInfoMsg('')
    setIsLoading(true)
    try {
      const res = await fetchWithTimeout(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email, password: data.password }),
      })
      // Un proxy/servidor caído puede devolver HTML: no debe verse como "sin conexión".
      const responseData: LoginResponse | null = await res.json().catch(() => null)
      if (!res.ok || !responseData) {
        setError(
          res.status >= 500 || !responseData
            ? 'El servidor no respondió correctamente. Intenta de nuevo en unos minutos.'
            : extractErrorMessage(responseData, 'Correo o contraseña incorrectos.'),
        )
        return
      }
      localStorage.setItem('token', responseData.access_token)
      localStorage.setItem('username', responseData.nombre || 'Usuario')
      localStorage.setItem('user_email', responseData.email || data.email)
      if (onLogin) onLogin()
      else navigate('/dashboard')
    } catch (err) {
      setError(describeNetworkError(err, 'No se pudo conectar al servidor. Verifica que el backend esté activo.'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleForgotPassword = () => {
    setError('')
    setInfoMsg('Estamos trabajando en la recuperación de contraseñas. Por favor, comunícate con el administrador para restablecer tu acceso.')
  }

  return (
    <AuthCard
      title="Inicio de sesión"
      subtitle="Ingresa tus credenciales para acceder a la plataforma de análisis."
      footer={
        <>
          ¿No tienes una cuenta?{' '}
          <button
            type="button"
            className={authLinkClass}
            onClick={() => {
              if (onRegister) onRegister()
              else navigate('/register')
            }}
          >
            Crear cuenta
          </button>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <AuthField
          id="login-email"
          label="Correo electrónico"
          icon={Mail}
          type="email"
          placeholder="tu.correo@institucion.gov.co"
          error={errors.email?.message}
          registration={register('email')}
        />
        <AuthField
          id="login-password"
          label="Contraseña"
          icon={Lock}
          type="password"
          placeholder="••••••••"
          error={errors.password?.message}
          registration={register('password')}
        />

        {error && <AuthNotice variant="error">{error}</AuthNotice>}
        {infoMsg && <AuthNotice variant="info">{infoMsg}</AuthNotice>}

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-slate-600">
            <input type="checkbox" className="size-4 accent-brand-magenta" /> Recordarme
          </label>
          <button type="button" className={authLinkClass} onClick={handleForgotPassword}>
            ¿Olvidaste tu contraseña?
          </button>
        </div>

        <button type="submit" className={authButtonClass} disabled={isLoading}>
          {isLoading && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
          {isLoading ? 'Verificando...' : 'Iniciar sesión'}
        </button>
      </form>
    </AuthCard>
  )
}
