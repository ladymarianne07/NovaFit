import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Brain, ChevronLeft, ChevronRight, Clock3, Mic, MicOff, Sparkles, Trash2 } from 'lucide-react'
import { foodAPI, nutritionAPI, MealGroupResponse } from '../services/api'

interface NutritionModuleProps {
  className?: string
}

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal'

interface SpeechRecognitionAlternative {
  transcript: string
}

interface SpeechRecognitionResult {
  isFinal: boolean
  length: number
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionResultList {
  length: number
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEvent {
  error: string
}

interface SpeechRecognitionInstance {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionInstance
}

interface SpeechEnabledWindow extends Window {
  SpeechRecognition?: SpeechRecognitionConstructor
  webkitSpeechRecognition?: SpeechRecognitionConstructor
}

const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: 'Desayuno',
  lunch: 'Almuerzo',
  dinner: 'Cena',
  snack: 'Snack',
  meal: 'Comida'
}

const FOOD_NAME_TRANSLATIONS: Record<string, string> = {
  chicken: 'pollo',
  'chicken breast': 'pechuga de pollo',
  beef: 'carne de res',
  fish: 'pescado',
  salmon: 'salmón',
  tuna: 'atún',
  egg: 'huevo',
  eggs: 'huevos',
  rice: 'arroz',
  white_rice: 'arroz blanco',
  brown_rice: 'arroz integral',
  pasta: 'pasta',
  bread: 'pan',
  potato: 'papa',
  potatoes: 'papas',
  sweet_potato: 'batata',
  oatmeal: 'avena',
  yogurt: 'yogur',
  milk: 'leche',
  cheese: 'queso',
  banana: 'banana',
  apple: 'manzana',
  orange: 'naranja',
  strawberry: 'frutilla',
  strawberries: 'frutillas',
  avocado: 'palta',
  lettuce: 'lechuga',
  tomato: 'tomate',
  onion: 'cebolla',
  carrot: 'zanahoria',
  broccoli: 'brócoli',
  spinach: 'espinaca',
  beans: 'porotos',
  lentils: 'lentejas',
  nuts: 'frutos secos',
  olive_oil: 'aceite de oliva',
  water: 'agua'
}

const normalizeMealType = (value: string): MealType => {
  const normalized = value?.toLowerCase()
  if (normalized === 'breakfast' || normalized === 'lunch' || normalized === 'dinner' || normalized === 'snack') {
    return normalized
  }
  return 'meal'
}

const normalizeTextKey = (value: string) =>
  value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .trim()
    .toLowerCase()

const translateFoodName = (foodName: string) => {
  if (!foodName) return ''

  const normalizedFullName = normalizeTextKey(foodName).replace(/[\s-]+/g, '_')
  const fullNameTranslation = FOOD_NAME_TRANSLATIONS[normalizedFullName]

  if (fullNameTranslation) {
    return fullNameTranslation
  }

  const normalizedSimple = normalizeTextKey(foodName)
  const simpleTranslation = FOOD_NAME_TRANSLATIONS[normalizedSimple]

  if (simpleTranslation) {
    return simpleTranslation
  }

  return foodName
}

const getDisplayMealLabel = (meal: MealGroupResponse, index: number) => {
  const normalizedMealType = normalizeMealType(meal.meal_type ?? 'meal')
  const rawLabel = meal.meal_label?.trim() ?? ''

  if (!rawLabel) {
    return normalizedMealType === 'meal' ? `Comida ${index + 1}` : MEAL_TYPE_LABELS[normalizedMealType]
  }

  const normalizedLabel = normalizeTextKey(rawLabel)

  if (normalizedLabel === 'breakfast') return 'Desayuno'
  if (normalizedLabel === 'lunch') return 'Almuerzo'
  if (normalizedLabel === 'dinner') return 'Cena'
  if (normalizedLabel === 'snack') return 'Snack'

  if (normalizedMealType === 'meal') {
    const genericMealMatch = normalizedLabel.match(/^(meal|comida)\s*(\d+)?$/)
    if (genericMealMatch) {
      const mealNumber = genericMealMatch[2] ? Number(genericMealMatch[2]) : index + 1
      return `Comida ${mealNumber}`
    }
  }

  return rawLabel
}

const getSpeechRecognitionConstructor = (): SpeechRecognitionConstructor | null => {
  if (typeof window === 'undefined') {
    return null
  }

  const speechWindow = window as SpeechEnabledWindow
  return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null
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
  const [activeMealIndex, setActiveMealIndex] = useState(0)
  const [isListening, setIsListening] = useState(false)
  const [voiceErrorMessage, setVoiceErrorMessage] = useState('')
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const isStoppingRecognitionRef = useRef(false)

  const isVoiceInputSupported = useMemo(() => getSpeechRecognitionConstructor() !== null, [])

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

  useEffect(() => {
    setActiveMealIndex((currentIndex) => {
      if (todayMeals.length === 0) {
        return 0
      }

      return Math.min(currentIndex, todayMeals.length - 1)
    })
  }, [todayMeals.length])

  useEffect(
    () => () => {
      if (recognitionRef.current) {
        isStoppingRecognitionRef.current = true
        recognitionRef.current.stop()
      }
    },
    []
  )

  const handleToggleVoiceInput = () => {
    if (!isVoiceInputSupported) {
      setVoiceErrorMessage('Tu navegador no soporta ingreso por voz. Probá con Chrome o Edge actualizado.')
      return
    }

    if (isListening && recognitionRef.current) {
      isStoppingRecognitionRef.current = true
      recognitionRef.current.stop()
      return
    }

    const SpeechRecognition = getSpeechRecognitionConstructor()

    if (!SpeechRecognition) {
      setVoiceErrorMessage('No se pudo iniciar el reconocimiento de voz en este dispositivo.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'es-ES'
    recognition.interimResults = true
    recognition.continuous = false

    recognition.onresult = (event) => {
      const finalSegments: string[] = []

      for (let index = 0; index < event.results.length; index += 1) {
        const result = event.results[index]
        if (result.isFinal && result[0]?.transcript) {
          finalSegments.push(result[0].transcript.trim())
        }
      }

      const finalTranscript = finalSegments.join(' ').trim()
      if (!finalTranscript) {
        return
      }

      setAiMealInput((currentText) => {
        if (!currentText.trim()) {
          return finalTranscript
        }

        return `${currentText.trim()} ${finalTranscript}`
      })
    }

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setVoiceErrorMessage('No diste permisos de micrófono. Habilítalos para usar ingreso por voz.')
      } else if (event.error === 'no-speech') {
        setVoiceErrorMessage('No detecté voz. Probá nuevamente y hablá un poco más cerca del micrófono.')
      } else if (event.error === 'audio-capture') {
        setVoiceErrorMessage('No se detectó micrófono disponible en el dispositivo.')
      } else {
        setVoiceErrorMessage('No pudimos procesar el audio. Intentá de nuevo en unos segundos.')
      }
    }

    recognition.onend = () => {
      recognitionRef.current = null
      if (!isStoppingRecognitionRef.current) {
        setIsListening(false)
        return
      }

      isStoppingRecognitionRef.current = false
      setIsListening(false)
    }

    recognitionRef.current = recognition
    setVoiceErrorMessage('')

    try {
      recognition.start()
      setIsListening(true)
    } catch {
      setVoiceErrorMessage('No se pudo iniciar el micrófono. Recargá la página e intentá nuevamente.')
      setIsListening(false)
      recognitionRef.current = null
    }
  }

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
            onChange={(event) => {
              setVoiceErrorMessage('')
              setAiMealInput(event.target.value)
            }}
            rows={4}
          />

          <div className="nutrition-voice-controls">
            <button
              type="button"
              className={`nutrition-chip-button nutrition-voice-button ${isListening ? 'is-listening' : ''}`.trim()}
              onClick={handleToggleVoiceInput}
              disabled={!isVoiceInputSupported || isSubmitting}
            >
              {isListening ? <MicOff size={15} /> : <Mic size={15} />}
              {isListening ? 'Detener voz' : 'Ingresar por voz'}
            </button>

            <p className="nutrition-voice-hint">
              {isVoiceInputSupported
                ? isListening
                  ? 'Escuchando... cuando termines, presiona detener.'
                  : 'Presioná y dictá tu comida en español.'
                : 'Ingreso por voz no disponible en este navegador.'}
            </p>
          </div>

          {voiceErrorMessage && (
            <p className="error-message" role="alert">
              {voiceErrorMessage}
            </p>
          )}

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
          <div className="nutrition-meals-slider">
            <div className="nutrition-slider-controls">
              <button
                type="button"
                className="nutrition-slider-nav"
                onClick={() => setActiveMealIndex((current) => Math.max(current - 1, 0))}
                disabled={activeMealIndex === 0}
                aria-label="Ver comida anterior"
              >
                <ChevronLeft size={16} />
              </button>

              <p className="nutrition-slider-indicator">
                Comida {activeMealIndex + 1} de {todayMeals.length}
              </p>

              <button
                type="button"
                className="nutrition-slider-nav"
                onClick={() => setActiveMealIndex((current) => Math.min(current + 1, todayMeals.length - 1))}
                disabled={activeMealIndex === todayMeals.length - 1}
                aria-label="Ver siguiente comida"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div className="nutrition-slider-window" aria-live="polite">
              <div
                className="nutrition-slider-track"
                style={{ transform: `translateX(-${activeMealIndex * 100}%)` }}
              >
                {todayMeals.map((meal, index) => {
                  const normalizedMealType = normalizeMealType(meal.meal_type ?? 'meal')
                  const itemsSummary = meal.items.map((item) => translateFoodName(item.food_name)).join(', ')
                  const mealDisplayLabel = getDisplayMealLabel(meal, index)

                  return (
                    <article key={meal.id} className="nutrition-meal-item">
                      <div className="nutrition-meal-top">
                        <div className="nutrition-meal-title-group">
                          <p className="nutrition-meal-name">{mealDisplayLabel}</p>
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
            </div>

            <div className="nutrition-slider-dots" role="tablist" aria-label="Selector de comidas">
              {todayMeals.map((meal, index) => (
                <button
                  key={meal.id}
                  type="button"
                  className={`nutrition-slider-dot ${index === activeMealIndex ? 'active' : ''}`}
                  onClick={() => setActiveMealIndex(index)}
                  aria-label={`Ir a comida ${index + 1}`}
                  aria-current={index === activeMealIndex}
                />
              ))}
            </div>
          </div>
        )}
      </article>
    </section>
  )
}

export default NutritionModule