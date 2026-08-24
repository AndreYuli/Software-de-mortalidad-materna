import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'
import { API_URL } from '../api'
import { useForm } from 'react-hook-form'
// Zod schema imported from external file
import { zodResolver } from '@hookform/resolvers/zod'
import LogoIcon from './LogoIcon'
import { loginSchema } from '../validation/loginSchema'

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
      const res = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email, password: data.password }),
      })
      const responseData: LoginResponse = await res.json()
      if (!res.ok) {
        setError(responseData.detail || responseData.error || 'Correo o contraseña incorrectos.')
        return
      }
      localStorage.setItem('token', responseData.access_token)
      localStorage.setItem('username', responseData.nombre || 'Usuario')
      localStorage.setItem('user_email', responseData.email || data.email)
      if (onLogin) onLogin()
      else navigate('/dashboard')
    } catch {
      setError('No se pudo conectar al servidor. Verifica que el backend esté activo.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleForgotPassword = () => {
    setError('')
    setInfoMsg('Estamos trabajando en la recuperación de contraseñas. Por favor, comunícate con el administrador para restablecer tu acceso.')
  }

  return (
    <div className="page">

      {/* LEFT PANEL */}
      <div className="left">
        <div className="blob blob-1" aria-hidden="true"></div>
        <div className="blob blob-2" aria-hidden="true"></div>
        <div className="blob blob-3" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="node" aria-hidden="true"></div>
        <div className="pulse-line" aria-hidden="true"></div>
        <div className="pulse-line" aria-hidden="true"></div>
        <div className="pulse-line" aria-hidden="true"></div>

        <div className="left-content">
          <LogoIcon className="logo-icon" aria-hidden="true" />


          <h1 className="brand-title">Vida<span>Materna</span></h1>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <main className="right">
        <div className="form-container">
          <div className="form-header">
            <h2>Inicio de sesión</h2>
            <p>Ingresa tus credenciales para acceder a la plataforma de análisis.</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="field">
              <label htmlFor="login-email">Correo electrónico</label>
              <input id="login-email"
                type="email"
                placeholder="tu.correo@institucion.gov.co"
                {...register('email')}
                required
              />
              {errors.email && <p className="error-msg">{errors.email.message}</p>}
              <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="2" y="4" width="20" height="16" rx="3" /><path d="M22 4L12 13 2 4" />
              </svg>
            </div>

            <div className="field">
              <label htmlFor="login-password">Contraseña</label>
              <input id="login-password"
                type="password"
                placeholder="••••••••"
                {...register('password')}
                required
              />
              {errors.password && <p className="error-msg">{errors.password.message}</p>}
              <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="3" y="11" width="18" height="11" rx="3" /><path d="M7 11V7a5 5 0 0110 0v4" />
              </svg>
            </div>

            {error && <p className="error-msg">{error}</p>}
            {infoMsg && (
              <div
                style={{
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.25)',
                  color: '#1d4ed8',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  fontSize: '12.5px',
                  lineHeight: '1.4',
                  margin: '8px 0 12px',
                  textAlign: 'left',
                }}
              >
                ℹ️ {infoMsg}
              </div>
            )}

            <div className="field-row">
              <label className="remember">
                <input type="checkbox" /> Recordarme
              </label>
              <button type="button" className="btn-link forgot" onClick={handleForgotPassword}>¿Olvidaste tu contraseña?</button>
            </div>

            <button type="submit" className="btn-login" disabled={isLoading}>
              {isLoading ? 'Verificando...' : 'Iniciar sesión'}
            </button>
          </form>

          <p className="footer-text">
            ¿No tienes una cuenta?{' '}
            <button
              type="button"
              className="btn-link"
              onClick={() => {
                if (onRegister) onRegister()
                else navigate('/register')
              }}
            >
              Crear cuenta
            </button>
          </p>
        </div>


      </main>

    </div>
  )
}
