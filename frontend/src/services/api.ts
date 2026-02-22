import axios from 'axios'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

// API base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Types
export type FitnessObjective = 'maintenance' | 'fat_loss' | 'muscle_gain' | 'body_recomp' | 'performance'

export interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  is_active: boolean
  created_at: string
  age?: number
  gender?: 'male' | 'female'
  weight?: number
  height?: number
  activity_level?: number
  bmr?: number
  daily_caloric_expenditure?: number
  // Objective and targets
  objective?: FitnessObjective
  aggressiveness_level?: number
  target_calories?: number
  protein_target_g?: number
  fat_target_g?: number
  carbs_target_g?: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  // All biometric fields are now required for registration
  age: number
  gender: 'male' | 'female'
  weight: number
  height: number
  activity_level: number
  // Fitness objective (optional at registration)
  objective?: FitnessObjective
  aggressiveness_level?: number
}

export interface BiometricData {
  age: number
  gender: 'male' | 'female'
  weight: number
  height: number
  activity_level: number
}

export interface SkinfoldValues {
  chest_mm?: number
  midaxillary_mm?: number
  triceps_mm?: number
  subscapular_mm?: number
  abdomen_mm?: number
  suprailiac_mm?: number
  thigh_mm?: number
}

export interface SkinfoldCalculationRequest extends SkinfoldValues {
  sex: 'male' | 'female'
  age_years: number
  weight_kg?: number
  measurement_unit: 'mm'
}

export interface SkinfoldCalculationResult {
  id?: number
  method: string
  measured_at: string
  sum_of_skinfolds_mm: number
  body_density: number
  body_fat_percent: number
  fat_free_mass_percent: number
  fat_mass_kg?: number | null
  lean_mass_kg?: number | null
  warnings: string[]
}

export interface SkinfoldAIParseResponse {
  parsed: SkinfoldValues
  warnings: string[]
}

// Nutrition Types
export interface MacronutrientData {
  carbs: number
  protein: number
  fat: number
  carbs_target: number
  protein_target: number
  fat_target: number
  carbs_percentage: number
  protein_percentage: number
  fat_percentage: number
  total_calories: number
  calories_target: number
  calories_percentage: number
}

export interface MealLogData {
  meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal'
  food_name: string
  quantity_grams: number
  calories_per_100g: number
  carbs_per_100g: number
  protein_per_100g: number
  fat_per_100g: number
}

export interface MealLogResponse extends MealLogData {
  id: number
  user_id: number
  total_calories: number
  total_carbs: number
  total_protein: number
  total_fat: number
  event_timestamp: string
}

export interface MealItemResponse {
  food_name: string
  quantity_grams: number
  calories_per_100g: number
  carbs_per_100g: number
  protein_per_100g: number
  fat_per_100g: number
  total_calories: number
  total_carbs: number
  total_protein: number
  total_fat: number
}

export interface MealGroupResponse {
  id: string
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal'
  meal_label: string
  event_timestamp: string
  items: MealItemResponse[]
  total_quantity_grams: number
  total_calories: number
  total_carbs: number
  total_protein: number
  total_fat: number
}

export interface SuggestionData {
  suggestion: string
  type: string
  priority: string
  created_at: string
}

// Progress Types
export interface ProgressMetrics {
  peso_inicial_kg?: number
  peso_actual_kg?: number
  delta_peso_kg?: number
  porcentaje_grasa_inicial?: number
  porcentaje_grasa_actual?: number
  delta_grasa_pct?: number
  porcentaje_magra_inicial?: number
  porcentaje_magra_actual?: number
  delta_magra_pct?: number
}

export interface ProgressEvaluationResponse {
  score: number
  estado: string
  resumen: string
  metricas: ProgressMetrics
  periodo_usado: string
  advertencias: string[]
}

export interface TimelinePoint {
  fecha: string
  valor: number
}

export interface DailyCaloriesPoint {
  fecha: string
  consumidas: number
  meta: number
}

export interface DailyMacroPercentagePoint {
  fecha: string
  carbohidratos_pct: number
  proteinas_pct: number
  grasas_pct: number
}

export interface ProgressTimelineSeries {
  peso: TimelinePoint[]
  porcentaje_grasa: TimelinePoint[]
  porcentaje_masa_magra: TimelinePoint[]
  calorias_diarias: DailyCaloriesPoint[]
  macros_porcentaje: DailyMacroPercentagePoint[]
}

