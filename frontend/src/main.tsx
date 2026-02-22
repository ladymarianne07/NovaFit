import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { registerSW } from 'virtual:pwa-register'

const updateSW = registerSW({
  immediate: true,
  onNeedRefresh() {
    // Dispatch event to notify app of update availability
    window.dispatchEvent(new CustomEvent('pwa-update-available'))
  },
})

// Expose updateSW globally for the hook to use if needed
;(window as any).updateSW = updateSW

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)