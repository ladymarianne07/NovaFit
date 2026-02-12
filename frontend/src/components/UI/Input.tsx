import React, { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  icon?: React.ReactNode
  error?: string
  showPasswordToggle?: boolean
}

export const Input: React.FC<InputProps> = ({
  label,
  icon,
  error,
  showPasswordToggle = false,
  type = 'text',
  required = false,
  className = '',
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false)
  
  const inputType = showPasswordToggle && showPassword ? 'text' : type
  const isPasswordField = type === 'password' && showPasswordToggle

  return (
    <div className="login-field">
      <label htmlFor={props.id || label.toLowerCase().replace(/\s+/g, '-')} className="login-label">
        {label}{required && ' *'}
      </label>
      
      <div className="login-input-container">
        {icon && <div className="login-input-icon">{icon}</div>}
        
        <input
          id={props.id || label.toLowerCase().replace(/\s+/g, '-')}
          type={inputType}
          className={`login-input ${className}`}
          {...props}
        />
        
        {isPasswordField && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="login-password-toggle"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            tabIndex={0}
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        )}
      </div>
      
      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}