import { useState } from 'react'
import './Login.css'

const API_URL = 'http://localhost:8000/api'

export default function Register({ onRegistered, onBack }) {
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.')
      return
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.')
      return
    }

    setIsLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Error al crear la cuenta.')
        return
      }
      setSuccess(true)
      setTimeout(() => onRegistered(), 1800)
    } catch {
      setError('No se pudo conectar al servidor. Verifica que el backend esté activo.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="page">

      {/* LEFT PANEL */}
      <div className="left">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="pulse-line"></div>
        <div className="pulse-line"></div>
        <div className="pulse-line"></div>

        <div className="left-content">
          <div className="logo-icon">
            <svg width="90" height="90" viewBox="0 0 64 64">
              <path d="M32 4 C52 4 58 20 58 34 C58 52 46 60 32 60 C18 60 6 52 6 34 C6 20 12 4 32 4Z" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.35)" strokeWidth="1.2"/>
              <path d="M26 16 C18 24 16 34 22 44 C26 48 30 52 32 54" fill="none" stroke="#F4C0D1" strokeWidth="2" strokeLinecap="round"/>
              <path d="M38 14 C46 22 48 34 42 44 C38 48 34 52 32 54" fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="32" cy="36" r="5" fill="none" stroke="#F4C0D1" strokeWidth="1.2"/>
              <circle cx="32" cy="36" r="1.8" fill="#F4C0D1"/>
              <circle cx="20" cy="26" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="17" cy="36" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="20" cy="44" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="44" cy="24" r="1.5" fill="rgba(255,255,255,0.25)"/>
              <circle cx="47" cy="34" r="1.5" fill="rgba(255,255,255,0.25)"/>
              <circle cx="44" cy="44" r="1.5" fill="rgba(255,255,255,0.25)"/>
            </svg>
          </div>
          <h1 className="brand-title">Vida<span>Materna</span></h1>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="right">
        <div className="form-container">
          <div className="form-header">
            <h2>Crear cuenta</h2>
            <p>Completa los datos para registrarte en la plataforma de análisis.</p>
          </div>

          {success ? (
            <div className="register-success">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <p>¡Cuenta creada exitosamente! Redirigiendo al inicio de sesión...</p>
            </div>
          ) : (
            <form onSubmit={handleRegister}>
              <div className="field">
                <label>Nombre completo</label>
                <input
                  type="text"
                  placeholder="Tu nombre y apellido"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
              </div>

              <div className="field">
                <label>Correo electrónico</label>
                <input
                  type="email"
                  placeholder="tu.correo@institucion.gov.co"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="3"/><path d="M22 4L12 13 2 4"/>
                </svg>
              </div>

              <div className="field">
                <label>Contraseña</label>
                <input
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="3"/><path d="M7 11V7a5 5 0 0110 0v4"/>
                </svg>
              </div>

              <div className="field">
                <label>Confirmar contraseña</label>
                <input
                  type="password"
                  placeholder="Repite tu contraseña"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>

              {error && <p className="error-msg">{error}</p>}

              <button type="submit" className="btn-login" disabled={isLoading}>
                {isLoading ? 'Creando cuenta...' : 'Crear cuenta'}
              </button>
            </form>
          )}

          <p className="footer-text">
            ¿Ya tienes una cuenta?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); onBack() }}>Iniciar sesión</a>
          </p>
        </div>
      </div>

    </div>
  )
}
