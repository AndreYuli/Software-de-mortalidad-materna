import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Lock, Mail, User } from 'lucide-react'
import { API_URL, describeNetworkError, extractErrorMessage, fetchWithTimeout } from '../../api'
import { registerSchema, type RegisterFormValues } from '../../validation/registerSchema'
import AuthCard from './AuthCard'
import AuthField from './AuthField'
import AuthNotice from './AuthNotice'
import { authButtonClass, authLinkClass } from './authStyles'

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
    <AuthCard
      title="Crear cuenta"
      subtitle="Completa los datos para registrarte en la plataforma de análisis."
      footer={
        <>
          ¿Ya tienes una cuenta?{' '}
          <button
            type="button"
            className={authLinkClass}
            onClick={() => {
              if (onBack) onBack()
              else navigate('/login')
            }}
          >
            Iniciar sesión
          </button>
        </>
      }
    >
      {success ? (
        <AuthNotice variant="success">
          ¡Cuenta creada exitosamente! Redirigiendo al inicio de sesión...
        </AuthNotice>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <AuthField
            id="nombre"
            label="Nombre completo"
            icon={User}
            placeholder="Tu nombre y apellido"
            error={errors.nombre?.message}
            registration={register('nombre')}
          />
          <AuthField
            id="email"
            label="Correo electrónico"
            icon={Mail}
            type="email"
            placeholder="tu.correo@institucion.gov.co"
            error={errors.email?.message}
            registration={register('email')}
          />
          <AuthField
            id="password"
            label="Contraseña"
            icon={Lock}
            type="password"
            placeholder="Mínimo 6 caracteres"
            error={errors.password?.message}
            registration={register('password')}
          />
          <AuthField
            id="confirmPassword"
            label="Confirmar contraseña"
            icon={Lock}
            type="password"
            placeholder="Repite tu contraseña"
            error={errors.confirmPassword?.message}
            registration={register('confirmPassword')}
          />

          {error && <AuthNotice variant="error">{error}</AuthNotice>}

          <button type="submit" className={authButtonClass} disabled={isLoading}>
            {isLoading && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
            {isLoading ? 'Creando cuenta...' : 'Crear cuenta'}
          </button>
        </form>
      )}
    </AuthCard>
  )
}
