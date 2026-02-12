import { render, screen, fireEvent } from '@testing-library/react'
import { Mail } from 'lucide-react'
import { Input } from './Input'

describe('Input Component', () => {
  test('renders input with label', () => {
    render(<Input label="Email" placeholder="Enter email" />)
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/enter email/i)).toBeInTheDocument()
  })

  test('applies glassmorphism styles', () => {
    render(<Input label="Email" />)
    const input = screen.getByLabelText(/email/i)
    expect(input).toHaveClass('login-input')
  })

  test('renders with icon', () => {
    render(
      <Input 
        label="Email" 
        icon={<Mail data-testid="mail-icon" />}
      />
    )
    expect(screen.getByTestId('mail-icon')).toBeInTheDocument()
  })

  test('handles change events', () => {
    const handleChange = jest.fn()
    render(<Input label="Email" onChange={handleChange} />)
    
    const input = screen.getByLabelText(/email/i)
    fireEvent.change(input, { target: { value: 'test@example.com' } })
    
    expect(handleChange).toHaveBeenCalledTimes(1)
    expect(input).toHaveValue('test@example.com')
  })

  test('shows error state', () => {
    render(<Input label="Email" error="Invalid email" />)
    expect(screen.getByText(/invalid email/i)).toBeInTheDocument()
  })

  test('supports required field indicator', () => {
    render(<Input label="Email" required />)
    expect(screen.getByText('Email *')).toBeInTheDocument()
  })

  test('handles password type with toggle', () => {
    render(<Input label="Password" type="password" showPasswordToggle />)
    
    const input = screen.getByLabelText(/contraseña/i)
    expect(input).toHaveAttribute('type', 'password')
    
    const toggleButton = screen.getByRole('button')
    fireEvent.click(toggleButton)
    
    expect(input).toHaveAttribute('type', 'text')
  })
})