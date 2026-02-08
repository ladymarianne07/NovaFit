import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, User, Zap, Scale, Activity, Calendar, Ruler } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { BiometricData } from '../services/api'

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
    if (!email || !password || !confirmPassword) {
      setError('All fields are required')
      return false
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return false
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return false
    }
    return true
  }

  const validateStep2 = () => {
    if (!age || !gender || !weight || !height || !activityLevel) {
      setError('All biometric fields are required for accurate calculations')
      return false
    }
    const ageNum = parseInt(age)
    if (ageNum < 13 || ageNum > 120) {
      setError('Age must be between 13 and 120')
      return false
    }
    const weightNum = parseFloat(weight)
    if (weightNum < 30 || weightNum > 300) {
      setError('Weight must be between 30kg and 300kg')
      return false
    }
    const heightNum = parseFloat(height)
    if (heightNum < 100 || heightNum > 250) {
      setError('Height must be between 100cm and 250cm')
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
      // Register user
      await register({
        email,
        password,
        first_name: firstName,
        last_name: lastName
      })

      // Update biometrics
      await updateBiometrics({
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
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-pink-50 to-sky-50 flex items-center justify-center px-4 py-12">"
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-pink-500 rounded-xl flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-pink-500 to-sky-400 rounded-full"></div>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Join{' '}
            <span className="gradient-text animate-gradient">NovaFitness</span>
          </h1>
          <p className="text-gray-600">
            {step === 1 
              ? 'Create your account to get started' 
              : 'Complete your profile for personalized insights'
            }
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-violet-600">
              Step {step} of 2
            </span>
            <span className="text-sm text-gray-500">
              {step === 1 ? 'Account Details' : 'Biometric Profile'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-violet-500 to-pink-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 2) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Registration Form */}
        <div className="card fade-in">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="error-message">{error}</p>
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleStep1Submit} className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="form-group">
                  <label htmlFor="firstName" className="form-label">
                    First Name
                  </label>
                  <input
                    id="firstName"
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="input"
                    placeholder="John"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="lastName" className="form-label">
                    Last Name
                  </label>
                  <input
                    id="lastName"
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="input"
                    placeholder="Doe"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address <span className="required">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input pl-10"
                    placeholder="Enter your email"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">
                  Password <span className="required">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input pl-10 pr-10"
                    placeholder="Create a password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm Password <span className="required">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input pl-10"
                    placeholder="Confirm your password"
                    required
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary w-full">
                Continue to Profile Setup
              </button>
            </form>
          ) : (
            <form onSubmit={handleStep2Submit} className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="form-group">
                  <label htmlFor="age" className="form-label">
                    Age <span className="required">*</span>
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      id="age"
                      type="number"
                      min="13"
                      max="120"
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                      className="input pl-10"
                      placeholder="25"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="gender" className="form-label">
                    Gender <span className="required">*</span>
                  </label>
                  <select
                    id="gender"
                    value={gender}
                    onChange={(e) => setGender(e.target.value as 'male' | 'female')}
                    className="select"
                    required
                  >
                    <option value="">Select</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="form-group">
                  <label htmlFor="weight" className="form-label">
                    Weight (kg) <span className="required">*</span>
                  </label>
                  <div className="relative">
                    <Scale className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      id="weight"
                      type="number"
                      min="30"
                      max="300"
                      step="0.1"
                      value={weight}
                      onChange={(e) => setWeight(e.target.value)}
                      className="input pl-10"
                      placeholder="70"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="height" className="form-label">
                    Height (cm) <span className="required">*</span>
                  </label>
                  <div className="relative">
                    <Ruler className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      id="height"
                      type="number"
                      min="100"
                      max="250"
                      step="0.1"
                      value={height}
                      onChange={(e) => setHeight(e.target.value)}
                      className="input pl-10"
                      placeholder="175"
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="activityLevel" className="form-label">
                  Activity Level <span className="required">*</span>
                </label>
                <select
                  id="activityLevel"
                  value={activityLevel}
                  onChange={(e) => setActivityLevel(e.target.value)}
                  className="select"
                  required
                >
                  <option value="">Select your activity level</option>
                  {activityLevels.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label} - {level.desc}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="btn btn-secondary flex-1"
                  disabled={isLoading}
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn btn-primary flex-1"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Creating...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      Complete Setup
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-center text-gray-600">
              Already have an account?{' '}
              <Link
                to="/login"
                className="text-violet-600 hover:text-violet-700 font-medium"
              >
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Register