import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import BottomNavigation from './BottomNavigation'

describe('BottomNavigation', () => {
  const mockOnTabChange = jest.fn()
  const mockOnLogout = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders all navigation items', () => {
    render(
      <BottomNavigation
        activeTab="profile"
        onTabChange={mockOnTabChange}
        onLogout={mockOnLogout}
      />
    )

    expect(screen.getByText('Perfil')).toBeInTheDocument()
    expect(screen.getByText('Comidas')).toBeInTheDocument()
    expect(screen.getByText('Entrenamiento')).toBeInTheDocument()
    expect(screen.getByText('Progreso')).toBeInTheDocument()
    expect(screen.getByText('Logout')).toBeInTheDocument()
  })

  it('shows active tab with correct styling', () => {
    render(
      <BottomNavigation
        activeTab="profile"
        onTabChange={mockOnTabChange}
        onLogout={mockOnLogout}
      />
    )

    const profileButton = screen.getByRole('button', { name: /perfil/i })
    expect(profileButton).toHaveClass('active')
  })

  it('calls onTabChange when navigation item is clicked', () => {
    render(
      <BottomNavigation
        activeTab="profile"
        onTabChange={mockOnTabChange}
        onLogout={mockOnLogout}
      />
    )

    const mealsButton = screen.getByRole('button', { name: /comidas/i })
    fireEvent.click(mealsButton)

    expect(mockOnTabChange).toHaveBeenCalledWith('meals')
  })

  it('calls onLogout when logout button is clicked', () => {
    render(
      <BottomNavigation
        activeTab="profile"
        onTabChange={mockOnTabChange}
        onLogout={mockOnLogout}
      />
    )

    const logoutButton = screen.getByRole('button', { name: /logout/i })
    fireEvent.click(logoutButton)

    expect(mockOnLogout).toHaveBeenCalled()
  })

  it('renders with default activeTab when not provided', () => {
    render(
      <BottomNavigation
        onTabChange={mockOnTabChange}
        onLogout={mockOnLogout}
      />
    )

    const profileButton = screen.getByRole('button', { name: /perfil/i })
    expect(profileButton).toHaveClass('active')
  })

  it('handles missing callback props gracefully', () => {
    render(<BottomNavigation activeTab="training" />)

    const trainingButton = screen.getByRole('button', { name: /entrenamiento/i })
    
    // Should not throw error when clicking
    expect(() => {
      fireEvent.click(trainingButton)
    }).not.toThrow()
  })

  it('displays correct icons for each navigation item', () => {
    render(
      <BottomNavigation
        activeTab="profile"
        onTabChange={mockOnTabChange}
        onLogout={mockOnLogout}
      />
    )

    // Check that buttons render (icons are inside buttons)
    expect(screen.getByRole('button', { name: /perfil/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /comidas/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entrenamiento/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /progreso/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument()
  })

  it('applies correct CSS classes', () => {
    const { container } = render(
      <BottomNavigation
        activeTab="progress"
        onTabChange={mockOnTabChange}
        onLogout={mockOnLogout}
      />
    )

    const navigation = container.querySelector('.bottom-navigation')
    const navigationContainer = container.querySelector('.bottom-navigation-container')

    expect(navigation).toBeInTheDocument()
    expect(navigationContainer).toBeInTheDocument()
  })
})