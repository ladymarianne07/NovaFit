import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, Zap } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { ValidationService } from '../services/validation'
import { requiredFieldMessage, translateValidationMessage } from '../services/validationMessages'

const Login: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({})

  const { login } = useAuth()
  const { showError, showSuccess } = useToast()

  const validateFields = () => {
    const nextErrors: { email?: string; password?: string } = {}

    if (!email.trim()) {
      nextErrors.email = requiredFieldMessage('El correo electrónico')
    } else {
      const emailResult = ValidationService.validateEmail(email)
      if (!emailResult.isValid) {
        nextErrors.email = translateValidationMessage(emailResult.error)
      }
    }

    if (!password.trim()) {
      nextErrors.password = requiredFieldMessage('La contraseña')
    }

    setFieldErrors(nextErrors)

    const firstError = nextErrors.email || nextErrors.password
    if (firstError) {
      showError(firstError, 'Revisa los datos del login')
      return false
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateFields()) {
      return
    }

    setIsLoading(true)

    try {
      await login({
        email,
        password
      })
      showSuccess('Has iniciado sesión correctamente', '¡Bienvenido de nuevo!')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      const message = typeof detail === 'string'
        ? translateValidationMessage(detail)
        : 'No pudimos iniciar sesión. Verifica tus credenciales e inténtalo nuevamente.'

      setFieldErrors({
        email: 'Revisa tu correo electrónico',
        password: 'Revisa tu contraseña'
      })

      showError(message, 'Error de autenticación')
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
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (fieldErrors.email) {
                    setFieldErrors((prev) => ({ ...prev, email: undefined }))
                  }
                }}
                placeholder="Ingresa tu correo electrónico"
                className={`login-input ${fieldErrors.email ? 'error' : ''}`}
                aria-invalid={Boolean(fieldErrors.email)}
                required
                disabled={isLoading}
              />
            </div>
            {fieldErrors.email && <span className="login-field-error">{fieldErrors.email}</span>}
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
                onChange={(e) => {
                  setPassword(e.target.value)
                  if (fieldErrors.password) {
                    setFieldErrors((prev) => ({ ...prev, password: undefined }))
                  }
                }}
                placeholder="Ingresa tu contraseña"
                className={`login-input ${fieldErrors.password ? 'error' : ''}`}
                aria-invalid={Boolean(fieldErrors.password)}
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
            {fieldErrors.password && <span className="login-field-error">{fieldErrors.password}</span>}
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="login-button"
          >
            {isLoading ? (
              <>
                <span className="neon-loader neon-loader--sm" aria-hidden="true"></span>
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