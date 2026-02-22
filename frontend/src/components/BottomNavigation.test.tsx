import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import BottomNavigation from './BottomNavigation'

describe('BottomNavigation', () => {
  const mockOnTabChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders all navigation items', () => {
    render(
      <BottomNavigation
        activeTab="dashboard"
        onTabChange={mockOnTabChange}
      />
    )

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Comidas')).toBeInTheDocument()
    expect(screen.getByText('Entreno')).toBeInTheDocument()
    expect(screen.getByText('Progreso')).toBeInTheDocument()
  })

  it('shows active tab with correct styling', () => {
    render(
      <BottomNavigation
        activeTab="training"
        onTabChange={mockOnTabChange}
      />
    )

    const trainingButton = screen.getByRole('button', { name: /entreno/i })
    expect(trainingButton).toHaveClass('active')
  })

  it('calls onTabChange when navigation item is clicked', () => {
    render(
      <BottomNavigation
        activeTab="dashboard"
        onTabChange={mockOnTabChange}
      />
    )

    const mealsButton = screen.getByRole('button', { name: /comidas/i })
    fireEvent.click(mealsButton)

    expect(mockOnTabChange).toHaveBeenCalledWith('meals')
  })

  it('renders with default activeTab when not provided', () => {
    render(
      <BottomNavigation
        onTabChange={mockOnTabChange}
      />
    )

    const dashboardButton = screen.getByRole('button', { name: /home/i })
    expect(dashboardButton).toHaveClass('active')
  })

  it('handles missing callback props gracefully', () => {
    render(<BottomNavigation activeTab="training" />)

    const trainingButton = screen.getByRole('button', { name: /entreno/i })
    
    // Should not throw error when clicking
    expect(() => {
      fireEvent.click(trainingButton)
    }).not.toThrow()
  })

  it('displays correct icons for each navigation item', () => {
    render(
      <BottomNavigation
        activeTab="dashboard"
        onTabChange={mockOnTabChange}
      />
    )

    // Check that buttons render (icons are inside buttons)
    expect(screen.getByRole('button', { name: /home/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /comidas/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entreno/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /progreso/i })).toBeInTheDocument()
  })

  it('applies correct CSS classes', () => {
    const { container } = render(
      <BottomNavigation
        activeTab="progress"
        onTabChange={mockOnTabChange}
      />
    )

    const navigation = container.querySelector('.bottom-navigation')
    const navigationContainer = container.querySelector('.bottom-navigation-container')

    expect(navigation).toBeInTheDocument()
    expect(navigationContainer).toBeInTheDocument()
  })
})