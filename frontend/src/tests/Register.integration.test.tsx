import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { TextEncoder } from 'util'
import Register from '../pages/Register'
import { AuthProvider } from '../contexts/AuthContext'

// Mock fetch for API calls
global.fetch = jest.fn()

const mockRegister = jest.fn()
const mockShowError = jest.fn()
const mockShowSuccess = jest.fn()

if (typeof global.TextEncoder === 'undefined') {
  ;(global as any).TextEncoder = TextEncoder
}

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    register: mockRegister,
    updateBiometrics: jest.fn(),
    user: null,
    token: null,
    loading: false,
    login: jest.fn(),
    logout: jest.fn(),
    refreshUser: jest.fn()
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

const RegisterWrapper: React.FC = () => (
  <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
    <AuthProvider>
      <Register />
    </AuthProvider>
  </BrowserRouter>
)

const completeStep1 = () => {
  fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: 'John' } })
  fireEvent.change(screen.getByLabelText(/apellido/i), { target: { value: 'Doe' } })
  fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'john@example.com' } })
  fireEvent.change(screen.getByLabelText(/^contraseña/i), { target: { value: 'password123' } })
  fireEvent.change(screen.getByLabelText(/confirmar contraseña/i), { target: { value: 'password123' } })
  fireEvent.click(screen.getByRole('button', { name: /continuar a configuración de perfil/i }))
}

const completeStep2 = () => {
  fireEvent.change(screen.getByLabelText(/edad/i), { target: { value: '25' } })

  fireEvent.click(screen.getByRole('button', { name: /género/i }))
  fireEvent.click(screen.getByRole('option', { name: /masculino/i }))

  fireEvent.change(screen.getByLabelText(/peso.*kg/i), { target: { value: '70' } })
  fireEvent.change(screen.getByLabelText(/altura.*cm/i), { target: { value: '175' } })

  fireEvent.click(screen.getByRole('button', { name: /nivel de actividad/i }))
  fireEvent.click(screen.getByRole('option', { name: /moderadamente activo/i }))
}

describe('Register Page - Design System Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockRegister.mockReset()
  })

  test('renders step 1 and base glassmorphism structure', () => {
    render(<RegisterWrapper />)

    expect(document.querySelector('.login-container')).toBeInTheDocument()
    expect(document.querySelector('.login-logo')).toBeInTheDocument()
    expect(document.querySelector('.login-content')).toBeInTheDocument()
    expect(document.querySelector('.login-header')).toBeInTheDocument()

    expect(screen.getByText(/detalles de la cuenta/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/apellido/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^contraseña/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirmar contraseña/i)).toBeInTheDocument()
  })

  test('shows validation when submitting empty step 1', async () => {
    render(<RegisterWrapper />)

    fireEvent.click(screen.getByRole('button', { name: /continuar a configuración de perfil/i }))

    await waitFor(() => {
      expect(screen.getByText(/el nombre es obligatorio/i)).toBeInTheDocument()
      expect(mockShowError).toHaveBeenCalled()
    })
  })

  test('shows password mismatch validation', async () => {
    render(<RegisterWrapper />)

    fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: 'John' } })
    fireEvent.change(screen.getByLabelText(/apellido/i), { target: { value: 'Doe' } })
    fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'john@example.com' } })
    fireEvent.change(screen.getByLabelText(/^contraseña/i), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText(/confirmar contraseña/i), { target: { value: 'different' } })

    fireEvent.click(screen.getByRole('button', { name: /continuar a configuración de perfil/i }))

    await waitFor(() => {
      expect(screen.getByText(/las contraseñas no coinciden/i)).toBeInTheDocument()
    })
  })

  test('progresses to step 2 and can navigate back to step 1', async () => {
    render(<RegisterWrapper />)

    completeStep1()

    await waitFor(() => {
      expect(screen.getByText(/perfil biométrico/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /atrás/i }))

    await waitFor(() => {
      expect(screen.getByText(/detalles de la cuenta/i)).toBeInTheDocument()
    })
  })

  test('progresses to step 3 from valid biometrics', async () => {
    render(<RegisterWrapper />)

    completeStep1()

    await waitFor(() => {
      expect(screen.getByText(/perfil biométrico/i)).toBeInTheDocument()
    })

    completeStep2()

    fireEvent.click(screen.getByRole('button', { name: /configurar objetivo/i }))

    await waitFor(() => {
      expect(screen.getByText(/objetivo fitness/i)).toBeInTheDocument()
    })
  })

  test('completes registration with objective data', async () => {
    mockRegister.mockResolvedValueOnce({ success: true })

    render(<RegisterWrapper />)

    completeStep1()

    await waitFor(() => {
      expect(screen.getByText(/perfil biométrico/i)).toBeInTheDocument()
    })

    completeStep2()
    fireEvent.click(screen.getByRole('button', { name: /configurar objetivo/i }))

    await waitFor(() => {
      expect(screen.getByText(/objetivo fitness/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /mantenimiento/i }))
    fireEvent.click(screen.getByRole('button', { name: /completar registro/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: 'john@example.com',
        password: 'password123',
        first_name: 'John',
        last_name: 'Doe',
        age: 25,
        gender: 'male',
        weight: 70,
        height: 175,
        activity_level: 1.5,
        objective: 'maintenance',
        aggressiveness_level: 2
      })
    })

    expect(mockShowSuccess).toHaveBeenCalled()
  })
})
