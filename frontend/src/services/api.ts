import axios from 'axios'

// API base configuration
const api = axios.create({
  baseURL: '/api',
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
}

export interface BiometricData {
  age: number
  gender: 'male' | 'female'
  weight: number
  height: number
  activity_level: number
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

export interface SuggestionData {
  suggestion: string
  type: string
  priority: string
  created_at: string
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
}

// Nutrition API endpoints
export const nutritionAPI = {
  getMacronutrients: async (targetDate?: string): Promise<MacronutrientData> => {
    const params = targetDate ? { target_date: targetDate } : {}
    const response = await api.get('/nutrition/macros', { params })
    return response.data
  },

  logMeal: async (mealData: MealLogData): Promise<MealLogResponse> => {
    const response = await api.post('/nutrition/meals', mealData)
    return response.data
  },

  getSuggestions: async (): Promise<SuggestionData> => {
    const response = await api.get('/nutrition/suggestions')
    return response.data
  },
}

export default api