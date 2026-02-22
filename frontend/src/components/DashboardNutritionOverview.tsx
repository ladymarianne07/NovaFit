import React from 'react'
import { Activity, Droplets, Flame, Zap } from 'lucide-react'
import { MacronutrientData } from '../services/api'

interface DashboardNutritionOverviewProps {
  currentCalories: number
  targetCalories: number
  macroData: MacronutrientData
  macroTargetPercentages?: {
    carbs: number
    protein: number
    fat: number
  }
  className?: string
}

const DashboardNutritionOverview: React.FC<DashboardNutritionOverviewProps> = ({
  currentCalories,
  targetCalories,
  macroData,
  macroTargetPercentages,
  className = ''
}) => {
  const caloriesPercentage = Math.min((currentCalories / targetCalories) * 100, 100)

  const derivedTargetPercentages = {
    carbs: targetCalories > 0 ? (macroData.carbs_target * 4 / targetCalories) * 100 : 0,
    protein: targetCalories > 0 ? (macroData.protein_target * 4 / targetCalories) * 100 : 0,
    fat: targetCalories > 0 ? (macroData.fat_target * 9 / targetCalories) * 100 : 0,
  }

  const targetPercentages = macroTargetPercentages || derivedTargetPercentages

  return (
    <section className={`dashboard-overview-card ${className}`.trim()} aria-label="Resumen nutricional">
      <header className="dashboard-overview-header">
        <h2 className="dashboard-overview-title">Resumen de hoy</h2>
      </header>

      <div className="dashboard-overview-calories">
        <div className="dashboard-overview-calories-icon" aria-hidden="true">
          <Flame size={20} />
        </div>
        <div className="dashboard-overview-calories-main">
          <p className="dashboard-overview-calories-label">Calorías consumidas</p>
          <p className="dashboard-overview-calories-value">
            {currentCalories.toLocaleString('en-US')} <span>cal</span>
          </p>
          <p className="dashboard-overview-calories-target">de {targetCalories.toLocaleString('en-US')} cal</p>
        </div>
      </div>

      <div className="dashboard-overview-progress" role="img" aria-label={`Progreso calórico ${Math.round(caloriesPercentage)}%`}>
        <div className="dashboard-overview-progress-fill" style={{ width: `${caloriesPercentage}%` }} />
      </div>

      <div className="dashboard-overview-macros-grid">
        <article className="dashboard-overview-macro carbs">
          <div className="dashboard-overview-macro-icon" aria-hidden="true">
            <Zap size={14} />
          </div>
          <p className="dashboard-overview-macro-name">Carbohidratos</p>
          <p className="dashboard-overview-macro-value">{Math.round(macroData.carbs)} g</p>
          <p className="dashboard-overview-macro-percentage">Meta {Math.round(targetPercentages.carbs)}% · Progreso {Math.round(macroData.carbs_percentage)}%</p>
        </article>

        <article className="dashboard-overview-macro protein">
          <div className="dashboard-overview-macro-icon" aria-hidden="true">
            <Activity size={14} />
          </div>
          <p className="dashboard-overview-macro-name">Proteínas</p>
          <p className="dashboard-overview-macro-value">{Math.round(macroData.protein)} g</p>
          <p className="dashboard-overview-macro-percentage">Meta {Math.round(targetPercentages.protein)}% · Progreso {Math.round(macroData.protein_percentage)}%</p>
        </article>

        <article className="dashboard-overview-macro fat">
          <div className="dashboard-overview-macro-icon" aria-hidden="true">
            <Droplets size={14} />
          </div>
          <p className="dashboard-overview-macro-name">Grasas</p>
          <p className="dashboard-overview-macro-value">{Math.round(macroData.fat)} g</p>
          <p className="dashboard-overview-macro-percentage">Meta {Math.round(targetPercentages.fat)}% · Progreso {Math.round(macroData.fat_percentage)}%</p>
        </article>
      </div>
    </section>
  )
}

export default DashboardNutritionOverview