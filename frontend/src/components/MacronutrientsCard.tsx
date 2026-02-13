import React from 'react'
import { Zap, Activity, Droplets } from 'lucide-react'

interface MacronutrientData {
  carbs: number
  protein: number
  fat: number
  carbs_target: number
  protein_target: number
  fat_target: number
  carbs_percentage: number
  protein_percentage: number
  fat_percentage: number
  total_calories: number
  calories_target: number
  calories_percentage: number
}

interface MacronutrientsCardProps {
  data: MacronutrientData
  className?: string
}

const MacronutrientsCard: React.FC<MacronutrientsCardProps> = ({ 
  data, 
  className = '' 
}) => {
  return (
    <div className={`macronutrients-card ${className}`}>
      {/* Header */}
      <div className="macronutrients-header">
        <h3 className="macronutrients-title">Macronutrientes</h3>
      </div>

      <div className="macronutrients-list">
        {/* Carbs */}
        <div className="macro-item carbs">
          <div className="macro-icon">
            <Zap size={20} />
          </div>
          <div className="macro-info">
            <span className="macro-label">Carbohidratos</span>
            <span className="macro-value">{Math.round(data.carbs)}g</span>
          </div>
          <div className="macro-percentage">
            {Math.round(data.carbs_percentage)}%
          </div>
        </div>

        {/* Protein */}
        <div className="macro-item protein">
          <div className="macro-icon">
            <Activity size={20} />
          </div>
          <div className="macro-info">
            <span className="macro-label">Proteína</span>
            <span className="macro-value">{Math.round(data.protein)}g</span>
          </div>
          <div className="macro-percentage">
            {Math.round(data.protein_percentage)}%
          </div>
        </div>

        {/* Fat */}
        <div className="macro-item fat">
          <div className="macro-icon">
            <Droplets size={20} />
          </div>
          <div className="macro-info">
            <span className="macro-label">Grasas</span>
            <span className="macro-value">{Math.round(data.fat)}g</span>
          </div>
          <div className="macro-percentage">
            {Math.round(data.fat_percentage)}%
          </div>
        </div>
      </div>
    </div>
  )
}

export default MacronutrientsCard