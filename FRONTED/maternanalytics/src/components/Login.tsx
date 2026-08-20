import { useState, FormEvent } from 'react'
import './Login.css'
import { API_URL } from '../api'

interface LoginProps {
  onLogin: () => void
  onRegister: () => void
}

export default function Login({ onLogin, onRegister }: LoginProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Correo o contraseña incorrectos.')
        return
      }
      localStorage.setItem('username', data.nombre)
      localStorage.setItem('user_email', data.email)
      onLogin()
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
            <h2>Inicio de sesión</h2>
            <p>Ingresa tus credenciales para acceder a la plataforma de análisis.</p>
          </div>

          <form onSubmit={handleLogin}>
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
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="3"/><path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
            </div>

            {error && <p className="error-msg">{error}</p>}

            <div className="field-row">
              <label className="remember">
                <input type="checkbox" /> Recordarme
              </label>
              <a href="#" className="forgot">¿Olvidaste tu contraseña?</a>
            </div>

            <button type="submit" className="btn-login" disabled={isLoading}>
              {isLoading ? 'Verificando...' : 'Iniciar sesión'}
            </button>
          </form>

          <p className="footer-text">
            ¿No tienes una cuenta?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); onRegister() }}>Crear cuenta</a>
          </p>
        </div>


      </div>

    </div>
  )
}
