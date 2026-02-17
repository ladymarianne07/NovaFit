import React, { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { AlertCircle, CheckCircle2, X } from 'lucide-react'

type ToastVariant = 'success' | 'error'

interface ToastItem {
  id: string
  title: string
  message: string
  variant: ToastVariant
}

interface ToastOptions {
  title?: string
  message: string
  variant?: ToastVariant
  duration?: number
}

interface ToastContextType {
  showToast: (options: ToastOptions) => void
  showError: (message: string, title?: string) => void
  showSuccess: (message: string, title?: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

const DEFAULT_DURATION = 4200

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismissToast = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const showToast = useCallback(({ title, message, variant = 'error', duration = DEFAULT_DURATION }: ToastOptions) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

    const toast: ToastItem = {
      id,
      title: title || (variant === 'success' ? '¡Éxito!' : 'Revisa el formulario'),
      message,
      variant
    }

    setToasts((current) => [...current, toast])

    window.setTimeout(() => {
      dismissToast(id)
    }, duration)
  }, [dismissToast])

  const showError = useCallback((message: string, title = 'Ups, algo salió mal') => {
    showToast({ message, title, variant: 'error' })
  }, [showToast])

  const showSuccess = useCallback((message: string, title = '¡Todo listo!') => {
    showToast({ message, title, variant: 'success' })
  }, [showToast])

  const value = useMemo(() => ({ showToast, showError, showSuccess }), [showToast, showError, showSuccess])

  return (
    <ToastContext.Provider value={value}>
      {children}

      <div className="toast-viewport" role="region" aria-live="polite" aria-label="Notificaciones">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`toast-card toast-${toast.variant}`}
            role="alert"
            aria-atomic="true"
          >
            <div className="toast-icon" aria-hidden="true">
              {toast.variant === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            </div>

            <div className="toast-content">
              <p className="toast-title">{toast.title}</p>
              <p className="toast-message">{toast.message}</p>
            </div>

            <button
              type="button"
              onClick={() => dismissToast(toast.id)}
              className="toast-close"
              aria-label="Cerrar notificación"
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => {
  const context = useContext(ToastContext)
  if (!context) {
    return {
      showToast: () => undefined,
      showError: () => undefined,
      showSuccess: () => undefined
    }
  }
  return context
}
