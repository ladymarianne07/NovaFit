import React, { useState } from 'react'
import { 
  User, 
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
import { Button } from '../components/UI/Button'
import { FormField } from '../components/UI/FormField'

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
    <div className="login-container">
      {/* Header */}
      <div className="login-logo">
        <Zap className="w-8 h-8 text-white" />
      </div>

      <div className="login-content">
        {/* Header */}
        <div className="login-header mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="login-title">
                <span className="login-title-brand">NovaFitness</span>
              </h1>
              <p className="login-subtitle">
                Welcome back, {user?.first_name || user?.email}!
              </p>
            </div>
            <Button
              onClick={logout}
              variant="ghost"
              icon={<LogOut className="w-4 h-4" />}
            >
              Logout
            </Button>
          </div>
        </div>
        {/* Alerts */}
        {error && (
          <div className="login-error mb-6">
            <p className="text-red-300 text-sm text-center">{error}</p>
          </div>
        )}
        
        {success && (
          <div className="mb-6 bg-green-500 bg-opacity-20 backdrop-blur-sm border border-green-400 border-opacity-30 rounded-lg p-4">
            <p className="text-green-300 text-sm text-center">{success}</p>
          </div>
        )}

        {/* Profile Setup Notice */}
        {needsProfile && !isEditing && (
          <div className="mb-6 bg-white bg-opacity-10 backdrop-blur-sm border border-white border-opacity-20 rounded-lg p-6">
            <div className="flex items-start space-x-4">
              <Target className="w-6 h-6 mt-1 flex-shrink-0 text-white" />
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2 text-white">Complete Your Profile</h3>
                <p className="text-gray-300 mb-4">
                  Add your biometric information to get personalized BMR and TDEE calculations for better fitness insights.
                </p>
                <Button
                  onClick={startEdit}
                  variant="ghost"
                  icon={<Edit3 className="w-4 h-4" />}
                >
                  Complete Profile
                </Button>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Card */}
          <div className="lg:col-span-1">
            <div className="bg-white bg-opacity-10 backdrop-blur-sm border border-white border-opacity-20 rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Profile
                </h2>
                {!needsProfile && !isEditing && (
                  <Button
                    onClick={startEdit}
                    variant="ghost"
                    icon={<Edit3 className="w-4 h-4" />}
                  />
                )}
              </div>

              {isEditing ? (
                <form onSubmit={handleEditSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      id="age"
                      label="Age"
                      type="number"
                      value={editData.age}
                      onChange={(value) => setEditData(prev => ({...prev, age: value}))}
                      icon={<Calendar className="w-4 h-4" />}
                      min={13}
                      max={120}
                      required
                    />
                    <div className="login-field">
                      <label className="login-label">Gender</label>
                      <div className="login-input-container">
                        <div className="login-input-icon">
                          <User className="w-4 h-4" />
                        </div>
                        <select
                          value={editData.gender}
                          onChange={(e) => setEditData(prev => ({...prev, gender: e.target.value}))}
                          className="login-input"
                          required
                        >
                          <option value="">Select</option>
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      id="weight"
                      label="Weight (kg)"
                      type="number"
                      value={editData.weight}
                      onChange={(value) => setEditData(prev => ({...prev, weight: value}))}
                      icon={<Scale className="w-4 h-4" />}
                      min={30}
                      max={300}
                      step={0.1}
                      required
                    />
                    <FormField
                      id="height"
                      label="Height (cm)"
                      type="number"
                      value={editData.height}
                      onChange={(value) => setEditData(prev => ({...prev, height: value}))}
                      icon={<Ruler className="w-4 h-4" />}
                      min={100}
                      max={250}
                      step={0.1}
                      required
                    />
                  </div>

                  <div className="login-field">
                    <label className="login-label">Activity Level</label>
                    <div className="login-input-container">
                      <div className="login-input-icon">
                        <Activity className="w-4 h-4" />
                      </div>
                      <select
                        value={editData.activity_level}
                        onChange={(e) => setEditData(prev => ({...prev, activity_level: e.target.value}))}
                        className="login-input"
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
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button
                      type="submit"
                      disabled={isLoading}
                      isLoading={isLoading}
                      icon={!isLoading ? <Save className="w-3 h-3" /> : undefined}
                      className="flex-1 text-sm"
                    >
                      {isLoading ? 'Saving...' : 'Save'}
                    </Button>
                    <Button
                      type="button"
                      onClick={cancelEdit}
                      disabled={isLoading}
                      variant="secondary"
                      icon={<X className="w-3 h-3" />}
                      className="text-sm"
                    />
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-white text-opacity-80">Email</span>
                    <span className="text-white font-medium">{user?.email}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-white text-opacity-80">Name</span>
                    <span className="text-white font-medium">
                      {user?.first_name || user?.last_name 
                        ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                        : 'Not set'
                      }
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-white text-opacity-80 flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      Age
                    </span>
                    <span className="text-white font-medium">{user?.age || 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-white text-opacity-80">Gender</span>
                    <span className="text-white font-medium capitalize">{user?.gender || 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-white text-opacity-80 flex items-center">
                      <Scale className="w-4 h-4 mr-1" />
                      Weight
                    </span>
                    <span className="text-white font-medium">{user?.weight ? `${user.weight} kg` : 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-white text-opacity-80 flex items-center">
                      <Ruler className="w-4 h-4 mr-1" />
                      Height
                    </span>
                    <span className="text-white font-medium">{user?.height ? `${user.height} cm` : 'Not set'}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-white text-opacity-80 flex items-center">
                      <Activity className="w-4 h-4 mr-1" />
                      Activity
                    </span>
                    <span className="text-white font-medium">
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
              <div className="bg-white bg-opacity-10 backdrop-blur-sm border border-white border-opacity-20 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    BMR
                  </h3>
                  <div className="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                    <Target className="w-4 h-4 text-white" />
                  </div>
                </div>
                {user?.bmr ? (
                  <>
                    <div className="text-3xl font-bold text-white mb-2">
                      {Math.round(user.bmr)}
                      <span className="text-lg text-white text-opacity-60 font-normal ml-1">cal/day</span>
                    </div>
                    <p className="text-white text-opacity-70 text-sm">
                      Basal Metabolic Rate - Calories your body burns at rest
                    </p>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <Target className="w-12 h-12 text-white text-opacity-40 mx-auto mb-3" />
                    <p className="text-white text-opacity-60 text-sm">
                      Complete your profile to see your BMR calculation
                    </p>
                  </div>
                )}
              </div>

              {/* TDEE Card */}
              <div className="bg-white bg-opacity-10 backdrop-blur-sm border border-white border-opacity-20 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2" />
                    TDEE
                  </h3>
                  <div className="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-4 h-4 text-white" />
                  </div>
                </div>
                {user?.daily_caloric_expenditure ? (
                  <>
                    <div className="text-3xl font-bold text-white mb-2">
                      {Math.round(user.daily_caloric_expenditure)}
                      <span className="text-lg text-white text-opacity-60 font-normal ml-1">cal/day</span>
                    </div>
                    <p className="text-white text-opacity-70 text-sm">
                      Total Daily Energy Expenditure - Including your activity level
                    </p>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <TrendingUp className="w-12 h-12 text-white text-opacity-40 mx-auto mb-3" />
                    <p className="text-white text-opacity-60 text-sm">
                      Complete your profile to see your TDEE calculation
                    </p>
                  </div>
                )}
              </div>

              {/* Calorie Zones Card */}
              {user?.daily_caloric_expenditure && (
                <div className="bg-white bg-opacity-10 backdrop-blur-sm border border-white border-opacity-20 rounded-lg p-6 md:col-span-2">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <Activity className="w-5 h-5 mr-2" />
                    Daily Calorie Zones
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-red-500 bg-opacity-20 backdrop-blur-sm border border-red-300 border-opacity-30 rounded-lg p-4">
                      <div className="text-sm font-medium text-red-200 mb-1">Weight Loss</div>
                      <div className="text-xl font-bold text-white">
                        {Math.round(user.daily_caloric_expenditure - 500)}
                      </div>
                      <div className="text-xs text-red-200">-500 cal/day</div>
                    </div>
                    <div className="bg-green-500 bg-opacity-20 backdrop-blur-sm border border-green-300 border-opacity-30 rounded-lg p-4">
                      <div className="text-sm font-medium text-green-200 mb-1">Maintenance</div>
                      <div className="text-xl font-bold text-white">
                        {Math.round(user.daily_caloric_expenditure)}
                      </div>
                      <div className="text-xs text-green-200">Your TDEE</div>
                    </div>
                    <div className="bg-blue-500 bg-opacity-20 backdrop-blur-sm border border-blue-300 border-opacity-30 rounded-lg p-4">
                      <div className="text-sm font-medium text-blue-200 mb-1">Weight Gain</div>
                      <div className="text-xl font-bold text-white">
                        {Math.round(user.daily_caloric_expenditure + 500)}
                      </div>
                      <div className="text-xs text-blue-200">+500 cal/day</div>
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