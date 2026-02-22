import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastProvider } from './contexts/ToastContext'
import { usePWAUpdate } from './hooks/usePWAUpdate'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import './styles/globals.css'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="login-container">
        <div className="login-content">
          <div className="loading-stack text-center">
            <div className="neon-loader neon-loader--lg" aria-hidden="true"></div>
            <p className="text-white text-sm">Cargando...</p>
          </div>
        </div>
      </div>
    )
  }
  
  return user ? <>{children}</> : <Navigate to="/login" />
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="login-container">
        <div className="login-content">
          <div className="loading-stack text-center">
            <div className="neon-loader neon-loader--lg" aria-hidden="true"></div>
            <p className="text-white text-sm">Cargando...</p>
          </div>
        </div>
      </div>
    )
  }
  
  return !user ? <>{children}</> : <Navigate to="/dashboard" />
}

function AppContent() {
  // Initialize PWA update listener
  usePWAUpdate()

  return (
    <Router>
      <div className="min-h-screen">
        <Routes>
          <Route 
            path="/login" 
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } 
          />
          <Route 
            path="/register" 
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App