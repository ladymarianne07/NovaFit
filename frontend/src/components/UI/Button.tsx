import React from 'react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost'
  isLoading?: boolean
  icon?: React.ReactNode
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  isLoading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const getVariantClass = () => {
    switch (variant) {
      case 'primary':
        return 'login-button' // Use glassmorphism style from Login
      case 'secondary':
        return 'btn-secondary'
      case 'ghost':
        return 'btn-ghost'
      default:
        return 'login-button'
    }
  }

  const isDisabled = disabled || isLoading

  return (
    <button
      className={`btn ${getVariantClass()} ${className}`}
      disabled={isDisabled}
      {...props}
    >
      {isLoading ? (
        <>
          <span className="neon-loader neon-loader--sm" aria-hidden="true"></span>
          Processing...
        </>
      ) : (
        <>
          {icon && icon}
          {children}
        </>
      )}
    </button>
  )
}