export interface ProgressTimelineResponse {
  periodo: string
  rango_inicio: string
  rango_fin: string
  series: ProgressTimelineSeries
  resumen: {
    calorias_semana_real: number
    calorias_semana_meta: number
  }
  advertencias: string[]
}

export interface FoodParseRequest {
  text: string
}

export interface FoodParseResponse {
  food: string
  quantity_grams: number
  calories_per_100g: number
  carbs_per_100g: number
  protein_per_100g: number
  fat_per_100g: number
  total_calories: number
  total_carbs: number
  total_protein: number
  total_fat: number
}

export interface FoodItemDistribution {
  food: string
  quantity_grams: number
  calories_per_100g: number
  carbs_per_100g: number
  protein_per_100g: number
  fat_per_100g: number
  total_calories: number
  total_carbs: number
  total_protein: number
  total_fat: number
}

export interface ParsedMeal {
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal'
  meal_label: string
  meal_timestamp: string
  items: FoodItemDistribution[]
  total_quantity_grams: number
  total_calories: number
  total_carbs: number
  total_protein: number
  total_fat: number
}

export interface FoodParseLogResponse {
  meals: ParsedMeal[]
  total_quantity_grams: number
  total_calories: number
  total_carbs: number
  total_protein: number
  total_fat: number
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

// Auth API endpoints
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', credentials)
    return response.data
  },

  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/users/me')
    return response.data
  },

  updateBiometrics: async (biometrics: BiometricData): Promise<User> => {
    const response = await api.put('/users/me/biometrics', biometrics)
    return response.data
  },

  updateObjective: async (objective: FitnessObjective, aggressiveness_level: number = 2): Promise<User> => {
    const response = await api.put('/users/me/objective', {
      objective,
      aggressiveness_level
    })
    return response.data
  },
}

// Nutrition API endpoints
export const nutritionAPI = {
  getMacronutrients: async (targetDate?: string): Promise<MacronutrientData> => {
    const params = targetDate ? { target_date: targetDate } : {}
    const response = await api.get('/nutrition/macros', { params })
    return response.data
  },

  getMeals: async (targetDate?: string): Promise<MealGroupResponse[]> => {
    const params = targetDate ? { target_date: targetDate } : {}
    const response = await api.get('/nutrition/meals', { params })
    return response.data
  },

  logMeal: async (mealData: MealLogData): Promise<MealLogResponse> => {
    const response = await api.post('/nutrition/meals', mealData)
    return response.data
  },

  deleteMeal: async (mealGroupId: string): Promise<{ status: string }> => {
    const response = await api.delete(`/nutrition/meals/${mealGroupId}`)
    return response.data
  },

  getSuggestions: async (): Promise<SuggestionData> => {
    const response = await api.get('/nutrition/suggestions')
    return response.data
  },
}

export const foodAPI = {
  parseAndCalculate: async (payload: FoodParseRequest): Promise<FoodParseResponse> => {
    const response = await api.post('/food/parse-and-calculate', payload)
    return response.data
  },

  parseAndLog: async (payload: FoodParseRequest): Promise<FoodParseLogResponse> => {
    const response = await api.post('/food/parse-and-log', payload)
    return response.data
  },
}

export const usersAPI = {
  calculateSkinfolds: async (payload: SkinfoldCalculationRequest): Promise<SkinfoldCalculationResult> => {
    const response = await api.post('/users/me/skinfolds', payload)
    return response.data
  },

  getSkinfoldHistory: async (limit: number = 20): Promise<SkinfoldCalculationResult[]> => {
    const response = await api.get('/users/me/skinfolds', { params: { limit } })
    return response.data
  },

  parseSkinfoldsWithAI: async (text: string): Promise<SkinfoldAIParseResponse> => {
    const response = await api.post('/users/me/skinfolds/ai-parse', { text })
    return response.data
  },
}

export const progressAPI = {
  getEvaluation: async (periodo: 'semana' | 'mes' | 'anio' = 'mes'): Promise<ProgressEvaluationResponse> => {
    const response = await api.post('/users/me/progress-evaluation', { periodo })
    return response.data
  },

  getTimeline: async (periodo: 'semana' | 'mes' | 'anio' = 'mes'): Promise<ProgressTimelineResponse> => {
    const response = await api.get('/users/me/progress/timeline', { params: { periodo } })
    return response.data
  },
}

export default api