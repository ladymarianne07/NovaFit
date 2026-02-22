import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import BottomNavigation from '../components/BottomNavigation'
import DashboardHeader from '../components/DashboardHeader'
import SuggestionCard from '../components/SuggestionCard'
import NutritionModule from '../components/NutritionModule'
import ProgressModule from '../components/ProgressModule'
import ProfileBiometricsPanel from '../components/ProfileBiometricsPanel'
import DashboardNutritionOverview from '../components/DashboardNutritionOverview'
import DashboardBodyComposition from '../components/DashboardBodyComposition'
import { nutritionAPI, MacronutrientData, SuggestionData, SkinfoldCalculationResult, usersAPI } from '../services/api'

type DashboardTab = 'dashboard' | 'profile' | 'meals' | 'training' | 'progress'

const MAIN_TAB_ORDER: Array<Exclude<DashboardTab, 'profile'>> = ['dashboard', 'meals', 'training', 'progress']

const Dashboard: React.FC = () => {
  const { user, logout, updateBiometrics } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<DashboardTab>('dashboard')
  const [macroData, setMacroData] = useState<MacronutrientData | null>(null)
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null)
  const [latestSkinfold, setLatestSkinfold] = useState<SkinfoldCalculationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [touchStartX, setTouchStartX] = useState<number | null>(null)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

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
        calories_target: user?.custom_target_calories || user?.target_calories || user?.daily_caloric_expenditure || 2000,
        calories_percentage: 0
      })
      setLatestSkinfold(null)
    } finally {
      setLoading(false)
    }
  }

  const handleTabChange = (tab: string) => {
    if ((['dashboard', 'profile', 'meals', 'training', 'progress'] as DashboardTab[]).includes(tab as DashboardTab)) {
      setActiveTab(tab as DashboardTab)
    }
  }

  const handleConfirmLogout = () => {
    setShowLogoutConfirm(false)
    logout()
    navigate('/login', { replace: true })
  }

  const handleRequestLogout = () => {
    setShowLogoutConfirm(true)
  }

  const handleCancelLogout = () => {
    setShowLogoutConfirm(false)
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
    return user?.custom_target_calories
      ? Math.round(user.custom_target_calories)
      : user?.target_calories
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
              macroTargetPercentages={{
                carbs: user?.carbs_target_percent ?? 50,
                protein: user?.protein_target_percent ?? 25,
                fat: user?.fat_target_percent ?? 25,
              }}
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

  const activeMainTab = activeTab === 'profile' ? 'dashboard' : activeTab
  const activeIndex = MAIN_TAB_ORDER.indexOf(activeMainTab)

  const handleTouchStart = (event: React.TouchEvent<HTMLElement>) => {
    setTouchStartX(event.touches[0]?.clientX ?? null)
  }

  const handleTouchEnd = (event: React.TouchEvent<HTMLElement>) => {
    if (touchStartX === null) return

    const endX = event.changedTouches[0]?.clientX ?? touchStartX
    const deltaX = endX - touchStartX
    const swipeThreshold = 45

    if (Math.abs(deltaX) < swipeThreshold) {
      setTouchStartX(null)
      return
    }

    if (deltaX < 0 && activeIndex < MAIN_TAB_ORDER.length - 1) {
      setActiveTab(MAIN_TAB_ORDER[activeIndex + 1])
    } else if (deltaX > 0 && activeIndex > 0) {
      setActiveTab(MAIN_TAB_ORDER[activeIndex - 1])
    }

    setTouchStartX(null)
  }

  return (
    <div className="login-container dashboard-with-navigation">
      <DashboardHeader
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onLogout={handleRequestLogout}
      />

      <div className="login-content dashboard-content">
        {activeTab === 'profile' ? (
          user ? (
            <section className="dashboard-tab-content">
              <ProfileBiometricsPanel user={user} />
            </section>
          ) : (
            <section className="dashboard-tab-content">
              <section className="dashboard-placeholder-card dashboard-placeholder-card-plain">
                <p>Cargando perfil...</p>
              </section>
            </section>
          )
        ) : (
          <section
            className="dashboard-slide-shell"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            aria-label="Navegación principal por secciones"
          >
            <div
              className="dashboard-slide-track"
              style={{ transform: `translate3d(-${activeIndex * 100}%, 0, 0)` }}
            >
              <div className="dashboard-slide-panel" aria-hidden={activeTab !== 'dashboard'}>
                {renderDashboardContent()}
              </div>

              <div className="dashboard-slide-panel" aria-hidden={activeTab !== 'meals'}>
                <section className="dashboard-tab-content">
                  <NutritionModule className="mb-6" />
                </section>
              </div>

              <div className="dashboard-slide-panel" aria-hidden={activeTab !== 'training'}>
                {renderTrainingPlaceholder()}
              </div>

              <div className="dashboard-slide-panel" aria-hidden={activeTab !== 'progress'}>
                <section className="dashboard-tab-content">
                  <ProgressModule className="mb-6" />
                </section>
              </div>
            </div>
          </section>
        )}
      </div>

      {showLogoutConfirm && (
        <div className="dashboard-modal-backdrop" role="presentation" onClick={handleCancelLogout}>
          <div
            className="dashboard-modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="logout-confirm-title"
            aria-describedby="logout-confirm-description"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="logout-confirm-title">¿Seguro que querés salir?</h2>
            <p id="logout-confirm-description">Vas a cerrar sesión en NovaFitness.</p>
            <div className="dashboard-modal-actions">
              <button type="button" className="dashboard-modal-btn ghost" onClick={handleCancelLogout}>
                Cancelar
              </button>
              <button type="button" className="dashboard-modal-btn danger" onClick={handleConfirmLogout}>
                Sí, salir
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <BottomNavigation 
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />
    </div>
  )
}

export default Dashboard