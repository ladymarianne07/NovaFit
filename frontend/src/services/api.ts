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
export type UserRole = 'student' | 'trainer'

export interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  role: UserRole
  uses_app_for_self?: boolean
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
  custom_target_calories?: number
  carbs_target_percent?: number
  protein_target_percent?: number
  fat_target_percent?: number
}

export interface NutritionTargetsUpdateRequest {
  custom_target_calories: number
  carbs_target_percent: number
  protein_target_percent: number
  fat_target_percent: number
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
  role?: UserRole
  uses_app_for_self?: boolean
  // Biometric fields — required for students and trainers who use the app for themselves
  age?: number
  gender?: 'male' | 'female'
  weight?: number
  height?: number
  activity_level?: number
  // Fitness objective (optional at registration)
  objective?: FitnessObjective
  aggressiveness_level?: number
}

export interface EnableSelfUseRequest {
  age: number
  gender: 'male' | 'female'
  weight: number
  height: number
  activity_level: number
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

// Workout Types
export interface WorkoutSessionBlockCreate {
  activity: string
  duration_minutes: number
  intensity?: string
}

export interface WorkoutSessionCreateRequest {
  session_date: string
  source?: 'ai' | 'manual' | 'wearable'
  status?: 'draft' | 'final' | 'discarded'
  raw_input?: string
  ai_output?: Record<string, unknown>
  weight_kg?: number
  blocks: WorkoutSessionBlockCreate[]
}

export interface WorkoutSessionBlockResponse {
  id: number
  block_order: number
  activity_id: number
  duration_minutes: number
  intensity_level?: string | null
  intensity_raw?: string | null
  weight_kg_used?: number | null
  met_used_min?: number | null
  met_used_max?: number | null
  correction_factor: number
  kcal_min?: number | null
  kcal_max?: number | null
  kcal_est?: number | null
}

export interface WorkoutSessionResponse {
  id: number
  user_id: number
  session_date: string
  source: string
  status: string
  total_kcal_min?: number | null
  total_kcal_max?: number | null
  total_kcal_est?: number | null
  blocks: WorkoutSessionBlockResponse[]
}

export interface WorkoutDailyEnergyResponse {
  user_id: number
  log_date: string
  exercise_kcal_min: number
  exercise_kcal_max: number
  exercise_kcal_est: number
  intake_kcal: number
  net_kcal_est: number
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

  updateNutritionTargets: async (payload: NutritionTargetsUpdateRequest): Promise<User> => {
    const response = await api.put('/users/me/nutrition-targets', payload)
    return response.data
  },

