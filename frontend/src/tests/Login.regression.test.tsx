import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'
import { AuthProvider } from '../contexts/AuthContext'

// Mock fetch for API calls
global.fetch = jest.fn()

const mockLogin = jest.fn()
const mockShowError = jest.fn()
const mockShowSuccess = jest.fn()

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    user: null,
    token: null,
    loading: false,
    logout: jest.fn()
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}))

jest.mock('../contexts/ToastContext', () => ({
  useToast: () => ({
    showError: mockShowError,
    showSuccess: mockShowSuccess,
    showToast: jest.fn()
  })
}))

const LoginWrapper: React.FC = () => (
  <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
    <AuthProvider>
      <Login />
    </AuthProvider>
  </BrowserRouter>
)

describe('Login Page - Regression Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLogin.mockReset()
  })

  test('renders essential UI elements in Spanish', () => {
    render(<LoginWrapper />)

    expect(screen.getByText(/novafitness/i)).toBeInTheDocument()
    expect(screen.getByText(/transforma tu camino hacia una vida más saludable/i)).toBeInTheDocument()

    expect(screen.getByLabelText(/dirección de correo electrónico/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()

    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
    expect(screen.getByText(/¿no tienes una cuenta\?/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /crea una ahora/i })).toBeInTheDocument()
  })

  test('toggles password visibility', () => {
    render(<LoginWrapper />)

    const passwordInput = screen.getByLabelText(/contraseña/i)
    const toggleButton = document.querySelector('.login-password-toggle')

    expect(passwordInput).toHaveAttribute('type', 'password')

    if (toggleButton) {
      fireEvent.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'text')

      fireEvent.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'password')
    }
  })

  test('submits form with valid credentials', async () => {
    mockLogin.mockResolvedValueOnce({ token: 'fake-token' })

    render(<LoginWrapper />)

    fireEvent.change(screen.getByLabelText(/dirección de correo electrónico/i), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
    })

    expect(mockShowSuccess).toHaveBeenCalled()
  })

  test('prevents submission when fields are empty', () => {
    render(<LoginWrapper />)

    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    expect(mockLogin).not.toHaveBeenCalled()
    expect(screen.getByLabelText(/dirección de correo electrónico/i)).toHaveAttribute('required')
    expect(screen.getByLabelText(/contraseña/i)).toHaveAttribute('required')
  })

  test('shows loading state during authentication', async () => {
    mockLogin.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)))

    render(<LoginWrapper />)

    const emailInput = screen.getByLabelText(/dirección de correo electrónico/i)
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    expect(screen.getByText(/iniciando sesión/i)).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })
  })

  test('handles authentication error', async () => {
    mockLogin.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Invalid credentials'
        }
      }
    })

    render(<LoginWrapper />)

    fireEvent.change(screen.getByLabelText(/dirección de correo electrónico/i), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'wrongpassword' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(mockShowError).toHaveBeenCalled()
    })

    expect(screen.getByText(/revisa tu correo electrónico/i)).toBeInTheDocument()
    expect(screen.getByText(/revisa tu contraseña/i)).toBeInTheDocument()
  })

  test('register link navigates to register page', () => {
    render(<LoginWrapper />)

    const registerLink = screen.getByRole('link', { name: /crea una ahora/i })
    expect(registerLink).toHaveAttribute('href', '/register')
    expect(registerLink).toHaveClass('login-register-link')
  })

  test('maintains glassmorphism class structure', () => {
    render(<LoginWrapper />)

    const requiredClasses = [
      '.login-container',
      '.login-field',
      '.login-input',
      '.login-button',
      '.login-input-container',
      '.login-input-icon'
    ]

    requiredClasses.forEach((className) => {
      const element = document.querySelector(className)
      expect(element).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /iniciar sesión/i }).closest('form')).toHaveClass('login-form')
  })
})
