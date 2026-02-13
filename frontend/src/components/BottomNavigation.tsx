import React from 'react'
import { Home, Utensils, Dumbbell, TrendingUp, LogOut } from 'lucide-react'

interface BottomNavigationProps {
  activeTab?: string
  onTabChange?: (tab: string) => void
  onLogout?: () => void
}

const BottomNavigation: React.FC<BottomNavigationProps> = ({
  activeTab = 'profile',
  onTabChange,
  onLogout
}) => {
  const navigationItems = [
    {
      id: 'profile',
      label: 'Perfil',
      icon: Home,
      onClick: () => onTabChange?.('profile')
    },
    {
      id: 'meals',
      label: 'Comidas',
      icon: Utensils,
      onClick: () => onTabChange?.('meals')
    },
    {
      id: 'training',
      label: 'Entrenamiento',
      icon: Dumbbell,
      onClick: () => onTabChange?.('training')
    },
    {
      id: 'progress',
      label: 'Progreso',
      icon: TrendingUp,
      onClick: () => onTabChange?.('progress')
    },
    {
      id: 'logout',
      label: 'Logout',
      icon: LogOut,
      onClick: onLogout
    }
  ]

  return (
    <nav className="bottom-navigation">
      <div className="bottom-navigation-container">
        {navigationItems.map((item) => {
          const IconComponent = item.icon
          const isActive = activeTab === item.id
          
          return (
            <button
              key={item.id}
              onClick={item.onClick}
              className={`bottom-navigation-item ${isActive ? 'active' : ''}`}
              type="button"
            >
              <div className="bottom-navigation-icon">
                <IconComponent size={20} />
              </div>
              <span className="bottom-navigation-label">
                {item.label}
              </span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}

export default BottomNavigation