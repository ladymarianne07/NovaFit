import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import BottomNavigation from '../components/BottomNavigation'
import SuggestionCard from '../components/SuggestionCard'
import NutritionModule from '../components/NutritionModule'
import ProgressModule from '../components/ProgressModule'
import ProfileBiometricsPanel from '../components/ProfileBiometricsPanel'
import DashboardNutritionOverview from '../components/DashboardNutritionOverview'
import DashboardBodyComposition from '../components/DashboardBodyComposition'
import { nutritionAPI, MacronutrientData, SuggestionData, SkinfoldCalculationResult, usersAPI } from '../services/api'

const Dashboard: React.FC = () => {
  const { user, logout, updateBiometrics } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('dashboard')
  const [macroData, setMacroData] = useState<MacronutrientData | null>(null)
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null)
  const [latestSkinfold, setLatestSkinfold] = useState<SkinfoldCalculationResult | null>(null)
  const [loading, setLoading] = useState(true)

  const loadNutritionData = async () => {
    try {
      setLoading(true)

      const [macros, suggestionData, skinfoldHistory] = await Promise.all([
        nutritionAPI.getMacronutrients(),
        nutritionAPI.getSuggestions(),
        usersAPI.getSkinfoldHistory(1)
      ])

      setMacroData(macros)
      setSuggestion(suggestionData)
      setLatestSkinfold(skinfoldHistory[0] || null)
    } catch (error) {
      console.error('Failed to load nutrition data:', error)
      setMacroData({
        carbs: 0,
        protein: 0,
        fat: 0,
        carbs_target: user?.carbs_target_g ?? (user?.daily_caloric_expenditure ? user.daily_caloric_expenditure * 0.5 / 4 : 250),
        protein_target: user?.protein_target_g ?? (user?.daily_caloric_expenditure ? user.daily_caloric_expenditure * 0.25 / 4 : 125),
        fat_target: user?.fat_target_g ?? (user?.daily_caloric_expenditure ? user.daily_caloric_expenditure * 0.25 / 9 : 56),
        carbs_percentage: 0,
        protein_percentage: 0,
        fat_percentage: 0,
        total_calories: 0,
        calories_target: user?.target_calories || user?.daily_caloric_expenditure || 2000,
        calories_percentage: 0
      })
      setLatestSkinfold(null)
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

  const handleWeightUpdate = async (newWeight: number) => {
    if (!user) {
      throw new Error('No pudimos identificar al usuario actual.')
    }

    if (
      user.age === undefined ||
      user.age === null ||
      !user.gender ||
      user.height === undefined ||
      user.height === null ||
      user.activity_level === undefined ||
      user.activity_level === null
    ) {
      throw new Error('Faltan datos biométricos base (edad, sexo, altura o actividad) para recalcular.')
    }

    await updateBiometrics({
      age: user.age,
      gender: user.gender,
      weight: newWeight,
      height: user.height,
      activity_level: user.activity_level,
    })

    await loadNutritionData()
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
    return user?.target_calories
      ? Math.round(user.target_calories)
      : user?.daily_caloric_expenditure
        ? Math.round(user.daily_caloric_expenditure)
        : 2000
  }

  const renderDashboardContent = () => (
    <section className="dashboard-main-stack" aria-label="Panel principal del dashboard">
      <div className="dashboard-overview-wrap">
        {macroData ? (
          <>
            <DashboardNutritionOverview
              currentCalories={getCurrentCalories()}
              targetCalories={getTargetCalories()}
              macroData={macroData}
            />
            <DashboardBodyComposition
              latestMeasurement={latestSkinfold}
              currentWeight={user?.weight}
              onWeightUpdate={handleWeightUpdate}
            />
          </>
        ) : (
          <section className="dashboard-placeholder-card">
            <div className="loading-stack">
              <div className="neon-loader neon-loader--md" aria-hidden="true"></div>
              <h2>Cargando resumen</h2>
              <p>Estamos preparando tus métricas de calorías y macronutrientes.</p>
            </div>
          </section>
        )}
      </div>

      <div className="dashboard-suggestion-wrap">
        <SuggestionCard suggestion={suggestion} loading={loading} />
      </div>
    </section>
  )

  const renderTrainingPlaceholder = () => (
    <section className="dashboard-tab-content">
      <section className="dashboard-placeholder-card dashboard-placeholder-card-plain">
        <p>Próximamente vamos a sumar el plan de entrenamiento y seguimiento de sesiones.</p>
      </section>
    </section>
  )

  return (
    <div className="login-container dashboard-with-navigation">
      <div className="login-content dashboard-content">
        {activeTab === 'dashboard' && renderDashboardContent()}
        {activeTab === 'profile' && user && (
          <section className="dashboard-tab-content">
            <ProfileBiometricsPanel user={user} />
          </section>
        )}
        {activeTab === 'meals' && (
          <section className="dashboard-tab-content">
            <NutritionModule className="mb-6" />
          </section>
        )}
        {activeTab === 'training' && renderTrainingPlaceholder()}
        {activeTab === 'progress' && (
          <section className="dashboard-tab-content">
            <ProgressModule className="mb-6" />
          </section>
        )}
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