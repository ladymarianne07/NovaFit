import React from 'react'
import { Activity, Droplets, Flame, Zap } from 'lucide-react'
import { MacronutrientData } from '../services/api'

interface DashboardNutritionOverviewProps {
  currentCalories: number
  targetCalories: number
  macroData: MacronutrientData
  className?: string
}

const DashboardNutritionOverview: React.FC<DashboardNutritionOverviewProps> = ({
  currentCalories,
  targetCalories,
  macroData,
  className = ''
}) => {
  const caloriesPercentage = Math.min((currentCalories / targetCalories) * 100, 100)

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
          <p className="dashboard-overview-macro-percentage">{Math.round(macroData.carbs_percentage)}%</p>
        </article>

        <article className="dashboard-overview-macro protein">
          <div className="dashboard-overview-macro-icon" aria-hidden="true">
            <Activity size={14} />
          </div>
          <p className="dashboard-overview-macro-name">Proteínas</p>
          <p className="dashboard-overview-macro-value">{Math.round(macroData.protein)} g</p>
          <p className="dashboard-overview-macro-percentage">{Math.round(macroData.protein_percentage)}%</p>
        </article>

        <article className="dashboard-overview-macro fat">
          <div className="dashboard-overview-macro-icon" aria-hidden="true">
            <Droplets size={14} />
          </div>
          <p className="dashboard-overview-macro-name">Grasas</p>
          <p className="dashboard-overview-macro-value">{Math.round(macroData.fat)} g</p>
          <p className="dashboard-overview-macro-percentage">{Math.round(macroData.fat_percentage)}%</p>
        </article>
      </div>
    </section>
  )
}

export default DashboardNutritionOverview