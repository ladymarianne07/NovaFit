import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import BottomNavigation from '../components/BottomNavigation'
import CalorieTracker from '../components/CalorieTracker'
import MacronutrientsCard from '../components/MacronutrientsCard'
import SuggestionCard from '../components/SuggestionCard'
import NutritionModule from '../components/NutritionModule'
import { nutritionAPI, MacronutrientData, SuggestionData } from '../services/api'

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('profile')
  const [macroData, setMacroData] = useState<MacronutrientData | null>(null)
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null)
  const [loading, setLoading] = useState(true)

  const loadNutritionData = async () => {
    try {
      setLoading(true)

      const [macros, suggestionData] = await Promise.all([
        nutritionAPI.getMacronutrients(),
        nutritionAPI.getSuggestions()
      ])

      setMacroData(macros)
      setSuggestion(suggestionData)
    } catch (error) {
      console.error('Failed to load nutrition data:', error)
      setMacroData({
        carbs: 0,
        protein: 0,
        fat: 0,
        carbs_target: user?.daily_caloric_expenditure ? user.daily_caloric_expenditure * 0.5 / 4 : 250,
        protein_target: user?.daily_caloric_expenditure ? user.daily_caloric_expenditure * 0.25 / 4 : 125,
        fat_target: user?.daily_caloric_expenditure ? user.daily_caloric_expenditure * 0.25 / 9 : 56,
        carbs_percentage: 0,
        protein_percentage: 0,
        fat_percentage: 0,
        total_calories: 0,
        calories_target: user?.daily_caloric_expenditure || 2000,
        calories_percentage: 0
      })
    } finally {
      setLoading(false)
    }
  }

  const handleTabChange = (tab: string) => {
    setActiveTab(tab)
  }

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  // Load nutrition data on component mount
  useEffect(() => {
    if (user) {
      loadNutritionData()
    }
  }, [user])

  useEffect(() => {
    const handler = () => {
      if (user) {
        loadNutritionData()
      }
    }

    window.addEventListener('nutrition:updated', handler)
    return () => window.removeEventListener('nutrition:updated', handler)
  }, [user])

  // Calculate current calories (using a mock value for now, could be from daily intake)
  const getCurrentCalories = () => {
    if (macroData) {
      return Math.round(macroData.total_calories)
    }
    return user?.daily_caloric_expenditure ? Math.round(user.daily_caloric_expenditure * 0.78) : 1670
  }

  const getTargetCalories = () => {
    return user?.daily_caloric_expenditure ? Math.round(user.daily_caloric_expenditure) : 2000
  }

  const getUserDisplayName = () => {
    return user?.first_name || user?.email?.split('@')[0] || 'User'
  }

  const renderProfileContent = () => (
    <>
      {/* Header Section - Welcome + Calorie Tracker */}
      <div className="dashboard-header">
        <CalorieTracker
          userName={getUserDisplayName()}
          currentCalories={getCurrentCalories()}
          targetCalories={getTargetCalories()}
          className="mb-6"
        />
      </div>

      {/* Main Content Section */}
      <div className="dashboard-main-content">
        {/* Macronutrients Card */}
        {macroData && (
          <MacronutrientsCard
            data={macroData}
            className="mb-6"
          />
        )}

        {/* Suggestion Card */}
        <SuggestionCard
          suggestion={suggestion}
          loading={loading}
          className="mb-6"
        />
      </div>

      {/* Future content will go here */}
      <div className="dashboard-additional-content">
        {/* Placeholder for future components */}
      </div>
    </>
  )

  const renderPlaceholderSection = (title: string, description: string) => (
    <div className="dashboard-main-content">
      <section className="dashboard-placeholder-card">
        <h2>{title}</h2>
        <p>{description}</p>
      </section>
    </div>
  )

  return (
    <div className="login-container dashboard-with-navigation">
      <div className="login-content">
        {activeTab === 'profile' && renderProfileContent()}
        {activeTab === 'meals' && <NutritionModule className="mb-6" />}
        {activeTab === 'training' && renderPlaceholderSection('Entrenamiento', 'Próximamente vamos a sumar el plan de entrenamiento y seguimiento de sesiones.')}
        {activeTab === 'progress' && renderPlaceholderSection('Progreso', 'Próximamente vamos a sumar métricas, evolución corporal y tendencias.')}
      </div>

      {/* Bottom Navigation */}
      <BottomNavigation 
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onLogout={handleLogout}
      />
    </div>
  )
}

export default Dashboard