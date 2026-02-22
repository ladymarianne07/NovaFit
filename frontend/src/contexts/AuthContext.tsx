import React, { createContext, useContext, useState, useEffect } from 'react'
import { User, authAPI, LoginRequest, RegisterRequest, BiometricData, FitnessObjective } from '../services/api'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  updateBiometrics: (biometrics: BiometricData) => Promise<void>
  updateObjective: (objective: FitnessObjective, aggressivenessLevel: number) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check for existing token and fetch user data
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token')
      if (token) {
        try {
          const userData = await authAPI.getCurrentUser()
          setUser(userData)
        } catch (error) {
          console.error('Failed to fetch user data:', error)
          localStorage.removeItem('access_token')
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      const response = await authAPI.login(credentials)
      localStorage.setItem('access_token', response.access_token)
      
      // Fetch user data after successful login
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
    } catch (error) {
      throw error
    }
  }

  const register = async (userData: RegisterRequest): Promise<void> => {
    try {
      const newUser = await authAPI.register(userData)
      // Auto login after registration
      await login({
        email: userData.email,
        password: userData.password
      })
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
  }

  const updateBiometrics = async (biometrics: BiometricData): Promise<void> => {
    try {
      const updatedUser = await authAPI.updateBiometrics(biometrics)
      setUser(updatedUser)
    } catch (error) {
      throw error
    }
  }

  const updateObjective = async (objective: FitnessObjective, aggressivenessLevel: number): Promise<void> => {
    try {
      const updatedUser = await authAPI.updateObjective(objective, aggressivenessLevel)
      setUser(updatedUser)
    } catch (error) {
      throw error
    }
  }

  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Failed to refresh user data:', error)
    }
  }

  const value = {
    user,
    isLoading,
    login,
    register,
    logout,
    updateBiometrics,
    updateObjective,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default AuthContext