import React from 'react'
import { Home, Utensils, Dumbbell, TrendingUp, Users } from 'lucide-react'
import { UserRole } from '../services/api'

interface BottomNavigationProps {
  activeTab?: string
  onTabChange?: (tab: string) => void
  role?: UserRole
  usesAppForSelf?: boolean
}

const STUDENT_TABS = [
  { id: 'dashboard', label: 'Home',     icon: Home },
  { id: 'meals',     label: 'Comidas',  icon: Utensils },
  { id: 'training',  label: 'Entreno',  icon: Dumbbell },
  { id: 'progress',  label: 'Progreso', icon: TrendingUp },
]

const TRAINER_TABS = [
  { id: 'dashboard', label: 'Home',    icon: Home },
  { id: 'students',  label: 'Alumnos', icon: Users },
]

// Trainer who also uses the app for themselves gets all student tabs + students tab
const TRAINER_FULL_TABS = [
  { id: 'dashboard', label: 'Home',     icon: Home },
  { id: 'meals',     label: 'Comidas',  icon: Utensils },
  { id: 'training',  label: 'Entreno',  icon: Dumbbell },
  { id: 'progress',  label: 'Progreso', icon: TrendingUp },
  { id: 'students',  label: 'Alumnos',  icon: Users },
]

const BottomNavigation: React.FC<BottomNavigationProps> = ({
  activeTab = 'dashboard',
  onTabChange,
  role,
  usesAppForSelf,
}) => {
  const tabs =
    role === 'trainer'
      ? usesAppForSelf ? TRAINER_FULL_TABS : TRAINER_TABS
      : STUDENT_TABS

  return (
    <nav className="bottom-navigation">
      <div className="bottom-navigation-container">
        {tabs.map((item) => {
          const IconComponent = item.icon
          const isActive = activeTab === item.id

          return (
            <button
              key={item.id}
              onClick={() => onTabChange?.(item.id)}
              className={`bottom-navigation-item ${isActive ? 'active' : ''}`}
              type="button"
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="bottom-navigation-icon">
                <IconComponent size={20} />
              </div>
              <span className="bottom-navigation-label">{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}

export default BottomNavigation
