import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { TextEncoder } from 'util'
import Register from '../pages/Register'
import { AuthProvider } from '../contexts/AuthContext'

if (typeof global.TextEncoder === 'undefined') {
  ;(global as any).TextEncoder = TextEncoder
}

const mockRegister = jest.fn()
const mockShowError = jest.fn()
const mockShowSuccess = jest.fn()

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    register: mockRegister,
    user: null,
    token: null,
    loading: false,
    login: jest.fn(),
    logout: jest.fn(),
    refreshUser: jest.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

jest.mock('../contexts/ToastContext', () => ({
  useToast: () => ({
    showError: mockShowError,
    showSuccess: mockShowSuccess,
    showToast: jest.fn(),
  }),
}))

const RegisterWrapper: React.FC = () => (
  <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
    <AuthProvider>
      <Register />
    </AuthProvider>
  </BrowserRouter>
)

// ── helpers ────────────────────────────────────────────────────────────────

const selectRole = (roleName: RegExp) => {
  fireEvent.click(screen.getByRole('button', { name: /tipo de cuenta/i }))
  fireEvent.click(screen.getByRole('option', { name: roleName }))
}

const completeStep1 = () => {
  fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: 'John' } })
  fireEvent.change(screen.getByLabelText(/apellido/i), { target: { value: 'Doe' } })
  fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'john@example.com' } })
  fireEvent.change(screen.getByLabelText(/^contraseña/i), { target: { value: 'password123' } })
  fireEvent.change(screen.getByLabelText(/confirmar contraseña/i), { target: { value: 'password123' } })
  fireEvent.click(screen.getByRole('button', { name: /^continuar$/i }))
}

// For trainers: after step 1 they reach the self-use question; click "Sí" to proceed to biometrics
const chooseTrainerSelfUse = () => {
  fireEvent.click(screen.getByRole('button', { name: /sí, también la uso para mí/i }))
}

const completeStep2 = () => {
  fireEvent.change(screen.getByLabelText(/edad/i), { target: { value: '25' } })
  fireEvent.click(screen.getByRole('button', { name: /sexo/i }))
  fireEvent.click(screen.getByRole('option', { name: /masculino/i }))
  fireEvent.change(screen.getByLabelText(/peso.*kg/i), { target: { value: '70' } })
  fireEvent.change(screen.getByLabelText(/altura.*cm/i), { target: { value: '175' } })
  fireEvent.click(screen.getByRole('button', { name: /nivel de actividad/i }))
  fireEvent.click(screen.getByRole('option', { name: /moderadamente activo/i }))
}

// ── tests ──────────────────────────────────────────────────────────────────

describe('Register Page - Role Selector', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockRegister.mockReset()
  })

  test('role selector is visible in step 1', () => {
    render(<RegisterWrapper />)

    expect(screen.getByRole('button', { name: /tipo de cuenta/i })).toBeInTheDocument()
  })

  test('defaults to Alumno (student) role', () => {
    render(<RegisterWrapper />)

    const roleButton = screen.getByRole('button', { name: /tipo de cuenta/i })
    expect(roleButton).toHaveTextContent(/alumno/i)
  })

  test('can select Entrenador (trainer) role', async () => {
    render(<RegisterWrapper />)

    selectRole(/entrenador/i)

    await waitFor(() => {
      const roleButton = screen.getByRole('button', { name: /tipo de cuenta/i })
      expect(roleButton).toHaveTextContent(/entrenador/i)
    })
  })

  test('can switch back from trainer to student', async () => {
    render(<RegisterWrapper />)

    selectRole(/entrenador/i)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /tipo de cuenta/i })).toHaveTextContent(/entrenador/i)
    })

    selectRole(/alumno/i)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /tipo de cuenta/i })).toHaveTextContent(/alumno/i)
    })
  })

  test('submits with role: student when default is kept', async () => {
    mockRegister.mockResolvedValueOnce({ success: true })
    render(<RegisterWrapper />)

    // keep default student role
    completeStep1()
    await waitFor(() => expect(screen.getByText(/perfil biométrico/i)).toBeInTheDocument())

    completeStep2()
    fireEvent.click(screen.getByRole('button', { name: /configurar objetivo/i }))
    await waitFor(() => expect(screen.getByText(/objetivo fitness/i)).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /mantenimiento/i }))
    fireEvent.click(screen.getByRole('button', { name: /completar registro/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith(
        expect.objectContaining({ role: 'student' }),
      )
    })
  })

  test('submits with role: trainer when Entrenador is selected', async () => {
    mockRegister.mockResolvedValueOnce({ success: true })
    render(<RegisterWrapper />)

    selectRole(/entrenador/i)

    completeStep1()
    await waitFor(() => expect(screen.getByText(/tipo de uso/i)).toBeInTheDocument())

    chooseTrainerSelfUse()
    await waitFor(() => expect(screen.getByText(/perfil biométrico/i)).toBeInTheDocument())

    completeStep2()
    fireEvent.click(screen.getByRole('button', { name: /configurar objetivo/i }))
    await waitFor(() => expect(screen.getByText(/objetivo fitness/i)).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /mantenimiento/i }))
    fireEvent.click(screen.getByRole('button', { name: /completar registro/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith(
        expect.objectContaining({ role: 'trainer', uses_app_for_self: true }),
      )
    })
  })

  test('role selection persists through all steps', async () => {
    render(<RegisterWrapper />)

    selectRole(/entrenador/i)

    completeStep1()
    await waitFor(() => expect(screen.getByText(/tipo de uso/i)).toBeInTheDocument())

    chooseTrainerSelfUse()
    await waitFor(() => expect(screen.getByText(/perfil biométrico/i)).toBeInTheDocument())

    // go back to step 2 (self-use question)
    fireEvent.click(screen.getByRole('button', { name: /atrás/i }))
    await waitFor(() => expect(screen.getByText(/tipo de uso/i)).toBeInTheDocument())

    // go back to step 1
    fireEvent.click(screen.getByRole('button', { name: /atrás/i }))
    await waitFor(() => expect(screen.getByText(/detalles de la cuenta/i)).toBeInTheDocument())

    // role should still be trainer
    expect(screen.getByRole('button', { name: /tipo de cuenta/i })).toHaveTextContent(/entrenador/i)
  })
})
