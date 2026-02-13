import React from 'react'
import { Flame } from 'lucide-react'

interface CalorieTrackerProps {
  userName: string
  currentCalories: number
  targetCalories: number
  className?: string
}

const CalorieTracker: React.FC<CalorieTrackerProps> = ({
  userName,
  currentCalories,
  targetCalories,
  className = ''
}) => {
  const percentage = Math.min((currentCalories / targetCalories) * 100, 100)
  const percentageText = Math.round(percentage)

  return (
    <div className={`calorie-tracker ${className}`}>
      {/* Welcome Message */}
      <div className="calorie-tracker-header">
        <h1 className="calorie-tracker-welcome">¡Bienvenido de vuelta, {userName}!</h1>
      </div>

      {/* Main Calorie Card */}
      <div className="calorie-tracker-card">
        {/* Fire Icon */}
        <div className="calorie-tracker-icon">
          <Flame size={48} />
        </div>

        {/* Calorie Info */}
        <div className="calorie-tracker-content">
          <div className="calorie-tracker-title">
            Gasto Calórico Total
          </div>
          
          <div className="calorie-tracker-main-value">
            {currentCalories.toLocaleString('en-US')}<span className="calorie-tracker-unit">cal</span>
          </div>

          {/* Progress Bar */}
          <div className="calorie-tracker-progress-container">
            <div className="calorie-tracker-progress-bar">
              <div 
                className="calorie-tracker-progress-fill"
                style={{ width: `${percentage}%` }}
              />
            </div>
            <div className="calorie-tracker-percentage">{percentageText}% cal</div>
          </div>

          <div className="calorie-tracker-target">de {targetCalories.toLocaleString('en-US')} cal</div>
        </div>
      </div>
    </div>
  )
}

export default CalorieTracker