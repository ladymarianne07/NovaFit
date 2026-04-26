import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Brain, Check, Clock3, Mic, MicOff, RefreshCw, Salad, SkipForward, Sparkles, Trash2, UtensilsCrossed, X } from 'lucide-react'
import { foodAPI, nutritionAPI, dietAPI, MealGroupResponse, FoodParseLogResponse, ConfirmMealsRequest, CurrentMealResponse, MealAlternativeResponse, DietMeal, getApiError } from '../services/api'
import AiMealConfirmModal from './AiMealConfirmModal'
import DietModule from './DietModule'

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
  // Proteínas
  chicken: 'pollo',
  'chicken breast': 'pechuga de pollo',
  'chicken thigh': 'muslo de pollo',
  beef: 'carne de res',
  'ground beef': 'carne picada',
  steak: 'bife',
  pork: 'cerdo',
  'pork chop': 'chuleta de cerdo',
  fish: 'pescado',
  salmon: 'salmón',
  tuna: 'atún',
  cod: 'bacalao',
  shrimp: 'camarones',
  egg: 'huevo',
  eggs: 'huevos',
  'egg white': 'clara de huevo',
  'egg whites': 'claras de huevo',
  tofu: 'tofu',
  tempeh: 'tempeh',
  
  // Carbohidratos
  rice: 'arroz',
  white_rice: 'arroz blanco',
  brown_rice: 'arroz integral',
  pasta: 'pasta',
  spaghetti: 'espagueti',
  noodles: 'fideos',
  bread: 'pan',
  'whole wheat bread': 'pan integral',
  'white bread': 'pan blanco',
  toast: 'tostada',
  potato: 'papa',
  potatoes: 'papas',
  sweet_potato: 'batata',
  'sweet potatoes': 'batatas',
  oatmeal: 'avena',
  oats: 'avena',
  quinoa: 'quinoa',
  couscous: 'cuscús',
  
  // Lácteos
  yogurt: 'yogur',
  'greek yogurt': 'yogur griego',
  milk: 'leche',
  'whole milk': 'leche entera',
  'skim milk': 'leche descremada',
  cheese: 'queso',
  'cottage cheese': 'queso cottage',
  'cream cheese': 'queso crema',
  butter: 'manteca',
  cream: 'crema',
  
  // Frutas
  banana: 'banana',
  apple: 'manzana',
  orange: 'naranja',
  strawberry: 'frutilla',
  strawberries: 'frutillas',
  blueberry: 'arándano',
  blueberries: 'arándanos',
  grapes: 'uvas',
  watermelon: 'sandía',
  melon: 'melón',
  pear: 'pera',
  peach: 'durazno',
  pineapple: 'ananá',
  mango: 'mango',
  kiwi: 'kiwi',
  
  // Vegetales
  avocado: 'palta',
  lettuce: 'lechuga',
  tomato: 'tomate',
  onion: 'cebolla',
  garlic: 'ajo',
  carrot: 'zanahoria',
  broccoli: 'brócoli',
  spinach: 'espinaca',
  kale: 'col rizada',
  cucumber: 'pepino',
  pepper: 'pimiento',
  'bell pepper': 'morrón',
  zucchini: 'calabacín',
  eggplant: 'berenjena',
  mushroom: 'champiñón',
  mushrooms: 'champiñones',
  corn: 'maíz',
  peas: 'arvejas',
  
  // Legumbres
  beans: 'porotos',
  'black beans': 'porotos negros',
  'kidney beans': 'porotos colorados',
  lentils: 'lentejas',
  chickpeas: 'garbanzos',
  
  // Grasas
  nuts: 'frutos secos',
  almonds: 'almendras',
  walnuts: 'nueces',
  peanuts: 'maníes',
  'peanut butter': 'manteca de maní',
  'almond butter': 'manteca de almendra',
  olive_oil: 'aceite de oliva',
  'olive oil': 'aceite de oliva',
  'coconut oil': 'aceite de coco',
  'vegetable oil': 'aceite vegetal',
  
  // Otros
  water: 'agua',
  coffee: 'café',
  tea: 'té',
  juice: 'jugo',
  'orange juice': 'jugo de naranja',
  protein: 'proteína',
  'protein shake': 'batido de proteína',
  'protein powder': 'proteína en polvo'
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
  const [moduleTab, setModuleTab] = useState<'meals' | 'diet'>('meals')
  const [previewData, setPreviewData] = useState<FoodParseLogResponse | null>(null)
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false)
  const [aiMealInput, setAiMealInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingMeals, setIsLoadingMeals] = useState(true)
  const [deletingMealId, setDeletingMealId] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [mealsError, setMealsError] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [voiceErrorMessage, setVoiceErrorMessage] = useState('')
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const isStoppingRecognitionRef = useRef(false)

  // Meal tracker state
  const [currentMeal, setCurrentMeal] = useState<CurrentMealResponse | null>(null)
  const [isMealTrackerLoading, setIsMealTrackerLoading] = useState(false)
  const [isLoggingMeal, setIsLoggingMeal] = useState(false)
  const [mealTrackerNoDiet, setMealTrackerNoDiet] = useState(false)

  // Alternative meal state
  const [isLoadingAlternative, setIsLoadingAlternative] = useState(false)
  const [alternativeData, setAlternativeData] = useState<MealAlternativeResponse | null>(null)
  const [isApplyingAlternative, setIsApplyingAlternative] = useState(false)

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

  const fetchCurrentMeal = useCallback(async () => {
    setIsMealTrackerLoading(true)
    setMealTrackerNoDiet(false)
    try {
      const data = await dietAPI.getCurrentMeal()
      setCurrentMeal(data)
      setMealTrackerNoDiet(false)
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 404) {
        setCurrentMeal(null)
        setMealTrackerNoDiet(true)
      }
    } finally {
      setIsMealTrackerLoading(false)
    }
  }, [])

  const handleLogMeal = async (action: 'complete' | 'skip') => {
    setIsLoggingMeal(true)
    try {
      await dietAPI.logMeal({ action })
      await fetchCurrentMeal()
    } finally {
      setIsLoggingMeal(false)
    }
  }

  const handleGetAlternative = async () => {
    setIsLoadingAlternative(true)
    try {
      const data = await dietAPI.getMealAlternative()
      setAlternativeData(data)
    } catch {
      // silently ignore — user sees no modal
    } finally {
      setIsLoadingAlternative(false)
    }
  }

  const handleApplyAlternative = async (scope: 'diet' | 'today') => {
    if (!alternativeData) return
    setIsApplyingAlternative(true)
    try {
      await dietAPI.applyMealAlternative({
        meal_index: alternativeData.meal_index,
        day_type: alternativeData.day_type,
        scope,
        meal: alternativeData.meal,
      })
      setAlternativeData(null)
      await fetchCurrentMeal()
    } finally {
      setIsApplyingAlternative(false)
    }
  }

  useEffect(() => {
    fetchMeals()
    fetchCurrentMeal()
  }, [fetchMeals, fetchCurrentMeal])

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

      const parsed = await foodAPI.parsePreview({ text: content })
      setPreviewData(parsed)
      setIsConfirmModalOpen(true)
    } catch (err: unknown) {
      const backendError = getApiError(err)

      if (backendError.error === 'insufficient_data') {
        setErrorMessage('No pude interpretar la cantidad. Probá con más detalle o una porción.')
      } else if (backendError.error === 'invalid_domain') {
        setErrorMessage('Ese texto no parece una comida. Ingresá un alimento o plato.')
      } else if (backendError.detail === 'gemini_quota_exceeded') {
        setErrorMessage('Se alcanzó el límite diario de uso de IA. Probá nuevamente más tarde o con otra API key/proyecto.')
      } else if (backendError.detail === 'missing_gemini_api_key') {
        setErrorMessage('Falta configurar GEMINI_API_KEY en el backend.')
      } else if (backendError.detail === 'USDA API key is not configured') {
        setErrorMessage('Falta configurar USDA_API_KEY en el backend.')
      } else {
        setErrorMessage('No se pudo calcular la comida ahora. Intentá nuevamente.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConfirmMeals = async (request: ConfirmMealsRequest) => {
    await foodAPI.confirmAndLog(request)
    await fetchMeals()
    window.dispatchEvent(new Event('nutrition:updated'))
    setIsConfirmModalOpen(false)
    setPreviewData(null)
    setAiMealInput('')
    setIsAiComposerOpen(false)
  }

  const handleCloseConfirmModal = () => {
    setIsConfirmModalOpen(false)
    setPreviewData(null)
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
      <div className="module-tabs" role="tablist" aria-label="Secciones de alimentación">
        <button
          type="button"
          role="tab"
          aria-selected={moduleTab === 'meals'}
          className={`module-tab ${moduleTab === 'meals' ? 'active' : ''}`}
          onClick={() => setModuleTab('meals')}
        >
          <Clock3 size={20} />
          <span>Mis Comidas</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={moduleTab === 'diet'}
          className={`module-tab ${moduleTab === 'diet' ? 'active' : ''}`}
          onClick={() => setModuleTab('diet')}
        >
          <Salad size={20} />
          <span>Mi Dieta</span>
        </button>
      </div>

      {moduleTab === 'diet' ? (
        <DietModule />
      ) : (
        <>
          {/* ── Planned meal tracker ── */}
          {isMealTrackerLoading ? (
            <article className="nutrition-card meal-tracker-card" aria-label="Próxima comida planificada">
              <div className="nutrition-empty-state">
                <div className="neon-loader neon-loader--sm" aria-hidden="true" />
              </div>
            </article>
          ) : mealTrackerNoDiet ? (
            <article className="nutrition-card meal-tracker-card meal-tracker-empty" aria-label="Sin dieta">
              <UtensilsCrossed size={28} className="meal-tracker-empty-icon" />
              <p className="meal-tracker-empty-text">Generá tu dieta para activar el seguimiento de comidas</p>
            </article>
          ) : currentMeal && currentMeal.total_meals > 0 ? (
            <article className="nutrition-card meal-tracker-card" aria-label="Próxima comida planificada">
              <div className="meal-tracker-header">
                <div className="meal-tracker-title-group">
                  <span className="meal-tracker-label">Próxima comida</span>
                  <span className="meal-tracker-progress">
                    {currentMeal.meal_index + 1} / {currentMeal.total_meals}
                  </span>
                </div>
              </div>

              {currentMeal.meal ? (
                <>
                  <div className="meal-tracker-name-row">
                    <h4 className="meal-tracker-meal-name">{currentMeal.meal.name}</h4>
                    <span className="meal-tracker-total-kcal">{Math.round(currentMeal.meal.total_calories)} kcal</span>
                  </div>

                  <p className="meal-tracker-ingredients">
                    {(currentMeal.meal.foods ?? []).map(f => `${f.portion} ${f.name}`).join(' · ')}
                  </p>

                  <div className="meal-tracker-macros">
                    <span className="meal-tracker-macro-pill calories">{Math.round(currentMeal.meal.total_calories)} kcal</span>
                    <span className="meal-tracker-macro-pill protein">P: {Math.round(currentMeal.meal.total_protein_g)}g</span>
                    <span className="meal-tracker-macro-pill carbs">Carbos: {Math.round(currentMeal.meal.total_carbs_g)}g</span>
                    <span className="meal-tracker-macro-pill fat">G: {Math.round(currentMeal.meal.total_fat_g)}g</span>
                  </div>

                  <div className="meal-tracker-actions">
                    <button
                      type="button"
                      className="meal-tracker-btn complete"
                      onClick={() => handleLogMeal('complete')}
                      disabled={isLoggingMeal || isLoadingAlternative}
                      aria-label="Marcar comida como completada"
                    >
                      <Check size={16} />
                      {isLoggingMeal ? 'Guardando...' : 'Completé esta comida'}
                    </button>
                    <button
                      type="button"
                      className="meal-tracker-btn skip"
                      onClick={() => handleLogMeal('skip')}
                      disabled={isLoggingMeal || isLoadingAlternative}
                      aria-label="Saltear esta comida"
                    >
                      <SkipForward size={16} />
                      Saltear
                    </button>
                    <button
                      type="button"
                      className="meal-tracker-btn alternative"
                      onClick={handleGetAlternative}
                      disabled={isLoggingMeal || isLoadingAlternative}
                      aria-label="Obtener comida alternativa"
                    >
                      {isLoadingAlternative
                        ? <div className="neon-loader neon-loader--sm" aria-hidden="true" />
                        : <RefreshCw size={14} />
                      }
                      {isLoadingAlternative ? '' : 'Alternativa'}
                    </button>
                  </div>
                </>
              ) : (
                <p className="meal-tracker-done">¡Todas las comidas del día completadas!</p>
              )}
            </article>
          ) : null}

      <div className="nutrition-top-action">
        <button
          type="button"
          className={`nutrition-primary-button${isAiComposerOpen ? '' : ' nutrition-free-meal-btn'}`}
          onClick={() => setIsAiComposerOpen((current) => !current)}
        >
          <Brain size={16} /> {isAiComposerOpen ? 'Cerrar ingreso IA' : 'Registrar comida libre'}
        </button>
      </div>

      {isAiComposerOpen && (
        <article className="nutrition-card nutrition-main-panel" role="region" aria-label="Ingreso por IA">
          <label className="nutrition-ai-label" htmlFor="ai-meal-input">
            Describe tu comida
          </label>
          <p className="nutrition-ai-hint">
            💡 Incluye cantidades en <strong>gramos</strong> o <strong>porciones</strong> para mayor precisión
          </p>
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
            <div className="loading-stack">
              <div className="neon-loader neon-loader--sm" aria-hidden="true" />
              <p>Cargando comidas...</p>
            </div>
          </div>
        ) : todayMeals.length === 0 ? (
          <div className="nutrition-empty-state">
            <p>Hoy todavía no cargaste comidas.</p>
          </div>
        ) : (
          <div className="logged-meals-list">
            {todayMeals.map((meal, index) => {
              const normalizedMealType = normalizeMealType(meal.meal_type ?? 'meal')
              const itemsSummary = meal.items.map((item) => translateFoodName(item.food_name)).join(' · ')
              const mealDisplayLabel = getDisplayMealLabel(meal, index)

              return (
                <article key={meal.id} className="nutrition-card logged-meal-card">
                  <div className="meal-tracker-header">
                    <div className="meal-tracker-title-group">
                      <span className={`logged-meal-badge ${normalizedMealType}`}>
                        {MEAL_TYPE_LABELS[normalizedMealType]}
                      </span>
                    </div>
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

                  <div className="meal-tracker-name-row">
                    <h4 className="meal-tracker-meal-name">{mealDisplayLabel}</h4>
                    <span className="meal-tracker-total-kcal">{meal.total_calories.toFixed(0)} kcal</span>
                  </div>

                  <p className="meal-tracker-ingredients">{itemsSummary}</p>

                  <div className="meal-tracker-macros">
                    <span className="meal-tracker-macro-pill calories">{meal.total_calories.toFixed(0)} kcal</span>
                    <span className="meal-tracker-macro-pill protein">P: {formatMacro(meal.total_protein)}g</span>
                    <span className="meal-tracker-macro-pill carbs">Carbos: {formatMacro(meal.total_carbs)}g</span>
                    <span className="meal-tracker-macro-pill fat">G: {formatMacro(meal.total_fat)}g</span>
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </article>
        </>
      )}

      {/* ══════════ MODAL ALTERNATIVA ══════════ */}
      {alternativeData && (
        <div
          className="alternative-modal-overlay"
          onClick={() => setAlternativeData(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Comida alternativa"
        >
          <div
            className="alternative-modal-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="alternative-modal-header">
              <span className="alternative-modal-title">Alternativa sugerida</span>
              <button
                type="button"
                className="routine-missing-close"
                onClick={() => setAlternativeData(null)}
                aria-label="Cerrar"
              >
                <X size={18} />
              </button>
            </div>

            <div className="alternative-modal-body">
              <div className="meal-tracker-name-row">
                <h4 className="meal-tracker-meal-name">{alternativeData.meal.name}</h4>
                <span className="meal-tracker-total-kcal">{Math.round(alternativeData.meal.total_calories)} kcal</span>
              </div>

              <p className="meal-tracker-ingredients">
                {(alternativeData.meal.foods ?? []).map(f => `${f.portion} ${f.name}`).join(' · ')}
              </p>

              <div className="meal-tracker-macros">
                <span className="meal-tracker-macro-pill calories">{Math.round(alternativeData.meal.total_calories)} kcal</span>
                <span className="meal-tracker-macro-pill protein">P: {Math.round(alternativeData.meal.total_protein_g)}g</span>
                <span className="meal-tracker-macro-pill carbs">Carbos: {Math.round(alternativeData.meal.total_carbs_g)}g</span>
                <span className="meal-tracker-macro-pill fat">G: {Math.round(alternativeData.meal.total_fat_g)}g</span>
              </div>

              {alternativeData.meal.notes && (
                <p className="alternative-modal-notes">{alternativeData.meal.notes}</p>
              )}
            </div>

            <div className="alternative-modal-actions">
              <button
                type="button"
                className="routine-primary-btn"
                onClick={() => handleApplyAlternative('diet')}
                disabled={isApplyingAlternative}
              >
                {isApplyingAlternative ? <div className="neon-loader neon-loader--sm" aria-hidden="true" /> : null}
                Reemplazar en mi dieta
              </button>
              <button
                type="button"
                className="routine-secondary-btn"
                onClick={() => handleApplyAlternative('today')}
                disabled={isApplyingAlternative}
              >
                Solo por hoy (24 hs)
              </button>
              <button
                type="button"
                className="routine-secondary-btn"
                onClick={() => setAlternativeData(null)}
                disabled={isApplyingAlternative}
              >
                Descartar
              </button>
            </div>
          </div>
        </div>
      )}

      <AiMealConfirmModal
        isOpen={isConfirmModalOpen}
        previewData={previewData}
        onClose={handleCloseConfirmModal}
        onConfirm={handleConfirmMeals}
        isSubmitting={isSubmitting}
        translateFoodName={translateFoodName}
      />
    </section>
  )
}

export default NutritionModule