  enableSelfUse: async (payload: EnableSelfUseRequest): Promise<User> => {
    const response = await api.post('/users/me/enable-self-use', payload)
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

  parsePreview: async (payload: FoodParseRequest): Promise<FoodParseLogResponse> => {
    const response = await api.post('/food/parse-preview', payload)
    return response.data
  },

  confirmAndLog: async (payload: ConfirmMealsRequest): Promise<FoodParseLogResponse> => {
    const response = await api.post('/food/confirm-and-log', payload)
    return response.data
  },
}

export const workoutAPI = {
  createSession: async (payload: WorkoutSessionCreateRequest): Promise<WorkoutSessionResponse> => {
    const response = await api.post('/v1/sessions', payload)
    return response.data
  },

  listSessions: async (sessionDate?: string): Promise<WorkoutSessionResponse[]> => {
    const params = sessionDate ? { session_date: sessionDate } : {}
    const response = await api.get('/v1/sessions', { params })
    return response.data
  },

  deleteSession: async (sessionId: number): Promise<{ status: string }> => {
    const response = await api.delete(`/v1/sessions/${sessionId}`)
    return response.data
  },

  getDailyEnergy: async (targetDate: string): Promise<WorkoutDailyEnergyResponse> => {
    const response = await api.get(`/v1/days/${targetDate}/energy`)
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

// Routine Types
export interface RoutineExercise {
  id: string
  name: string
  muscle?: string
  group?: string
  sets?: string
  reps?: string
  rest_seconds?: number
  estimated_calories: number
  notes?: string
}

export interface RoutineSession {
  id: string
  label: string
  title: string
  day_label?: string
  color?: string
  estimated_calories_per_session: number
  exercises: RoutineExercise[]
}

export interface RoutineHealthAnalysis {
  conditions_detected: string[]
  contraindications_applied: string[]
  adaptations: string[]
  warning?: string | null
}

export interface UserRoutineResponse {
  id: number
  status: 'processing' | 'ready' | 'error'
  source_filename?: string
  source_type?: 'file' | 'ai_text'
  html_content?: string
  error_message?: string
  routine_data?: {
    sessions: RoutineSession[]
    title?: string
    subtitle?: string
  }
  health_analysis?: RoutineHealthAnalysis
  intake_data?: Record<string, unknown>
  current_session_index: number
}

export interface RoutineIntakeData {
  objective: 'fat_loss' | 'body_recomp' | 'muscle_gain'
  duration_months: number
  health_conditions: string
  medications: string
  injuries: string
  preferred_exercises: string
  frequency_days: '2' | '3-4' | '5+'
  experience_level: 'principiante' | 'intermedio' | 'avanzado'
  equipment: 'gimnasio completo' | 'mancuernas en casa' | 'bandas elásticas' | 'peso corporal'
  session_duration_minutes: number
}

export interface RoutineGenerateRequest {
  intake: RoutineIntakeData
  free_text: string
}

export interface RoutineEditRequest {
  edit_instruction: string
}

export interface RoutineLogSessionRequest {
  session_id: string
  session_date: string
  skipped_exercise_ids: string[]
}

export interface RoutineAdvanceSessionRequest {
  action: 'complete' | 'skip'
}

export interface ConfirmMealsRequest {
  items: Array<{
    meal_type: string
    meal_label: string
    food_name: string
    quantity_grams: number
    calories_per_100g: number
    carbs_per_100g: number
    protein_per_100g: number
    fat_per_100g: number
  }>
}

export const routineAPI = {
  getActive: async (): Promise<UserRoutineResponse> => {
    const response = await api.get('/v1/routines/active')
    return response.data
  },

  upload: async (file: File): Promise<UserRoutineResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/v1/routines/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  generateFromText: async (payload: RoutineGenerateRequest): Promise<UserRoutineResponse> => {
    const response = await api.post('/v1/routines/generate', payload)
    return response.data
  },

  editRoutine: async (payload: RoutineEditRequest): Promise<UserRoutineResponse> => {
    const response = await api.post('/v1/routines/edit', payload)
    return response.data
  },

  logSession: async (payload: RoutineLogSessionRequest): Promise<WorkoutSessionResponse> => {
    const response = await api.post('/v1/routines/log-session', payload)
    return response.data
  },

  advanceSession: async (payload: RoutineAdvanceSessionRequest): Promise<UserRoutineResponse> => {
    const response = await api.post('/v1/routines/advance-session', payload)
    return response.data
  },
}

// Trainer Types
export interface TrainerInviteResponse {
  id: number
  code: string
  expires_at: string
  created_at: string
}

export interface StudentSummary {
  id: number
  email: string
  first_name?: string
  last_name?: string
  linked_at: string
  objective?: string
  target_calories?: number
  weight_kg?: number
}

export interface NotificationResponse {
  id: number
  type: string
  title: string
  body: string
  is_read: boolean
  created_at: string
}

export interface NotificationListResponse {
  notifications: NotificationResponse[]
  unread_count: number
}

export const trainerAPI = {
  generateInvite: async (): Promise<TrainerInviteResponse> => {
    const response = await api.post('/trainer/invite')
    return response.data
  },

  getCurrentInvite: async (): Promise<TrainerInviteResponse> => {
    const response = await api.get('/trainer/invite')
    return response.data
  },

  listStudents: async (): Promise<StudentSummary[]> => {
    const response = await api.get('/trainer/students')
    return response.data
  },

  getStudent: async (studentId: number): Promise<User> => {
    const response = await api.get(`/trainer/students/${studentId}`)
    return response.data
  },

  unlinkStudent: async (studentId: number): Promise<void> => {
    await api.delete(`/trainer/students/${studentId}`)
  },

  updateStudentBiometrics: async (studentId: number, biometrics: BiometricData): Promise<User> => {
    const response = await api.put(`/trainer/students/${studentId}/biometrics`, biometrics)
    return response.data
  },

  updateStudentObjective: async (
    studentId: number,
    objective: FitnessObjective,
    aggressiveness_level: number = 2,
  ): Promise<User> => {
    const response = await api.put(`/trainer/students/${studentId}/objective`, {
      objective,
      aggressiveness_level,
    })
    return response.data
  },

  getStudentMacros: async (studentId: number, targetDate?: string): Promise<MacronutrientData> => {
    const params = targetDate ? { target_date: targetDate } : {}
    const response = await api.get(`/trainer/students/${studentId}/macros`, { params })
    return response.data
  },

  getStudentSkinfolds: async (studentId: number, limit = 10): Promise<SkinfoldCalculationResult[]> => {
    const response = await api.get(`/trainer/students/${studentId}/skinfolds`, { params: { limit } })
    return response.data
  },
}

export const inviteAPI = {
  acceptInvite: async (code: string): Promise<{ status: string }> => {
    const response = await api.post('/invite/accept', { code })
    return response.data
  },
}

export const notificationsAPI = {
  getNotifications: async (): Promise<NotificationListResponse> => {
    const response = await api.get('/notifications')
    return response.data
  },

  markAsRead: async (notificationId: number): Promise<void> => {
    await api.put(`/notifications/${notificationId}/read`)
  },

  markAllAsRead: async (): Promise<void> => {
    await api.put('/notifications/read-all')
  },
}

export default api