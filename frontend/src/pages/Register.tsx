import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, User, Zap, Scale, Activity, Calendar, Ruler } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/UI/Button'
import { FormField } from '../components/UI/FormField'
import { ValidationService } from '../services/validation'

const Register: React.FC = () => {
  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Form data
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')

  // Biometric data
  const [age, setAge] = useState('')
  const [gender, setGender] = useState<'male' | 'female' | ''>('')
  const [weight, setWeight] = useState('')
  const [height, setHeight] = useState('')
  const [activityLevel, setActivityLevel] = useState('')

  const { register, updateBiometrics } = useAuth()

  const validateStep1 = () => {
    // Use ValidationService for consistent validation
    const emailResult = ValidationService.validateEmail(email)
    if (!emailResult.isValid) {
      setError(emailResult.error!)
      return false
    }
    
    const passwordResult = ValidationService.validatePassword(password)
    if (!passwordResult.isValid) {
      setError(passwordResult.error!)
      return false
    }
    
    if (!confirmPassword) {
      setError('Please confirm your password')
      return false
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return false
    }
    
    const firstNameResult = ValidationService.validateName(firstName)
    if (!firstNameResult.isValid) {
      setError(`First name: ${firstNameResult.error}`)
      return false
    }
    
    const lastNameResult = ValidationService.validateName(lastName)
    if (!lastNameResult.isValid) {
      setError(`Last name: ${lastNameResult.error}`)
      return false
    }
    
    return true
  }

  const validateStep2 = () => {
    // Use ValidationService for biometric data validation  
    const ageResult = ValidationService.validateAge(age)
    if (!ageResult.isValid) {
      setError(ageResult.error!)
      return false
    }
    
    const genderResult = ValidationService.validateGender(gender)
    if (!genderResult.isValid) {
      setError(genderResult.error!)
      return false
    }
    
    const weightResult = ValidationService.validateWeight(weight)
    if (!weightResult.isValid) {
      setError(weightResult.error!)
      return false
    }
    
    const heightResult = ValidationService.validateHeight(height)
    if (!heightResult.isValid) {
      setError(heightResult.error!)
      return false
    }
    
    const activityResult = ValidationService.validateActivityLevel(activityLevel)
    if (!activityResult.isValid) {
      setError(activityResult.error!)
      return false
    }
    
    return true
  }

  const handleStep1Submit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (validateStep1()) {
      setStep(2)
    }
  }

  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!validateStep2()) return

    setIsLoading(true)

    try {
      // Truncate password if needed for bcrypt compatibility (matches backend)
      const safePassword = ValidationService.truncatePasswordIfNeeded(password)
      
      // Register user with all data including biometrics (atomic operation)
      await register({
        email,
        password: safePassword,
        first_name: firstName,
        last_name: lastName,
        age: parseInt(age),
        gender: gender as 'male' | 'female',
        weight: parseFloat(weight),
        height: parseFloat(height),
        activity_level: parseFloat(activityLevel)
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const activityLevels = [
    { value: '1.20', label: 'Sedentary', desc: 'Little to no exercise' },
    { value: '1.35', label: 'Lightly Active', desc: 'Light exercise 1-3 days/week' },
    { value: '1.50', label: 'Moderately Active', desc: 'Moderate exercise 3-5 days/week' },
    { value: '1.65', label: 'Active', desc: 'Heavy exercise 6-7 days/week' },
    { value: '1.80', label: 'Very Active', desc: 'Very heavy exercise, physical job' }
  ]

  return (
    <div className="login-container">
      {/* Logo */}
      <div className="login-logo">
        <Zap className="w-8 h-8 text-white" />
      </div>

      {/* Main Content */}
      <div className="login-content">
        {/* Header */}
        <div className="login-header">
          <h1 className="login-title">
            <span className="login-title-brand">NovaFitness</span>
          </h1>
          <p className="login-subtitle">
            {step === 1 
              ? 'Crea tu cuenta para comenzar' 
              : 'Completa tu perfil para obtener información personalizada'
            }
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-white">
              Paso {step} de 2
            </span>
            <span className="text-sm text-gray-300">
              {step === 1 ? '- Detalles de la cuenta' : '- Perfil biométrico'}
            </span>
          </div>
          <div className="w-full bg-gray-700 bg-opacity-30 rounded-full h-2">
            <div 
              className="bg-white bg-opacity-40 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 2) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Registration Form */}
        <form onSubmit={step === 1 ? handleStep1Submit : handleStep2Submit} className="login-form">
          {error && (
            <div className="login-error">
              <p className="text-red-300 text-sm text-center">{error}</p>
            </div>
          )}

          {step === 1 ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  id="firstName"
                  label="Nombre"
                  type="text"
                  value={firstName}
                  onChange={(value) => setFirstName(value)}
                  icon={<User className="w-5 h-5" />}
                />
                <FormField
                  id="lastName"
                  label="Apellido"
                  type="text"
                  value={lastName}
                  onChange={(value) => setLastName(value)}
                  icon={<User className="w-5 h-5" />}
                />
              </div>

              <FormField
                id="email"
                label="Correo Electrónico"
                type="email"
                value={email}
                onChange={(value) => setEmail(value)}
                icon={<Mail className="w-5 h-5" />}
                placeholder="Introduce tu correo electrónico"
                required
              />

              <FormField
                id="password"
                label="Contraseña"
                type="password"
                value={password}
                onChange={(value) => setPassword(value)}
                icon={<Lock className="w-5 h-5" />}
                placeholder="Crea una contraseña"
                showPasswordToggle
                required
              />

              <FormField
                id="confirmPassword"
                label="Confirmar Contraseña"
                type="password"
                value={confirmPassword}
                onChange={(value) => setConfirmPassword(value)}
                icon={<Lock className="w-5 h-5" />}
                placeholder="Confirma tu contraseña"
                required
              />

              <Button type="submit" className="w-full">
                Continuar a Configuración de Perfil
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  id="age"
                  label="Age"
                  type="number"
                  value={age}
                  onChange={(value) => setAge(value)}
                  icon={<Calendar className="w-5 h-5" />}
                  placeholder="25"
                  min={13}
                  max={120}
                  required
                />

                <div className="login-field">
                  <label htmlFor="gender" className="login-label">
                    Género *
                  </label>
                  <div className="login-input-container">
                    <div className="login-input-icon">
                      <User className="w-5 h-5" />
                    </div>
                    <select
                      id="gender"
                      value={gender}
                      onChange={(e) => setGender(e.target.value as 'male' | 'female')}
                      className="login-input"
                      required
                    >
                      <option value="">Selecciona</option>
                      <option value="male">Masculino</option>
                      <option value="female">Femenino</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  id="weight"
                  label="Peso (kg)"
                  type="number"
                  value={weight}
                  onChange={(value) => setWeight(value)}
                  icon={<Scale className="w-5 h-5" />}
                  placeholder="70"
                  min={30}
                  max={300}
                  step={0.1}
                  required
                />

                <FormField
                  id="height"
                  label="Altura (cm)"
                  type="number"
                  value={height}
                  onChange={(value) => setHeight(value)}
                  icon={<Ruler className="w-5 h-5" />}
                  placeholder="175"
                  min={100}
                  max={250}
                  step={0.1}
                  required
                />
              </div>

              <div className="login-field">
                <label htmlFor="activityLevel" className="login-label">
                  Nivel de Actividad *
                </label>
                <div className="login-input-container">
                  <div className="login-input-icon">
                    <Activity className="w-5 h-5" />
                  </div>
                  <select
                    id="activityLevel"
                    value={activityLevel}
                    onChange={(e) => setActivityLevel(e.target.value)}
                    className="login-input"
                    required
                  >
                    <option value="">Selecciona tu nivel de actividad</option>
                    {activityLevels.map((level) => (
                      <option key={level.value} value={level.value}>
                        {level.label} - {level.desc}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setStep(1)}
                  disabled={isLoading}
                  className="flex-1"
                >
                  Atrás
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  isLoading={isLoading}
                  icon={!isLoading ? <Zap className="w-4 h-4" /> : undefined}
                  className="flex-1"
                >
                  {isLoading ? 'Creando...' : 'Completar Configuración'}
                </Button>
              </div>
            </div>
          )}

          <div className="login-register">
            <p className="login-register-text">
              ¿Ya tienes una cuenta?{' '}
              <Link
                to="/login"
                className="login-register-link"
              >
                Inicia sesión aquí
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Register