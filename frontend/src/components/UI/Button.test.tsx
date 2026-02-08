import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Button Component', () => {
  test('renders button with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  test('applies correct variant classes', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button')).toHaveClass('login-button')

    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button')).toHaveClass('btn-secondary')
  })

  test('handles click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  test('is disabled when loading', () => {
    render(<Button isLoading>Loading</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  test('shows loading state', () => {
    render(<Button isLoading>Submit</Button>)
    expect(screen.getByText(/processing/i)).toBeInTheDocument()
  })

  test('renders with icon', () => {
    const TestIcon = () => <span data-testid="test-icon">Icon</span>
    render(
      <Button icon={<TestIcon />}>
        With Icon
      </Button>
    )
    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
  })
})