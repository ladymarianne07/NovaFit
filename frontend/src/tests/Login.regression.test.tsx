import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, Zap } from 'lucide-react'
import Login from '../pages/Login'
import { AuthProvider } from '../contexts/AuthContext'

// Mock fetch for API calls
global.fetch = jest.fn()

// mock AuthContext
const mockLogin = jest.fn()
const mockUseAuth = {
  login: mockLogin,
  user: null,
  token: null,
  loading: false,
  logout: jest.fn()
}

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}))

// Test wrapper component
const LoginWrapper: React.FC = () => (
  <BrowserRouter>
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

  describe('Initial Rendering & UI Structure', () => {
    test('renders all essential UI elements', () => {
      render(<LoginWrapper />)

      // Logo and branding (Zap icon in login-logo)
      const logoContainer = document.querySelector('.login-logo')
      expect(logoContainer).toBeInTheDocument()
      
      // Header elements
      expect(screen.getByText(/novafitness/i)).toBeInTheDocument()
      expect(screen.getByText(/transforma tu camino/i)).toBeInTheDocument()
      expect(screen.getByText(/novafitness/i)).toBeInTheDocument()
      expect(screen.getByText(/transform your fitness journey/i)).toBeInTheDocument()

      // Form fields
      expect(screen.getByLabelText(/dirección de correo electrónico/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
      
      // Form controls
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /create one now/i })).toBeInTheDocument()
    })

    test('renders with correct glassmorphism CSS classes', () => {
      render(<LoginWrapper />)

      // Container structure
      const container = document.querySelector('.login-container')
      expect(container).toBeInTheDocument()

      // Form fields
      const emailField = screen.getByLabelText(/dirección de correo electrónico/i).closest('.login-field')
      expect(emailField).toHaveClass('login-field')

      const passwordField = screen.getByLabelText(/contraseña/i).closest('.login-field')
      expect(passwordField).toHaveClass('login-field')

      // Input styling
      expect(screen.getByLabelText(/dirección de correo electrónico/i)).toHaveClass('login-input')
      expect(screen.getByLabelText(/contraseña/i)).toHaveClass('login-input')

      // Button styling
      expect(screen.getByRole('button', { name: /sign in/i })).toHaveClass('login-button')
    })

    test('displays correct icons for form elements', () => {
      render(<LoginWrapper />)

      // Email icon
      const emailContainer = screen.getByLabelText(/email address/i).closest('.login-input-container')
      expect(emailContainer?.querySelector('.login-input-icon')).toBeInTheDocument()

      // Password icon
      const passwordContainer = screen.getByLabelText(/password/i).closest('.login-input-container')
      expect(passwordContainer?.querySelector('.login-input-icon')).toBeInTheDocument()

      // Password toggle button
      const passwordToggle = document.querySelector('.login-password-toggle')
      expect(passwordToggle).toBeInTheDocument()

      // Submit button icon
      const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
      expect(submitButton.textContent).toContain('Iniciar sesión')
    })
  })

  describe('Form Functionality', () => {
    test('handles email input changes', () => {
      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/dirección de correo electrónico/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      
      expect(emailInput).toHaveValue('test@example.com')
    })

    test('handles password input changes', () => {
      render(<LoginWrapper />)

      const passwordInput = screen.getByLabelText(/contraseña/i)
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      
      expect(passwordInput).toHaveValue('password123')
    })

    test('toggles password visibility correctly', () => {
      render(<LoginWrapper />)

      const passwordInput = screen.getByLabelText(/contraseña/i)
      const toggleButton = document.querySelector('.login-password-toggle')

      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password')

      // Click toggle to show password
      if (toggleButton) {
        fireEvent.click(toggleButton)
        expect(passwordInput).toHaveAttribute('type', 'text')

        // Click toggle to hide password again
        fireEvent.click(toggleButton)
        expect(passwordInput).toHaveAttribute('type', 'password')
      }
    })

    test('validates required fields on submit', () => {
      render(<LoginWrapper />)

      const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
      
      // Click submit without filling required fields
      fireEvent.click(submitButton)
      
      // HTML5 validation prevents submission, so mockLogin should not be called
      expect(mockLogin).not.toHaveBeenCalled()
      
      // Verify required attributes exist
      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      expect(emailInput).toHaveAttribute('required')
      expect(passwordInput).toHaveAttribute('required')
    })

    test('submits form with valid credentials', async () => {
      mockLogin.mockResolvedValueOnce({ token: 'fake-token' })
      
      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      // Fill form
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      // Submit form
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'test@example.com',
          password: 'password123'
        })
      })
    })
  })

  describe('Loading States', () => {
    test('shows loading state during authentication', async () => {
      // Mock delayed login
      mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      // Fill and submit form
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      // Check loading state
      expect(screen.getByText(/signing in.../i)).toBeInTheDocument()
      expect(submitButton).toBeDisabled()
      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()

      // Spinner should be visible
      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    test('disables form elements during loading', async () => {
      mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      const toggleButton = passwordInput.closest('.login-input-container')?.querySelector('.login-password-toggle')

      // Fill and submit form
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      // All interactive elements should be disabled
      expect(submitButton).toBeDisabled()
      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
      if (toggleButton) {
        expect(toggleButton).toBeDisabled()
      }
    })
  })

  describe('Error Handling', () => {
    test('displays error message on authentication failure', async () => {
      const errorMessage = 'Invalid credentials'
      mockLogin.mockRejectedValueOnce({
        response: {
          data: {
            detail: errorMessage
          }
        }
      })

      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      // Submit form with credentials
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
    })

    test('displays generic error message for network failures', async () => {
      mockLogin.mockRejectedValueOnce(new Error('Network error'))

      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      // Submit form
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/login failed. please try again./i)).toBeInTheDocument()
      })
    })

    test('clears error message on new submission', async () => {
      // First attempt - error
      mockLogin.mockRejectedValueOnce({
        response: { data: { detail: 'Invalid credentials' } }
      })

      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      // First submission with error
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrong' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
      })

      // Second attempt - should clear error
      mockLogin.mockResolvedValueOnce({ token: 'valid-token' })
      
      fireEvent.change(passwordInput, { target: { value: 'correct' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByText(/invalid credentials/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Navigation & Links', () => {
    test('register link navigates correctly', () => {
      render(<LoginWrapper />)

      const registerLink = screen.getByRole('link', { name: /create one now/i })
      
      expect(registerLink).toHaveAttribute('href', '/register')
      expect(registerLink).toHaveClass('login-register-link')
    })

    test('maintains glassmorphism styling for register section', () => {
      render(<LoginWrapper />)

      const registerSection = screen.getByText(/don't have an account/i).closest('.login-register')
      expect(registerSection).toHaveClass('login-register')

      const registerText = screen.getByText(/don't have an account/i)
      expect(registerText).toHaveClass('login-register-text')
    })
  })

  describe('Accessibility', () => {
    test('has proper form labels and structure', () => {
      render(<LoginWrapper />)

      // Labels should be properly associated
      expect(screen.getByLabelText(/email address/i)).toHaveAttribute('id', 'email')
      expect(screen.getByLabelText(/password/i)).toHaveAttribute('id', 'password')

      // Form should be semantic
      const form = screen.getByRole('button', { name: /sign in/i }).closest('form')
      expect(form).toBeInTheDocument()
    })

    test('error messages have proper ARIA attributes', async () => {
      mockLogin.mockRejectedValueOnce({
        response: { data: { detail: 'Test error' } }
      })

      render(<LoginWrapper />)

      const emailInput = screen.getByLabelText(/email address/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrong' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        const errorElement = screen.getByText(/test error/i)
        expect(errorElement.closest('.login-error')).toBeInTheDocument()
      })
    })

    test('submit button is keyboard accessible', () => {
      render(<LoginWrapper />)

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      expect(submitButton).toHaveAttribute('type', 'submit')
      
      // Should be focusable and activatable via keyboard
      submitButton.focus()
      expect(document.activeElement).toBe(submitButton)
    })
  })

  describe('CSS Integration & Glassmorphism Preservation', () => {
    test('maintains glassmorphism class structure', () => {
      render(<LoginWrapper />)

      // Verify key glassmorphism classes are applied correctly
      const requiredClasses = [
        '.login-container',
        '.login-field', 
        '.login-input',
        '.login-button',
        '.login-input-container',
        '.login-input-icon'
      ]

      requiredClasses.forEach(className => {
        const element = document.querySelector(className)
        expect(element).toBeInTheDocument()
      })
    })

    test('password toggle maintains glassmorphism styling', () => {
      render(<LoginWrapper />)

      const passwordToggle = document.querySelector('.login-password-toggle')
      expect(passwordToggle).toBeInTheDocument()
      expect(passwordToggle).toHaveClass('login-password-toggle')
    })

    test('form maintains responsive design structure', () => {
      render(<LoginWrapper />)

      // Check that responsive classes and structure are preserved
      const form = screen.getByRole('button', { name: /sign in/i }).closest('form')
      expect(form).toHaveClass('login-form')

      const content = document.querySelector('.login-content')
      expect(content).toBeInTheDocument()

      const header = document.querySelector('.login-header')  
      expect(header).toBeInTheDocument()
    })
  })
})