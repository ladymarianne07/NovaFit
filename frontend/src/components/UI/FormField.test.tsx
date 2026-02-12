import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Mail } from 'lucide-react'
import { FormField } from './FormField'

describe('FormField Component', () => {
  test('renders input with all props', () => {
    render(
      <FormField
        id="email"
        label="Email Address"
        type="email"
        placeholder="Enter your email"
        icon={<Mail data-testid="mail-icon" />}
      />
    )
    
    expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument()
    expect(screen.getByTestId('mail-icon')).toBeInTheDocument()
  })

  test('handles validation on blur', async () => {
    const validateEmail = (value: string) => {
      if (!value.includes('@')) return 'Invalid email format'
      return ''
    }

    render(
      <FormField
        id="email"
        label="Email"
        type="email"
        validate={validateEmail}
      />
    )

    const input = screen.getByLabelText(/email/i)
    
    fireEvent.change(input, { target: { value: 'invalid-email' } })
    fireEvent.blur(input)

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
    })
  })

  test('calls onChange with current value and validation', () => {
    const mockOnChange = jest.fn()
    const mockValidate = jest.fn().mockReturnValue('')

    render(
      <FormField
        id="name"
        label="Name"
        onChange={mockOnChange}
        validate={mockValidate}
      />
    )

    const input = screen.getByLabelText(/name/i)
    fireEvent.change(input, { target: { value: 'John Doe' } })

    expect(mockOnChange).toHaveBeenCalledWith('John Doe', true) // value, isValid
    expect(mockValidate).toHaveBeenCalledWith('John Doe')
  })

  test('supports controlled value', () => {
    const { rerender } = render(
      <FormField
        id="controlled"
        label="Controlled Input"
        value="initial value"
        onChange={() => {}}
      />
    )

    expect(screen.getByDisplayValue('initial value')).toBeInTheDocument()

    rerender(
      <FormField
        id="controlled"
        label="Controlled Input"  
        value="updated value"
        onChange={() => {}}
      />
    )

    expect(screen.getByDisplayValue('updated value')).toBeInTheDocument()
  })

  test('shows error state from external prop', () => {
    render(
      <FormField
        id="test"
        label="Test Field"
        error="External error message"
      />
    )

    expect(screen.getByText(/external error message/i)).toBeInTheDocument()
  })

  test('clears error when value becomes valid', async () => {
    const validateRequired = (value: string) => {
      if (!value.trim()) return 'This field is required'
      return ''
    }

    render(
      <FormField
        id="required"
        label="Required Field"
        validate={validateRequired}
      />
    )

    const input = screen.getByLabelText(/required field/i)
    
    // Trigger error
    fireEvent.blur(input)
    await waitFor(() => {
      expect(screen.getByText(/this field is required/i)).toBeInTheDocument()
    })

    // Fix error
    fireEvent.change(input, { target: { value: 'Valid input' } })
    fireEvent.blur(input)
    
    await waitFor(() => {
      expect(screen.queryByText(/this field is required/i)).not.toBeInTheDocument()
    })
  })
})