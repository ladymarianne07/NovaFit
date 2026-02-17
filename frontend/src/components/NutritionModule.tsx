import React, { useEffect, useMemo, useState } from 'react'
import { Brain, Clock3, Sparkles, X } from 'lucide-react'
import { foodAPI } from '../services/api'

interface NutritionModuleProps {
  className?: string
}

interface MealEntry {
  id: string
  title: string
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal'
  source: 'ia'
  createdAt: string
  dateKey: string
  totalCalories: number
  totalCarbs: number
  totalProtein: number
  totalFat: number
  itemsSummary: string
}

const MEAL_TYPE_LABELS: Record<MealEntry['mealType'], string> = {
  breakfast: 'Desayuno',
  lunch: 'Almuerzo',
  dinner: 'Cena',
  snack: 'Snack',
  meal: 'Comida'
}

const STORAGE_KEYS = {
  MEALS: 'nova_meals_v1'
} as const

const getTodayKey = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = `${now.getMonth() + 1}`.padStart(2, '0')
  const day = `${now.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

const NutritionModule: React.FC<NutritionModuleProps> = ({ className = '' }) => {
  const [allMeals, setAllMeals] = useState<MealEntry[]>([])
  const [isAiComposerOpen, setIsAiComposerOpen] = useState(false)
  const [aiMealInput, setAiMealInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const todayKey = getTodayKey()

  useEffect(() => {
    const savedMeals = window.localStorage.getItem(STORAGE_KEYS.MEALS)

    if (savedMeals) {
      try {
        const parsedMeals = JSON.parse(savedMeals) as MealEntry[]
        setAllMeals(parsedMeals)
      } catch {
        setAllMeals([])
      }
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEYS.MEALS, JSON.stringify(allMeals))
  }, [allMeals])

  const todayMeals = useMemo(
    () =>
      allMeals
        .filter((meal) => meal.dateKey === todayKey)
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
    [allMeals, todayKey]
  )

  const addMeal = (entry: {
    title: string
    mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal'
    createdAt: string
    totalCalories: number
    totalCarbs: number
    totalProtein: number
    totalFat: number
    itemsSummary: string
  }) => {
    const newMeal: MealEntry = {
      id: `meal-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      title: entry.title,
      mealType: entry.mealType,
      source: 'ia',
      createdAt: entry.createdAt,
      dateKey: todayKey,
      totalCalories: entry.totalCalories,
      totalCarbs: entry.totalCarbs,
      totalProtein: entry.totalProtein,
      totalFat: entry.totalFat,
      itemsSummary: entry.itemsSummary
    }

    setAllMeals((previousMeals) => [newMeal, ...previousMeals])
  }

  const handleAddFromAi = async () => {
    const content = aiMealInput.trim()
    if (!content) return

    try {
      setIsSubmitting(true)
      setErrorMessage('')

      const parsed = await foodAPI.parseAndLog({ text: content })

      parsed.meals.forEach((meal) => {
        addMeal({
          title: meal.meal_label,
          mealType: meal.meal_type,
          createdAt: meal.meal_timestamp,
          totalCalories: meal.total_calories,
          totalCarbs: meal.total_carbs,
          totalProtein: meal.total_protein,
          totalFat: meal.total_fat,
          itemsSummary: meal.items.map((item) => item.food).join(', ')
        })
      })

      window.dispatchEvent(new Event('nutrition:updated'))

      setAiMealInput('')
      setIsAiComposerOpen(false)
    } catch (error: any) {
      const backendError = error?.response?.data

      if (backendError?.error === 'insufficient_data') {
        setErrorMessage('No pude interpretar la cantidad. Probá con más detalle o una porción.')
      } else if (backendError?.error === 'invalid_domain') {
        setErrorMessage('Ese texto no parece una comida. Ingresá un alimento o plato.')
      } else if (backendError?.detail === 'gemini_quota_exceeded') {
        setErrorMessage('Se alcanzó el límite diario de uso de IA. Probá nuevamente más tarde o con otra API key/proyecto.')
      } else if (backendError?.detail === 'missing_gemini_api_key') {
        setErrorMessage('Falta configurar GEMINI_API_KEY en el backend.')
      } else if (backendError?.detail === 'missing_usda_api_key') {
        setErrorMessage('Falta configurar USDA_API_KEY en el backend.')
      } else {
        setErrorMessage('No se pudo calcular la comida ahora. Intentá nuevamente.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const clearMeals = () => {
    setAllMeals((previousMeals) => previousMeals.filter((meal) => meal.dateKey !== todayKey))
  }

  const formatMacro = (value: number) => Math.round(value)

  return (
    <section className={`nutrition-module ${className}`.trim()} aria-label="Módulo de alimentación">
      <header className="nutrition-module-header">
        <h2 className="nutrition-module-title">Comidas</h2>
        <p className="nutrition-module-subtitle">Ingresa tu comida diaria</p>
      </header>

      <div className="nutrition-top-action">
        <button
          type="button"
          className="nutrition-primary-button"
          onClick={() => setIsAiComposerOpen((current) => !current)}
        >
          <Brain size={16} /> {isAiComposerOpen ? 'Cerrar ingreso IA' : 'Ingresar comida por IA'}
        </button>
      </div>

      {isAiComposerOpen && (
        <article className="nutrition-card nutrition-main-panel" role="region" aria-label="Ingreso por IA">
          <label className="nutrition-ai-label" htmlFor="ai-meal-input">
            Describe tu comida
          </label>
          <textarea
            id="ai-meal-input"
            className="nutrition-ai-textarea"
            placeholder="Ej: 200g pollo + 150g arroz + ensalada"
            value={aiMealInput}
            onChange={(event) => setAiMealInput(event.target.value)}
            rows={4}
          />

          {errorMessage && (
            <p className="error-message" role="alert">
              {errorMessage}
            </p>
          )}

          <div className="nutrition-ai-footer">
            <button
              type="button"
              className="nutrition-primary-button"
              onClick={handleAddFromAi}
              disabled={isSubmitting}
            >
              <Sparkles size={16} /> {isSubmitting ? 'Calculando...' : 'Agregar a Mis comidas'}
            </button>
          </div>
        </article>
      )}

      <article className="nutrition-card nutrition-main-panel" role="region" aria-label="Mis comidas">
        <div className="nutrition-card-header">
          <h3 className="nutrition-card-title">
            <Clock3 size={18} /> Mis comidas
          </h3>
          {todayMeals.length > 0 && (
            <button type="button" className="nutrition-chip-button" onClick={clearMeals}>
              <X size={14} /> Limpiar día
            </button>
          )}
        </div>

        {todayMeals.length === 0 ? (
          <div className="nutrition-empty-state">
            <p>Hoy todavía no cargaste comidas.</p>
          </div>
        ) : (
          <div className="nutrition-meals-list">
            {todayMeals.map((meal) => (
              <article key={meal.id} className="nutrition-meal-item">
                <div className="nutrition-meal-top">
                  <div className="nutrition-meal-title-group">
                    <p className="nutrition-meal-name">{meal.title}</p>
                    <span className={`nutrition-meal-type-badge ${meal.mealType}`}>
                      {MEAL_TYPE_LABELS[meal.mealType]}
                    </span>
                  </div>

                  <span className="nutrition-meal-time">
                    {new Date(meal.createdAt).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>

                <p className="nutrition-meal-items-line">
                  <strong>Alimentos:</strong> {meal.itemsSummary}
                </p>

                <div className="nutrition-meal-macro-grid">
                  <div className="nutrition-macro-pill calories">
                    <span className="nutrition-macro-label">Calorías</span>
                    <span className="nutrition-macro-value">{meal.totalCalories.toFixed(0)} kcal</span>
                  </div>
                  <div className="nutrition-macro-pill carbs">
                    <span className="nutrition-macro-label">Carbohidratos</span>
                    <span className="nutrition-macro-value">{formatMacro(meal.totalCarbs)} g</span>
                  </div>
                  <div className="nutrition-macro-pill protein">
                    <span className="nutrition-macro-label">Proteínas</span>
                    <span className="nutrition-macro-value">{formatMacro(meal.totalProtein)} g</span>
                  </div>
                  <div className="nutrition-macro-pill fat">
                    <span className="nutrition-macro-label">Grasas</span>
                    <span className="nutrition-macro-value">{formatMacro(meal.totalFat)} g</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>
    </section>
  )
}

export default NutritionModule