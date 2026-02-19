import React, { useState } from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Mail, Lock, Zap, User } from 'lucide-react'
import { Button } from './Button'
import { FormField } from './FormField'

describe('Design System Integration', () => {
  test('FormField displays validation error correctly', async () => {
    const validateEmail = (value: string) => {
      if (!value.includes('@')) return 'Invalid email format'
      return ''
    }

    render(
      <FormField
        id="email"
        label="Email Address"
        type="email"
        validate={validateEmail}
      />
    )

    const emailInput = screen.getByLabelText(/email address/i)
    
    // Input invalid email
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)

    // Check if error message appears
    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
    })
  })

  test('Button and FormField work together in form', async () => {
    const mockSubmit = jest.fn()
    const validateEmail = (value: string) => {
      if (!value.includes('@')) return 'Invalid email format'
      return ''
    }

    const TestForm = () => {
      const [email, setEmail] = useState('')
      const [isValid, setIsValid] = useState(false)
      const [error, setError] = useState('')

      const handleChange = (value: string, valid: boolean) => {
        setEmail(value)
        setIsValid(valid)
        // Update error based on validation
        if (!valid && value) {
          setError(validateEmail(value))
        } else {
          setError('')
        }
      }

      return (
        <form onSubmit={(e) => { 
          e.preventDefault();
          mockSubmit({ email, isValid });
        }}>
          <FormField
            id="email"
            label="Email Address"
            type="email"
            value={email}
            validate={validateEmail}
            error={error}
            icon={<Mail data-testid="email-icon" />}
            onChange={handleChange}
          />
          <Button type="submit" icon={<Zap data-testid="submit-icon" />}>
            Sign In
          </Button>
        </form>
      )
    }

    render(<TestForm />)

    // Verify form renders correctly
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByTestId('email-icon')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByTestId('submit-icon')).toBeInTheDocument()

    // Test invalid input
    const emailInput = screen.getByLabelText(/email address/i)
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
    })

    // Submit with invalid email
    const form = screen.getByRole('button', { name: /sign in/i }).closest('form')!
    fireEvent.submit(form)
    expect(mockSubmit).toHaveBeenCalledWith({ email: 'invalid-email', isValid: false })

    // Test valid input  
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.blur(emailInput)

    await waitFor(() => {
      expect(screen.queryByText(/invalid email format/i)).not.toBeInTheDocument()
    })

    // Submit with valid email
    fireEvent.submit(form)
    expect(mockSubmit).toHaveBeenCalledWith({ email: 'test@example.com', isValid: true })
  })

  test('Multiple FormFields maintain glassmorphism styling', () => {
    render(
      <div>
        <FormField
          id="email"
          label="Email Address"
          type="email"
          icon={<Mail data-testid="email-icon" />}
        />
        <FormField
          id="password"
          label="Password"
          type="password"
          showPasswordToggle
          icon={<Lock data-testid="password-icon" />}
        />
        <FormField
          id="name"
          label="Full Name"
          icon={<User data-testid="name-icon" />}
        />
      </div>
    )

    // All inputs should have glassmorphism styling
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i, { selector: 'input' })
    const nameInput = screen.getByLabelText(/full name/i)

    expect(emailInput).toHaveClass('login-input')
    expect(passwordInput).toHaveClass('login-input')
    expect(nameInput).toHaveClass('login-input')

    // All should have proper icon positioning
    expect(screen.getByTestId('email-icon')).toBeInTheDocument()
    expect(screen.getByTestId('password-icon')).toBeInTheDocument()
    expect(screen.getByTestId('name-icon')).toBeInTheDocument()
  })

  test('Button variants display consistently', () => {
    render(
      <div>
        <Button variant="primary">Primary Action</Button>
        <Button variant="secondary">Secondary Action</Button>
        <Button variant="ghost">Ghost Action</Button>
        <Button isLoading>Loading Action</Button>
      </div>
    )

    const primaryBtn = screen.getByRole('button', { name: /primary action/i })
    const secondaryBtn = screen.getByRole('button', { name: /secondary action/i })
    const ghostBtn = screen.getByRole('button', { name: /ghost action/i })
    const loadingBtn = screen.getByRole('button', { name: /processing/i })

    // Check glassmorphism for primary (login-button class)
    expect(primaryBtn).toHaveClass('login-button')
    expect(secondaryBtn).toHaveClass('btn-secondary')
    expect(ghostBtn).toHaveClass('btn-ghost')
    expect(loadingBtn).toBeDisabled()
    expect(loadingBtn).toHaveClass('login-button')
  })

  test('Password field with toggle maintains glassmorphism', () => {
    render(
      <FormField
        id="password"
        label="Password"
        type="password"
        showPasswordToggle
        icon={<Lock data-testid="lock-icon" />}
      />
    )

    const passwordInput = screen.getByLabelText(/password/i)
    const toggleButton = screen.getByRole('button', { name: /mostrar contraseña|ocultar contraseña/i })

    // Verify glassmorphism styling
    expect(passwordInput).toHaveClass('login-input')
    expect(passwordInput).toHaveAttribute('type', 'password')

    // Test toggle functionality
    fireEvent.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')

    fireEvent.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'password')

    // Verify icon is still present
    expect(screen.getByTestId('lock-icon')).toBeInTheDocument()
  })
})