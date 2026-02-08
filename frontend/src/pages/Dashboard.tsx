import React, { useState } from 'react'
import { 
  User, 
  Settings, 
  LogOut, 
  Activity, 
  Scale, 
  Target, 
  TrendingUp,
  Calendar,
  Ruler,
  Zap,
  Edit3,
  Save,
  X
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { BiometricData } from '../services/api'

const Dashboard: React.FC = () => {
  const { user, logout, updateBiometrics } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Edit form state
  const [editData, setEditData] = useState({
    age: user?.age?.toString() || '',
    gender: user?.gender || '',
    weight: user?.weight?.toString() || '',
    height: user?.height?.toString() || '',
    activity_level: user?.activity_level?.toString() || ''
  })

  const activityLevels = [
    { value: '1.20', label: 'Sedentary', desc: 'Little to no exercise' },
    { value: '1.35', label: 'Lightly Active', desc: 'Light exercise 1-3 days/week' },
    { value: '1.50', label: 'Moderately Active', desc: 'Moderate exercise 3-5 days/week' },
    { value: '1.65', label: 'Active', desc: 'Heavy exercise 6-7 days/week' },
    { value: '1.80', label: 'Very Active', desc: 'Very heavy exercise, physical job' }
  ]

  const getActivityLevelLabel = (level: number) => {
    const found = activityLevels.find(al => parseFloat(al.value) === level)
    return found ? found.label : 'Unknown'
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccess('')

    try {
      await updateBiometrics({
        age: parseInt(editData.age),
        gender: editData.gender as 'male' | 'female',
        weight: parseFloat(editData.weight),
        height: parseFloat(editData.height),
        activity_level: parseFloat(editData.activity_level)
      })
      setSuccess('Profile updated successfully!')
      setIsEditing(false)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update profile')
    } finally {
      setIsLoading(false)
    }
  }

  const startEdit = () => {
    setEditData({
      age: user?.age?.toString() || '',
      gender: user?.gender || '',
      weight: user?.weight?.toString() || '',
      height: user?.height?.toString() || '',
      activity_level: user?.activity_level?.toString() || ''
    })
    setIsEditing(true)
    setError('')
    setSuccess('')
  }

  const cancelEdit = () => {
    setIsEditing(false)
    setError('')
    setSuccess('')
  }

  const needsProfile = !user?.age || !user?.gender || !user?.weight || !user?.height || !user?.activity_level

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-pink-50 to-sky-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-pink-500 rounded-xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  <span className="gradient-text">NovaFitness</span>
                </h1>
                <p className="text-sm text-gray-500">
                  Welcome back, {user?.first_name || user?.email}!
                </p>
              </div>
            </div>
            <button
              onClick={logout}
              className="btn btn-ghost"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Alerts */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="error-message">{error}</p>
          </div>
        )}
        
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="success-message">{success}</p>
          </div>
        )}

        {/* Profile Setup Notice */}
        {needsProfile && !isEditing && (
          <div className="mb-6 card-gradient rounded-xl p-6 text-white">
            <div className="flex items-start space-x-4">
              <Target className="w-6 h-6 mt-1 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">Complete Your Profile</h3>
                <p className="text-white/90 mb-4">
                  Add your biometric information to get personalized BMR and TDEE calculations for better fitness insights.
                </p>
                <button
                  onClick={startEdit}
                  className="bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/20 
                           text-white px-4 py-2 rounded-lg font-medium transition-all duration-200"
                >
                  <Edit3 className="w-4 h-4 inline mr-2" />
                  Complete Profile
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Card */}
          <div className="lg:col-span-1">
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <User className="w-5 h-5 mr-2 text-violet-600" />
                  Profile
                </h2>
                {!needsProfile && !isEditing && (
                  <button
                    onClick={startEdit}
                    className="btn btn-ghost text-sm"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                )}
              </div>

              {isEditing ? (
                <form onSubmit={handleEditSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="form-label">Age</label>
                      <input
                        type="number"
                        min="13"
                        max="120"
                        value={editData.age}
                        onChange={(e) => setEditData(prev => ({...prev, age: e.target.value}))}
                        className="input"
                        required
                      />
                    </div>
                    <div>
                      <label className="form-label">Gender</label>
                      <select
                        value={editData.gender}
                        onChange={(e) => setEditData(prev => ({...prev, gender: e.target.value}))}
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
                    <div>
                      <label className="form-label">Weight (kg)</label>
                      <input
                        type="number"
                        min="30"
                        max="300"
                        step="0.1"
                        value={editData.weight}
                        onChange={(e) => setEditData(prev => ({...prev, weight: e.target.value}))}
                        className="input"
                        required
                      />
                    </div>
                    <div>
                      <label className="form-label">Height (cm)</label>
                      <input
                        type="number"
                        min="100"
                        max="250"
                        step="0.1"
                        value={editData.height}
                        onChange={(e) => setEditData(prev => ({...prev, height: e.target.value}))}
                        className="input"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="form-label">Activity Level</label>
                    <select
                      value={editData.activity_level}
                      onChange={(e) => setEditData(prev => ({...prev, activity_level: e.target.value}))}
                      className="select"
                      required
                    >
                      <option value="">Select activity level</option>
                      {activityLevels.map((level) => (
                        <option key={level.value} value={level.value}>
                          {level.label} - {level.desc}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex gap-2 pt-4">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="btn btn-primary flex-1 text-sm"
                    >
                      {isLoading ? (
                        <>
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="w-3 h-3" />
                          Save
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={cancelEdit}
                      disabled={isLoading}
                      className="btn btn-secondary text-sm"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-600">Email</span>
                    <span className="font-medium">{user?.email}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-600">Name</span>
                    <span className="font-medium">
                      {user?.first_name || user?.last_name 
                        ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                        : 'Not set'
                      }
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-600 flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      Age
                    </span>
                    <span className="font-medium">{user?.age || 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-600">Gender</span>
                    <span className="font-medium capitalize">{user?.gender || 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-600 flex items-center">
                      <Scale className="w-4 h-4 mr-1" />
                      Weight
                    </span>
                    <span className="font-medium">{user?.weight ? `${user.weight} kg` : 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-600 flex items-center">
                      <Ruler className="w-4 h-4 mr-1" />
                      Height
                    </span>
                    <span className="font-medium">{user?.height ? `${user.height} cm` : 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-600 flex items-center">
                      <Activity className="w-4 h-4 mr-1" />
                      Activity
                    </span>
                    <span className="font-medium">
                      {user?.activity_level ? getActivityLevelLabel(user.activity_level) : 'Not set'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Metrics Cards */}
          <div className="lg:col-span-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* BMR Card */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                    <Target className="w-5 h-5 mr-2 text-pink-500" />
                    BMR
                  </h3>
                  <div className="w-8 h-8 bg-pink-100 rounded-lg flex items-center justify-center">
                    <Target className="w-4 h-4 text-pink-500" />
                  </div>
                </div>
                {user?.bmr ? (
                  <>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                      {Math.round(user.bmr)}
                      <span className="text-lg text-gray-500 font-normal ml-1">cal/day</span>
                    </div>
                    <p className="text-gray-600 text-sm">
                      Basal Metabolic Rate - Calories your body burns at rest
                    </p>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm">
                      Complete your profile to see your BMR calculation
                    </p>
                  </div>
                )}
              </div>

              {/* TDEE Card */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-sky-500" />
                    TDEE
                  </h3>
                  <div className="w-8 h-8 bg-sky-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-4 h-4 text-sky-500" />
                  </div>
                </div>
                {user?.tdee ? (
                  <>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                      {Math.round(user.tdee)}
                      <span className="text-lg text-gray-500 font-normal ml-1">cal/day</span>
                    </div>
                    <p className="text-gray-600 text-sm">
                      Total Daily Energy Expenditure - Including your activity level
                    </p>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm">
                      Complete your profile to see your TDEE calculation
                    </p>
                  </div>
                )}
              </div>

              {/* Calorie Zones Card */}
              {user?.tdee && (
                <div className="card md:col-span-2">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <Activity className="w-5 h-5 mr-2 text-violet-500" />
                    Daily Calorie Zones
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-red-50 rounded-lg p-4 border border-red-100">
                      <div className="text-sm font-medium text-red-700 mb-1">Weight Loss</div>
                      <div className="text-xl font-bold text-red-600">
                        {Math.round(user.tdee - 500)}
                      </div>
                      <div className="text-xs text-red-600">-500 cal/day</div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4 border border-green-100">
                      <div className="text-sm font-medium text-green-700 mb-1">Maintenance</div>
                      <div className="text-xl font-bold text-green-600">
                        {Math.round(user.tdee)}
                      </div>
                      <div className="text-xs text-green-600">Your TDEE</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                      <div className="text-sm font-medium text-blue-700 mb-1">Weight Gain</div>
                      <div className="text-xl font-bold text-blue-600">
                        {Math.round(user.tdee + 500)}
                      </div>
                      <div className="text-xs text-blue-600">+500 cal/day</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard