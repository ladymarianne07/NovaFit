import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Brain, Clock3, Sparkles, Trash2 } from 'lucide-react'
import { foodAPI, nutritionAPI, MealGroupResponse } from '../services/api'

interface NutritionModuleProps {
  className?: string
}

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal'

const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: 'Desayuno',
  lunch: 'Almuerzo',
  dinner: 'Cena',
  snack: 'Snack',
  meal: 'Comida'
}

const normalizeMealType = (value: string): MealType => {
  const normalized = value?.toLowerCase()
  if (normalized === 'breakfast' || normalized === 'lunch' || normalized === 'dinner' || normalized === 'snack') {
    return normalized
  }
  return 'meal'
}

const NutritionModule: React.FC<NutritionModuleProps> = ({ className = '' }) => {
  const [meals, setMeals] = useState<MealGroupResponse[]>([])
  const [isAiComposerOpen, setIsAiComposerOpen] = useState(false)
  const [aiMealInput, setAiMealInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingMeals, setIsLoadingMeals] = useState(true)
  const [deletingMealId, setDeletingMealId] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [mealsError, setMealsError] = useState('')

  const fetchMeals = useCallback(async () => {
    try {
      setIsLoadingMeals(true)
      setMealsError('')
      const data = await nutritionAPI.getMeals()
      setMeals(data)
    } catch {
      setMealsError('No se pudieron cargar las comidas.')
    } finally {
      setIsLoadingMeals(false)
    }
  }, [])

  useEffect(() => {
    fetchMeals()
  }, [fetchMeals])

  useEffect(() => {
    const handler = () => {
      fetchMeals()
    }
    window.addEventListener('nutrition:updated', handler)
    return () => window.removeEventListener('nutrition:updated', handler)
  }, [fetchMeals])

  const todayMeals = useMemo(
    () =>
      [...meals].sort(
        (a, b) => new Date(b.event_timestamp).getTime() - new Date(a.event_timestamp).getTime()
      ),
    [meals]
  )

  const handleAddFromAi = async () => {
    const content = aiMealInput.trim()
    if (!content) return

    try {
      setIsSubmitting(true)
      setErrorMessage('')

      await foodAPI.parseAndLog({ text: content })
      await fetchMeals()

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

  const handleDeleteMeal = async (mealGroupId: string) => {
    try {
      setDeletingMealId(mealGroupId)
      await nutritionAPI.deleteMeal(mealGroupId)
      setMeals((previousMeals) => previousMeals.filter((meal) => meal.id !== mealGroupId))
      window.dispatchEvent(new Event('nutrition:updated'))
    } catch {
      setMealsError('No se pudo eliminar la comida.')
    } finally {
      setDeletingMealId(null)
    }
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
        </div>

        {mealsError && (
          <p className="error-message" role="alert">
            {mealsError}
          </p>
        )}

        {isLoadingMeals ? (
          <div className="nutrition-empty-state">
            <p>Cargando comidas...</p>
          </div>
        ) : todayMeals.length === 0 ? (
          <div className="nutrition-empty-state">
            <p>Hoy todavía no cargaste comidas.</p>
          </div>
        ) : (
          <div className="nutrition-meals-list">
            {todayMeals.map((meal) => {
              const normalizedMealType = normalizeMealType(meal.meal_type ?? 'meal')
              const itemsSummary = meal.items.map((item) => item.food_name).join(', ')

              return (
                <article key={meal.id} className="nutrition-meal-item">
                  <div className="nutrition-meal-top">
                    <div className="nutrition-meal-title-group">
                      <p className="nutrition-meal-name">{meal.meal_label}</p>
                      <span className={`nutrition-meal-type-badge ${normalizedMealType}`}>
                        {MEAL_TYPE_LABELS[normalizedMealType]}
                      </span>
                    </div>

                    <div className="nutrition-meal-actions">
                      <span className="nutrition-meal-time">
                        {new Date(meal.event_timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                      <button
                        type="button"
                        className="nutrition-meal-delete"
                        onClick={() => handleDeleteMeal(meal.id)}
                        disabled={deletingMealId === meal.id}
                        aria-label="Eliminar comida"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <p className="nutrition-meal-items-line">
                    <strong>Alimentos:</strong> {itemsSummary}
                  </p>

                  <div className="nutrition-meal-macro-grid">
                    <div className="nutrition-macro-pill calories">
                      <span className="nutrition-macro-label">Calorías</span>
                      <span className="nutrition-macro-value">{meal.total_calories.toFixed(0)} kcal</span>
                    </div>
                    <div className="nutrition-macro-pill carbs">
                      <span className="nutrition-macro-label">Carbohidratos</span>
                      <span className="nutrition-macro-value">{formatMacro(meal.total_carbs)} g</span>
                    </div>
                    <div className="nutrition-macro-pill protein">
                      <span className="nutrition-macro-label">Proteínas</span>
                      <span className="nutrition-macro-value">{formatMacro(meal.total_protein)} g</span>
                    </div>
                    <div className="nutrition-macro-pill fat">
                      <span className="nutrition-macro-label">Grasas</span>
                      <span className="nutrition-macro-value">{formatMacro(meal.total_fat)} g</span>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </article>
    </section>
  )
}

export default NutritionModule