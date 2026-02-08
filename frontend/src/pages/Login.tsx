import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, Zap } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const Login: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      await login({
        username: email, // Backend expects 'username' field
        password
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="login-container">
      {/* Logo */}
      <div className="login-logo">
        <Zap className="w-8 h-8 text-white" />
      </div>

      {/* Main Content */}
      <div className="login-content">
        {/* Header */}
        <div className="login-header">
          <h1 className="login-title"> 
            <span className="login-title-brand">NovaFitness</span>
          </h1>
          <p className="login-subtitle">
            Transforma tu camino hacia una vida más saludable
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="login-error">
              <p className="text-red-300 text-sm text-center">{error}</p>
            </div>
          )}

          {/* Email Field */}
          <div className="login-field">
            <label htmlFor="email" className="login-label">
              Dirección de correo electrónico
            </label>
            <div className="login-input-container">
              <Mail className="login-input-icon" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="login-input"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Password Field */}
          <div className="login-field">
            <label htmlFor="password" className="login-label">
              Contraseña
            </label>
            <div className="login-input-container">
              <Lock className="login-input-icon" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="login-input"
                required
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="login-password-toggle"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="login-button"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Iniciando sesión...
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                Iniciar sesión
              </>
            )}
          </button>

          {/* Register Link */}
          <div className="login-register">
            <p className="login-register-text">
              ¿No tienes una cuenta?{' '}
              <Link
                to="/register"
                className="login-register-link"
              >
                Crea una ahora
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login