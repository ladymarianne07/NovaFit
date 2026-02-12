import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Register from '../pages/Register'
import { AuthProvider } from '../contexts/AuthContext'

// Mock fetch for API calls
global.fetch = jest.fn()

// Mock AuthContext
const mockRegister = jest.fn()
const mockUpdateBiometrics = jest.fn()
const mockUseAuth = {
  register: mockRegister,
  updateBiometrics: mockUpdateBiometrics,
  user: null,
  token: null,
  loading: false,
  login: jest.fn(),
  logout: jest.fn(),
  refreshUser: jest.fn()
}

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}))

// Test wrapper component
const RegisterWrapper: React.FC = () => (
  <BrowserRouter>
    <AuthProvider>
      <Register />
    </AuthProvider>
  </BrowserRouter>
)

describe('Register Page - Design System Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockRegister.mockReset()
    mockUpdateBiometrics.mockReset()
  })

  describe('Glassmorphism Design System Integration', () => {
    test('applies glassmorphism container classes', () => {
      render(<RegisterWrapper />)

      // Verify glassmorphism container structure
      const container = document.querySelector('.login-container')
      expect(container).toBeInTheDocument()

      const logo = document.querySelector('.login-logo')
      expect(logo).toBeInTheDocument()

      const content = document.querySelector('.login-content')
      expect(content).toBeInTheDocument()

      const header = document.querySelector('.login-header')
      expect(header).toBeInTheDocument()
    })

    test('uses design system components for form fields', () => {
      render(<RegisterWrapper />)

      // Verify FormField components are used (they have glassmorphism classes)
      const emailField = screen.getByLabelText(/correo electrónico/i).closest('.login-field')
      expect(emailField).toBeInTheDocument()
      expect(emailField).toHaveClass('login-field')

      const passwordField = screen.getByLabelText(/^contraseña/i).closest('.login-field')
      expect(passwordField).toBeInTheDocument()
      expect(passwordField).toHaveClass('login-field')

      // Verify inputs have glassmorphism styling
      expect(screen.getByLabelText(/correo electrónico/i)).toHaveClass('login-input')
      expect(screen.getByLabelText(/^contraseña/i)).toHaveClass('login-input')
    })

    test('uses design system Button component', () => {
      render(<RegisterWrapper />)

      const continueButton = screen.getByRole('button', { name: /continuar a configuración de perfil/i })
      expect(continueButton).toHaveClass('login-button') // Design system button uses glassmorphism class
    })

    test('maintains consistent styling with Login page', () => {
      render(<RegisterWrapper />)

      // Title styling
      expect(screen.getByText(/crea tu cuenta/i)).toBeInTheDocument()
      const titleBrand = screen.getByText(/novafitness/i)
      expect(titleBrand).toHaveClass('login-title-brand')

      // Footer/register link styling  
      const loginLink = screen.getByRole('link', { name: /inicia sesión aquí/i })
      expect(loginLink).toHaveClass('login-register-link')
    })
  })

  describe('Step 1: Account Creation Form', () => {
    test('renders step 1 form fields correctly', () => {
      render(<RegisterWrapper />)

      // Form fields should be present
      expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/apellido/i)).toBeInTheDocument()  
      expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/^contraseña/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirmar contraseña/i)).toBeInTheDocument()

      // Continue button should be present
      expect(screen.getByRole('button', { name: /continuar a configuración de perfil/i })).toBeInTheDocument()
    })

    test('handles form input changes', () => {
      render(<RegisterWrapper />)

      const firstNameInput = screen.getByLabelText(/nombre/i)
      const emailInput = screen.getByLabelText(/correo electrónico/i)
      const passwordInput = screen.getByLabelText(/^contraseña/i)

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      expect(firstNameInput).toHaveValue('John')
      expect(emailInput).toHaveValue('john@example.com')
      expect(passwordInput).toHaveValue('password123')
    })

    test('shows password toggle functionality', () => {
      render(<RegisterWrapper />)

      const passwordInput = screen.getByLabelText(/^contraseña/i)
      
      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password')

      // Should have password toggle (via FormField component)
      const passwordToggle = passwordInput.closest('.login-input-container')?.querySelector('.login-password-toggle')
      if (passwordToggle) {
        fireEvent.click(passwordToggle)
        expect(passwordInput).toHaveAttribute('type', 'text')
      }
    })

    test('progresses to step 2 with valid data', async () => {
      render(<RegisterWrapper />)

      // Fill step 1 form
      fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: 'John' } })
      fireEvent.change(screen.getByLabelText(/apellido/i), { target: { value: 'Doe' } })
      fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'john@example.com' } })
      fireEvent.change(screen.getByLabelText(/^contraseña/i), { target: { value: 'password123' } })
      fireEvent.change(screen.getByLabelText(/confirmar contraseña/i), { target: { value: 'password123' } })

      // Submit step 1
      fireEvent.click(screen.getByRole('button', { name: /continuar a configuración de perfil/i }))

      // Should progress to step 2
      await waitFor(() => {
        expect(screen.getByText(/paso 2 de 2/i)).toBeInTheDocument()
        expect(screen.getByText(/perfil biométrico/i)).toBeInTheDocument()
      })
    })
  })

  describe('Step 2: Biometric Profile Form', () => {
    beforeEach(async () => {
      render(<RegisterWrapper />)
      
      // Fill and submit step 1 first
      fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: 'John' } })
      fireEvent.change(screen.getByLabelText(/apellido/i), { target: { value: 'Doe' } })
      fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'john@example.com' } })
      fireEvent.change(screen.getByLabelText(/^contraseña/i), { target: { value: 'password123' } })
      fireEvent.change(screen.getByLabelText(/confirmar contraseña/i), { target: { value: 'password123' } })
      fireEvent.click(screen.getByRole('button', { name: /continuar a configuración de perfil/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/paso 2 de 2/i)).toBeInTheDocument()
      })
    })

    test('renders step 2 biometric form fields', () => {
      // Biometric fields should be present
      expect(screen.getByLabelText(/age/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/género/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/peso.*kg/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/altura.*cm/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/nivel de actividad/i)).toBeInTheDocument()

      // Navigation buttons
      expect(screen.getByRole('button', { name: /atrás/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /completar configuración/i })).toBeInTheDocument()
    })

    test('uses glassmorphism styling for select fields', () => {
      const genderSelect = screen.getByLabelText(/género/i)
      expect(genderSelect).toHaveClass('login-input')

      const genderField = genderSelect.closest('.login-field')
      expect(genderField).toHaveClass('login-field')

      const activitySelect = screen.getByLabelText(/nivel de actividad/i)
      expect(activitySelect).toHaveClass('login-input')
    })

    test('handles back navigation to step 1', async () => {
      fireEvent.click(screen.getByRole('button', { name: /atrás/i }))

      await waitFor(() => {
        expect(screen.getByText(/paso 1 de 2/i)).toBeInTheDocument()
        expect(screen.getByText(/detalles de la cuenta/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument()
      })
    })

    test('completes registration with biometric data', async () => {
      mockRegister.mockResolvedValueOnce({ success: true })
      mockUpdateBiometrics.mockResolvedValueOnce({ success: true })

      // Fill biometric form
      fireEvent.change(screen.getByLabelText(/age/i), { target: { value: '25' } })
      fireEvent.change(screen.getByLabelText(/género/i), { target: { value: 'male' } })
      fireEvent.change(screen.getByLabelText(/peso.*kg/i), { target: { value: '70' } })
      fireEvent.change(screen.getByLabelText(/altura.*cm/i), { target: { value: '175' } })
      fireEvent.change(screen.getByLabelText(/nivel de actividad/i), { target: { value: '1.50' } })

      // Submit complete registration
      fireEvent.click(screen.getByRole('button', { name: /completar configuración/i }))

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: 'john@example.com',
          password: 'password123',
          first_name: 'John',
          last_name: 'Doe'
        })
        
        expect(mockUpdateBiometrics).toHaveBeenCalledWith({
          age: 25,
          gender: 'male',
          weight: 70,
          height: 175,
          activity_level: 1.50
        })
      })
    })
  })

  describe('Progress Indicator', () => {
    test('shows glassmorphism styled progress indicator', () => {
      render(<RegisterWrapper />)

      expect(screen.getByText(/step 1 of 2/i)).toBeInTheDocument()
      
      // Progress bar should have glassmorphism styling
      const progressContainer = document.querySelector('.w-full.bg-gray-700.bg-opacity-30')
      expect(progressContainer).toBeInTheDocument()
      
      const progressBar = document.querySelector('.bg-white.bg-opacity-40')
      expect(progressBar).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    test('displays validation errors with glassmorphism styling', async () => {
      render(<RegisterWrapper />)

      // Try to submit empty form
      fireEvent.click(screen.getByRole('button', { name: /continue to profile setup/i }))

      await waitFor(() => {
        const errorContainer = document.querySelector('.login-error')
        expect(errorContainer).toBeInTheDocument()
        
        const errorText = screen.getByText(/all fields are required/i)
        expect(errorText).toBeInTheDocument()
        expect(errorText).toHaveClass('text-red-300')
      })
    })

    test('displays password mismatch error', async () => {
      render(<RegisterWrapper />)

      // Fill form with mismatched passwords
      fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: 'John' } })
      fireEvent.change(screen.getByLabelText(/apellido/i), { target: { value: 'Doe' } })
      fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'john@example.com' } })
      fireEvent.change(screen.getByLabelText(/^contraseña/i), { target: { value: 'password123' } })
      fireEvent.change(screen.getByLabelText(/confirmar contraseña/i), { target: { value: 'different' } })

      fireEvent.click(screen.getByRole('button', { name: /continuar a configuración de perfil/i }))

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
      })
    })
  })
})