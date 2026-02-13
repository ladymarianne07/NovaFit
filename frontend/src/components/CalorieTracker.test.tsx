import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import CalorieTracker from './CalorieTracker'

describe('CalorieTracker', () => {
  const defaultProps = {
    userName: 'John Doe',
    currentCalories: 1670,
    targetCalories: 2000
  }

  it('renders user name in welcome message', () => {
    render(<CalorieTracker {...defaultProps} />)
    
    expect(screen.getByText('Welcome back, John Doe!')).toBeInTheDocument()
  })

  it('displays current calorie value correctly', () => {
    render(<CalorieTracker {...defaultProps} />)
    
    // Check for the main calorie value with specific class
    expect(screen.getByText(/1,670/)).toBeInTheDocument()
    // Check that the unit span exists
    const unitElement = document.querySelector('.calorie-tracker-unit')
    expect(unitElement).toHaveTextContent('cal')
  })

  it('displays target calorie value correctly', () => {
    render(<CalorieTracker {...defaultProps} />)
    
    expect(screen.getByText(/of 2,000 cal/)).toBeInTheDocument()
  })

  it('shows correct percentage calculation', () => {
    render(<CalorieTracker {...defaultProps} />)
    
    // 1670/2000 = 0.835 = 83.5%, should round to 84%
    expect(screen.getByText('84% cal')).toBeInTheDocument()
  })

  it('displays Total Caloric Expenditure title', () => {
    render(<CalorieTracker {...defaultProps} />)
    
    expect(screen.getByText('Total Caloric Expenditure')).toBeInTheDocument()
  })

  it('handles large numbers with proper formatting', () => {
    render(
      <CalorieTracker 
        userName="Alice"
        currentCalories={12345}
        targetCalories={15000}
      />
    )
    
    expect(screen.getByText(/12,345/)).toBeInTheDocument()
    expect(screen.getByText(/of 15,000 cal/)).toBeInTheDocument()
  })

  it('handles 100% progress correctly', () => {
    render(
      <CalorieTracker 
        userName="Bob"
        currentCalories={2000}
        targetCalories={2000}
      />
    )
    
    expect(screen.getByText('100% cal')).toBeInTheDocument()
  })

  it('handles over 100% progress correctly (caps at 100%)', () => {
    render(
      <CalorieTracker 
        userName="Charlie"
        currentCalories={2500}
        targetCalories={2000}
      />
    )
    
    expect(screen.getByText('100% cal')).toBeInTheDocument()
  })

  it('handles zero calories correctly', () => {
    render(
      <CalorieTracker 
        userName="Dave"
        currentCalories={0}
        targetCalories={2000}
      />
    )
    
    // Check for zero in the main value area
    const mainValue = document.querySelector('.calorie-tracker-main-value')
    expect(mainValue).toHaveTextContent('0cal')
    expect(screen.getByText('0% cal')).toBeInTheDocument()
  })

  it('applies custom className when provided', () => {
    const { container } = render(
      <CalorieTracker {...defaultProps} className="custom-class" />
    )
    
    const calorieTracker = container.querySelector('.calorie-tracker')
    expect(calorieTracker).toHaveClass('custom-class')
  })

  it('renders flame icon', () => {
    const { container } = render(<CalorieTracker {...defaultProps} />)
    
    const flameIcon = container.querySelector('.calorie-tracker-icon')
    expect(flameIcon).toBeInTheDocument()
  })

  it('sets correct progress bar width style', () => {
    const { container } = render(<CalorieTracker {...defaultProps} />)
    
    const progressFill = container.querySelector('.calorie-tracker-progress-fill')
    // 1670/2000 = 0.835 = 83.5%
    expect(progressFill).toHaveStyle('width: 83.5%')
  })

  it('handles decimal percentages by rounding', () => {
    render(
      <CalorieTracker 
        userName="Eve"
        currentCalories={1567}
        targetCalories={2000}
      />
    )
    
    // 1567/2000 = 0.7835 = 78.35%, should round to 78%
    expect(screen.getByText('78% cal')).toBeInTheDocument()
  })
})