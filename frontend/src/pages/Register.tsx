import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, User, Zap, Scale, Activity, Calendar, Ruler, ArrowLeft } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/UI/Button'
import { FormField } from '../components/UI/FormField'
import CustomSelect from '../components/UI/CustomSelect'
import { ValidationService } from '../services/validation'
import { useToast } from '../contexts/ToastContext'
import { requiredFieldMessage, translateValidationMessage } from '../services/validationMessages'
import ObjectiveForm from '../components/ObjectiveForm'
import { FitnessObjective } from '../services/api'

const Register: React.FC = () => {
  const [step, setStep] = useState(1)
  const [stepDirection, setStepDirection] = useState<'forward' | 'backward'>('forward')
  const [isLoading, setIsLoading] = useState(false)
  const [step1Errors, setStep1Errors] = useState<Record<string, string>>({})
  const [step2Errors, setStep2Errors] = useState<Record<string, string>>({})

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

  // Objective data (optional)
  const [objective, setObjective] = useState<FitnessObjective | undefined>(undefined)
  const [aggressiveness, setAggressiveness] = useState(2)

  const { register } = useAuth()
  const { showError, showSuccess } = useToast()

  const goToStep = (nextStep: number) => {
    setStepDirection(nextStep > step ? 'forward' : 'backward')
    setStep(nextStep)
  }

  const validateStep1 = () => {
    const errors: Record<string, string> = {}

    if (!firstName.trim()) {
      errors.firstName = requiredFieldMessage('El nombre')
    }

    if (!lastName.trim()) {
      errors.lastName = requiredFieldMessage('El apellido')
    }

    if (!email.trim()) {
      errors.email = requiredFieldMessage('El correo electrónico')
    }

    if (!password.trim()) {
      errors.password = requiredFieldMessage('La contraseña')
    }

    if (!confirmPassword.trim()) {
      errors.confirmPassword = requiredFieldMessage('La confirmación de contraseña')
    }

    if (Object.keys(errors).length > 0) {
      setStep1Errors(errors)
      showError(Object.values(errors)[0], 'Completa los campos requeridos')
      return false
    }

    const emailResult = ValidationService.validateEmail(email)
    if (!emailResult.isValid) {
      const message = translateValidationMessage(emailResult.error)
      setStep1Errors({ email: message })
      showError(message, 'Correo electrónico inválido')
      return false
    }
    
    const passwordResult = ValidationService.validatePassword(password)
    if (!passwordResult.isValid) {
      const message = translateValidationMessage(passwordResult.error)
      setStep1Errors({ password: message })
      showError(message, 'Contraseña inválida')
      return false
    }
    
    if (password !== confirmPassword) {
      const message = translateValidationMessage('Passwords do not match')
      setStep1Errors({ confirmPassword: message })
      showError(message, 'Contraseñas no coinciden')
      return false
    }
    
    const firstNameResult = ValidationService.validateName(firstName)
    if (!firstNameResult.isValid) {
      const message = translateValidationMessage(firstNameResult.error)
      setStep1Errors({ firstName: message })
      showError(message, 'Nombre inválido')
      return false
    }
    
    const lastNameResult = ValidationService.validateName(lastName)
    if (!lastNameResult.isValid) {
      const message = translateValidationMessage(lastNameResult.error)
      setStep1Errors({ lastName: message })
      showError(message, 'Apellido inválido')
      return false
    }

    setStep1Errors({})
    
    return true
  }

  const validateStep2 = () => {
    const errors: Record<string, string> = {}

    if (!age.trim()) {
      errors.age = requiredFieldMessage('La edad')
    }

    if (!gender.trim()) {
      errors.gender = requiredFieldMessage('El género')
    }

    if (!weight.trim()) {
      errors.weight = requiredFieldMessage('El peso')
    }

    if (!height.trim()) {
      errors.height = requiredFieldMessage('La altura')
    }

    if (!activityLevel.trim()) {
      errors.activityLevel = requiredFieldMessage('El nivel de actividad')
    }

    if (Object.keys(errors).length > 0) {
      setStep2Errors(errors)
      showError(Object.values(errors)[0], 'Completa tu perfil biométrico')
      return false
    }

    const ageResult = ValidationService.validateAge(age)
    if (!ageResult.isValid) {
      const message = translateValidationMessage(ageResult.error)
      setStep2Errors({ age: message })
      showError(message, 'Edad inválida')
      return false
    }
    
    const genderResult = ValidationService.validateGender(gender)
    if (!genderResult.isValid) {
      const message = translateValidationMessage(genderResult.error)
      setStep2Errors({ gender: message })
      showError(message, 'Género inválido')
      return false
    }
    
    const weightResult = ValidationService.validateWeight(weight)
    if (!weightResult.isValid) {
      const message = translateValidationMessage(weightResult.error)
      setStep2Errors({ weight: message })
      showError(message, 'Peso inválido')
      return false
    }
    
    const heightResult = ValidationService.validateHeight(height)
    if (!heightResult.isValid) {
      const message = translateValidationMessage(heightResult.error)
      setStep2Errors({ height: message })
      showError(message, 'Altura inválida')
      return false
    }
    
    const activityResult = ValidationService.validateActivityLevel(activityLevel)
    if (!activityResult.isValid) {
      const message = translateValidationMessage(activityResult.error)
      setStep2Errors({ activityLevel: message })
      showError(message, 'Actividad inválida')
      return false
    }

    setStep2Errors({})
    
    return true
  }

  const handleStep1Submit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (validateStep1()) {
      goToStep(2)
    }
  }

  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateStep2()) return

    // Move to step 3 (objective) instead of registering immediately
    goToStep(3)
  }

  const handleStep3Submit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!objective) {
      showError('Selecciona un objetivo para continuar', 'Falta completar el objetivo')
      return
    }

    setIsLoading(true)

    try {
      // Truncate password if needed for bcrypt compatibility (matches backend)
      const safePassword = ValidationService.truncatePasswordIfNeeded(password)
      
      // Register user with all data including biometrics and objective
      await register({
        email,
        password: safePassword,
        first_name: firstName,
        last_name: lastName,
        age: parseInt(age),
        gender: gender as 'male' | 'female',
        weight: parseFloat(weight),
        height: parseFloat(height),
        activity_level: parseFloat(activityLevel),
        objective: objective,
        aggressiveness_level: objective ? aggressiveness : undefined
      })
      showSuccess('Tu cuenta se creó correctamente', '¡Registro completado!')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      const message = typeof detail === 'string'
        ? translateValidationMessage(detail)
        : 'No pudimos completar tu registro. Inténtalo nuevamente.'

      showError(message, 'Error al registrar')
    } finally {
      setIsLoading(false)
    }
  }

  const activityLevels = [
    { value: '1.20', label: 'Sedentario', desc: 'Poco o nada de ejercicio' },
    { value: '1.35', label: 'Ligeramente activo', desc: 'Ejercicio ligero 1-3 días/semana' },
    { value: '1.50', label: 'Moderadamente activo', desc: 'Ejercicio moderado 3-5 días/semana' },
    { value: '1.65', label: 'Activo', desc: 'Ejercicio intenso 6-7 días/semana' },
    { value: '1.80', label: 'Muy activo', desc: 'Ejercicio muy intenso o trabajo físico' }
  ]

  const stepBadges = [
    'Detalles de la cuenta',
    'Perfil biométrico',
    'Objetivo fitness'
  ]

  return (
    <div className="login-container">
      {/* Logo */}
      <div className="login-logo">
        <Zap className="w-8 h-8 text-white" />
      </div>

      {/* Main Content */}
      <div className="login-content register-content">
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
        <div className="register-progress" aria-label="Progreso del registro">
          <div className="register-progress-steps" aria-label="Etapa actual del registro">
            <div
              className="register-progress-step register-progress-step-single is-active"
              aria-current="step"
            >
              <span className="register-progress-step-number">{step}</span>
              <span className="register-progress-step-label">{stepBadges[step - 1]}</span>
            </div>
          </div>

          <div className="register-progress-bar bg-gray-700 bg-opacity-30" aria-hidden="true">
            <div
              className="register-progress-bar-fill bg-white bg-opacity-40"
              style={{ width: `${(step / 3) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Registration Form */}
        <form onSubmit={step === 1 ? handleStep1Submit : step === 2 ? handleStep2Submit : handleStep3Submit} className="login-form">
          <div key={step} className={`register-step-panel ${stepDirection === 'backward' ? 'register-step-backward' : 'register-step-forward'}`}>
          {step === 1 ? (
            <div className="register-step-content">
              <div className="register-step-grid">
                <FormField
                  id="firstName"
                  label="Nombre"
                  type="text"
                  value={firstName}
                  onChange={(value) => {
                    setFirstName(value)
                    if (step1Errors.firstName) {
                      setStep1Errors((prev) => ({ ...prev, firstName: '' }))
                    }
                  }}
                  icon={<User className="w-5 h-5" />}
                  placeholder="Ingresa tu nombre"
                  error={step1Errors.firstName}
                  required
                />
                <FormField
                  id="lastName"
                  label="Apellido"
                  type="text"
                  value={lastName}
                  onChange={(value) => {
                    setLastName(value)
                    if (step1Errors.lastName) {
                      setStep1Errors((prev) => ({ ...prev, lastName: '' }))
                    }
                  }}
                  icon={<User className="w-5 h-5" />}
                  placeholder="Ingresa tu apellido"
                  error={step1Errors.lastName}
                  required
                />
              </div>

              <FormField
                id="email"
                label="Correo Electrónico"
                type="email"
                value={email}
                onChange={(value) => {
                  setEmail(value)
                  if (step1Errors.email) {
                    setStep1Errors((prev) => ({ ...prev, email: '' }))
                  }
                }}
                icon={<Mail className="w-5 h-5" />}
                placeholder="Introduce tu correo electrónico"
                error={step1Errors.email}
                required
              />

              <FormField
                id="password"
                label="Contraseña"
                type="password"
                value={password}
                onChange={(value) => {
                  setPassword(value)
                  if (step1Errors.password) {
                    setStep1Errors((prev) => ({ ...prev, password: '' }))
                  }
                }}
                icon={<Lock className="w-5 h-5" />}
                placeholder="Crea una contraseña"
                showPasswordToggle
                error={step1Errors.password}
                required
              />

              <FormField
                id="confirmPassword"
                label="Confirmar Contraseña"
                type="password"
                value={confirmPassword}
                onChange={(value) => {
                  setConfirmPassword(value)
                  if (step1Errors.confirmPassword) {
                    setStep1Errors((prev) => ({ ...prev, confirmPassword: '' }))
                  }
                }}
                icon={<Lock className="w-5 h-5" />}
                placeholder="Confirma tu contraseña"
                error={step1Errors.confirmPassword}
                required
              />

              <Button type="submit" className="w-full register-step-primary-action">
                Continuar a Configuración de Perfil
              </Button>
            </div>
          ) : step === 2 ? (
            <div className="register-step-content">
              <div className="register-step-grid">
                <FormField
                  id="age"
                  label="Edad"
                  type="number"
                  value={age}
                  onChange={(value) => {
                    setAge(value)
                    if (step2Errors.age) {
                      setStep2Errors((prev) => ({ ...prev, age: '' }))
                    }
                  }}
                  icon={<Calendar className="w-5 h-5" />}
                  placeholder="25"
                  error={step2Errors.age}
                  min={13}
                  max={120}
                  required
                />
                <CustomSelect
                  id="gender"
                  label="Género"
                  value={gender}
                  onChange={(selectedValue) => {
                    setGender(selectedValue as 'male' | 'female')
                    if (step2Errors.gender) {
                      setStep2Errors((prev) => ({ ...prev, gender: '' }))
                    }
                  }}
                  icon={<User className="w-5 h-5" />}
                  placeholder="Selecciona"
                  required
                  error={step2Errors.gender}
                  options={[
                    { value: 'male', label: 'Masculino' },
                    { value: 'female', label: 'Femenino' }
                  ]}
                />
              </div>

              <div className="register-step-grid">
                <FormField
                  id="weight"
                  label="Peso (kg)"
                  type="number"
                  value={weight}
                  onChange={(value) => {
                    setWeight(value)
                    if (step2Errors.weight) {
                      setStep2Errors((prev) => ({ ...prev, weight: '' }))
                    }
                  }}
                  icon={<Scale className="w-5 h-5" />}
                  placeholder="70"
                  error={step2Errors.weight}
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
                  onChange={(value) => {
                    setHeight(value)
                    if (step2Errors.height) {
                      setStep2Errors((prev) => ({ ...prev, height: '' }))
                    }
                  }}
                  icon={<Ruler className="w-5 h-5" />}
                  placeholder="175"
                  error={step2Errors.height}
                  min={100}
                  max={250}
                  step={0.1}
                  required
                />
              </div>

              <CustomSelect
                id="activityLevel"
                label="Nivel de Actividad"
                value={activityLevel}
                onChange={(selectedValue) => {
                  setActivityLevel(selectedValue)
                  if (step2Errors.activityLevel) {
                    setStep2Errors((prev) => ({ ...prev, activityLevel: '' }))
                  }
                }}
                icon={<Activity className="w-5 h-5" />}
                placeholder="Selecciona tu nivel de actividad"
                required
                error={step2Errors.activityLevel}
                options={activityLevels.map((level) => ({
                  value: level.value,
                  label: level.label,
                  description: level.desc
                }))}
              />

              <div className="register-step-actions-vertical">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => goToStep(1)}
                  disabled={isLoading}
                  icon={<ArrowLeft className="w-4 h-4" />}
                  className="register-back-ghost"
                >
                  Atrás
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  isLoading={isLoading}
                  icon={!isLoading ? <Zap className="w-4 h-4" /> : undefined}
                  className="w-full register-step-primary-action"
                >
                  {isLoading ? 'Creando...' : 'Configurar Objetivo'}
                </Button>
              </div>
            </div>
          ) : step === 3 ? (
            <div className="register-step-content">
              <ObjectiveForm
                selectedObjective={objective}
                selectedAggressiveness={aggressiveness}
                onObjectiveChange={(obj, agg) => {
                  setObjective(obj)
                  setAggressiveness(agg)
                }}
              />

              <div className="register-step-actions-vertical">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => goToStep(2)}
                  disabled={isLoading}
                  icon={<ArrowLeft className="w-4 h-4" />}
                  className="register-back-ghost"
                >
                  Atrás
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  isLoading={isLoading}
                  icon={!isLoading ? <Zap className="w-4 h-4" /> : undefined}
                  className="w-full register-step-primary-action"
                >
                  {isLoading ? 'Creando Cuenta...' : 'Completar Registro'}
                </Button>
              </div>

              <p className="register-objective-note">
                Puedes cambiar tu objetivo después en tu perfil
              </p>
            </div>
          ) : null}
          </div>

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