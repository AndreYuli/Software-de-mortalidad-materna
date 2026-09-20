import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'
import { API_URL, describeNetworkError, extractErrorMessage, fetchWithTimeout } from '../../api'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { LogoIcon } from '../icons'
import { registerSchema, type RegisterFormValues } from '../../validation/registerSchema'

interface RegisterProps {
  onRegistered?: () => void
  onBack?: () => void
}

interface RegisterResponse {
  detail?: string
  error?: string
}

export default function Register({ onRegistered, onBack }: RegisterProps = {}) {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormValues) => {
    setError('')
    setIsLoading(true)
    try {
      const res = await fetchWithTimeout(`${API_URL}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: data.nombre, email: data.email, password: data.password }),
      })
      const responseData: RegisterResponse | null = await res.json().catch(() => null)
      if (!res.ok) {
        setError(extractErrorMessage(responseData, 'Error al crear la cuenta.'))
        return
      }
      setSuccess(true)
      setTimeout(() => {
        if (onRegistered) onRegistered()
        else navigate('/login')
      }, 1500)
    } catch (err) {
      setError(describeNetworkError(err, 'No se pudo conectar al servidor. Verifica que el backend esté activo.'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="login-page">

      {/* LEFT PANEL */}
      <div className="login-left" aria-hidden="true">
        <div className="background-decorations">
          <div className="login-blob login-blob-1"></div>
          <div className="login-blob login-blob-2"></div>
          <div className="login-blob login-blob-3"></div>
        </div>

        <div className="login-left-content">
          <LogoIcon className="login-logo-icon" />
          <h1 className="login-brand-title">Vida<span>Materna</span></h1>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="login-right">
        <div className="login-form-container">
          <div className="login-form-header">
            <h2>Crear cuenta</h2>
            <p>Completa los datos para registrarte en la plataforma de análisis.</p>
          </div>

          {success ? (
            <div className="login-register-success">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <p>¡Cuenta creada exitosamente! Redirigiendo al inicio de sesión...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)}>
              <div className="login-field">
                <label htmlFor="nombre">Nombre completo</label>
                <input
                  id="nombre"
                  type="text"
                  placeholder="Tu nombre y apellido"
                  {...register('nombre')}
                  required
                />
                {errors.nombre && <p className="login-error-msg">{errors.nombre.message}</p>}
                <svg className="login-field-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
              </div>

              <div className="login-field">
                <label htmlFor="email">Correo electrónico</label>
                <input
                  id="email"
                  type="email"
                  placeholder="tu.correo@institucion.gov.co"
                  {...register('email')}
                  required
                />
                {errors.email && <p className="login-error-msg">{errors.email.message}</p>}
                <svg className="login-field-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="3"/><path d="M22 4L12 13 2 4"/>
                </svg>
              </div>

              <div className="login-field">
                <label htmlFor="password">Contraseña</label>
                <input
                  id="password"
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  {...register('password')}
                  required
                />
                {errors.password && <p className="login-error-msg">{errors.password.message}</p>}
                <svg className="login-field-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="3"/><path d="M7 11V7a5 5 0 0110 0v4"/>
                </svg>
              </div>

              <div className="login-field">
                <label htmlFor="confirmPassword">Confirmar contraseña</label>
                <input
                  id="confirmPassword"
                  type="password"
                  placeholder="Repite tu contraseña"
                  {...register('confirmPassword')}
                  required
                />
                {errors.confirmPassword && <p className="login-error-msg">{errors.confirmPassword.message}</p>}
                <svg className="login-field-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>

              {error && <p className="login-error-msg">{error}</p>}

              <button type="submit" className="login-btn-login" disabled={isLoading}>
                {isLoading ? 'Creando cuenta...' : 'Crear cuenta'}
              </button>
            </form>
          )}

          <p className="login-footer-text">
            ¿Ya tienes una cuenta?{' '}
            <button
              type="button"
              className="login-btn-link"
              onClick={() => {
                if (onBack) onBack()
                else navigate('/login')
              }}
            >
              Iniciar sesión
            </button>
          </p>
        </div>
      </div>

    </div>
  )
}
