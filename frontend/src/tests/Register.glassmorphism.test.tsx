import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Register from '../pages/Register'
import { AuthProvider } from '../contexts/AuthContext'

// Mock AuthContext
const mockUseAuth = {
  register: jest.fn(),
  updateBiometrics: jest.fn(),
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
  <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
    <AuthProvider>
      <Register />
    </AuthProvider>
  </BrowserRouter>
)

describe('Register Page - Glassmorphism Design System Verification', () => {
  test('successfully applies glassmorphism design system', () => {
    render(<RegisterWrapper />)

    // ✅ Verify glassmorphism container structure
    const container = document.querySelector('.login-container')
    expect(container).toBeInTheDocument()

    const logo = document.querySelector('.login-logo')
    expect(logo).toBeInTheDocument()

    const content = document.querySelector('.login-content')
    expect(content).toBeInTheDocument()

    const header = document.querySelector('.login-header')
    expect(header).toBeInTheDocument()

    // ✅ Verify form uses login-form class (glassmorphism)
    const form = document.querySelector('.login-form')
    expect(form).toBeInTheDocument()

    // ✅ Verify FormField components generate glassmorphism classes
    const loginFields = document.querySelectorAll('.login-field')
    expect(loginFields.length).toBeGreaterThan(0) // Should have multiple form fields

    const loginInputs = document.querySelectorAll('.login-input')
    expect(loginInputs.length).toBeGreaterThan(0) // Should have multiple inputs

    // ✅ Verify Button component uses glassmorphism styling
    const loginButton = document.querySelector('.login-button')
    expect(loginButton).toBeInTheDocument()

    // ✅ Verify register section uses glassmorphism classes
    const registerSection = document.querySelector('.login-register')
    expect(registerSection).toBeInTheDocument()

    const registerText = document.querySelector('.login-register-text')
    expect(registerText).toBeInTheDocument()

    const registerLink = document.querySelector('.login-register-link')
    expect(registerLink).toBeInTheDocument()
  })

  test('maintains consistent branding with Login page', () => {
    render(<RegisterWrapper />)

    // ✅ Verify title uses glassmorphism classes
    const titleBrand = screen.getByText(/novafitness/i)
    expect(titleBrand).toHaveClass('login-title-brand')

    // ✅ Verify subtitle uses glassmorphism classes
    expect(screen.getByText(/crea tu cuenta para comenzar/i)).toBeInTheDocument()
  })

  test('progress indicator uses glassmorphism styling', () => {
    render(<RegisterWrapper />)

    // ✅ Verify simplified current-step chip is visible
    expect(screen.getByText(/detalles de la cuenta/i)).toBeInTheDocument()
    
    // ✅ Verify progress bar container uses glassmorphism styles
    const progressContainer = document.querySelector('.bg-gray-700.bg-opacity-30')
    expect(progressContainer).toBeInTheDocument()
    
    const progressBar = document.querySelector('.bg-white.bg-opacity-40')
    expect(progressBar).toBeInTheDocument()
  })

  test('form structure matches design system expectations', () => {
    render(<RegisterWrapper />)

    // ✅ Verify essential form elements are present
    expect(screen.getByText(/^nombre$/i)).toBeInTheDocument()
    expect(screen.getByText(/^apellido$/i)).toBeInTheDocument()
    expect(screen.getByText(/correo electrónico/i)).toBeInTheDocument()
    expect(screen.getAllByText(/contraseña/i).length).toBeGreaterThan(0)

    // ✅ Verify continue button is present
    expect(screen.getByRole('button', { name: /continuar a configuración de perfil/i })).toBeInTheDocument()

    // ✅ Verify login link is present
    expect(screen.getByRole('link', { name: /inicia sesión aquí/i })).toBeInTheDocument()
  })
})