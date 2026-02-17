import React, { useEffect, useMemo, useState } from 'react'
import { Brain, Clock3, Sparkles, X } from 'lucide-react'
import { foodAPI } from '../services/api'

interface NutritionModuleProps {
  className?: string
}

interface MealEntry {
  id: string
  title: string
  source: 'ia'
  createdAt: string
  dateKey: string
  quantityGrams: number
  totalCalories: number
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
    () => allMeals.filter((meal) => meal.dateKey === todayKey),
    [allMeals, todayKey]
  )

  const addMeal = (entry: { title: string; quantityGrams: number; totalCalories: number }) => {
    const newMeal: MealEntry = {
      id: `meal-${Date.now()}`,
      title: entry.title,
      source: 'ia',
      createdAt: new Date().toISOString(),
      dateKey: todayKey,
      quantityGrams: entry.quantityGrams,
      totalCalories: entry.totalCalories
    }

    setAllMeals((previousMeals) => [newMeal, ...previousMeals])
  }

  const handleAddFromAi = async () => {
    const content = aiMealInput.trim()
    if (!content) return

    try {
      setIsSubmitting(true)
      setErrorMessage('')

      const parsed = await foodAPI.parseAndCalculate({ text: content })

      addMeal({
        title: parsed.food,
        quantityGrams: parsed.quantity_grams,
        totalCalories: parsed.total_calories
      })

      setAiMealInput('')
      setIsAiComposerOpen(false)
    } catch (error: any) {
      const backendError = error?.response?.data

      if (backendError?.error === 'insufficient_data') {
        setErrorMessage('No pude interpretar la cantidad. Probá con más detalle o una porción.')
      } else if (backendError?.error === 'invalid_domain') {
        setErrorMessage('Ese texto no parece una comida. Ingresá un alimento o plato.')
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
              <button key={meal.id} type="button" className="nutrition-meal-item">
                <div className="nutrition-meal-main">
                  <p className="nutrition-meal-name">{meal.title}</p>
                  <span className="nutrition-meal-time">
                    {new Date(meal.createdAt).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>
                <div className="nutrition-meal-macros">
                  <span>{meal.quantityGrams} g</span>
                  <span>{meal.totalCalories} kcal</span>
                  <span>IA</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </article>
    </section>
  )
}

export default NutritionModule