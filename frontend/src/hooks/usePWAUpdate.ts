import { useEffect } from 'react'
import { useToast } from '../contexts/ToastContext'

export const usePWAUpdate = () => {
  const { showToast } = useToast()

  useEffect(() => {
    const handlePWAUpdate = () => {
      showToast({
        title: '¡Nueva versión disponible!',
        message: 'Toca para actualizar y disfrutar de las mejoras',
        variant: 'success',
        duration: 0 // Persistent until user acts
      })

      // Reload page to activate new SW
      const updateSW = (window as any).updateSW
      if (updateSW && typeof updateSW === 'function') {
        setTimeout(() => {
          updateSW()
          // Force reload after a short delay to ensure new SW is activated
          window.location.reload()
        }, 1000)
      }
    }

    // Listen for the custom PWA update event
    window.addEventListener('pwa-update-available', handlePWAUpdate)

    return () => {
      window.removeEventListener('pwa-update-available', handlePWAUpdate)
    }
  }, [showToast])
}

