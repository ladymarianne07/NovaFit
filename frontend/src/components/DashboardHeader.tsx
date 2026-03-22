import React from 'react'
import { LogOut, UserRound } from 'lucide-react'
import NotificationBell from './NotificationBell'
import { UserRole } from '../services/api'
import Logo from './Logo'

interface DashboardHeaderProps {
  activeTab: string
  onTabChange: (tab: string) => void
  onLogout: () => void
  role?: UserRole
}

const TAB_TITLES: Record<string, string> = {
  dashboard: 'Inicio',
  profile: 'Perfil',
  meals: 'Comidas',
  training: 'Entrenamiento',
  progress: 'Progreso',
  students: 'Alumnos',
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  activeTab,
  onTabChange,
  onLogout,
  role,
}) => {
  const title = TAB_TITLES[activeTab] || 'Inicio'

  return (
    <header className="dashboard-global-header" aria-label="Header principal">
      <div className="dashboard-global-header-brand">
        <Logo size={28} className="dashboard-global-header-logo" />
        <div className="dashboard-global-header-text">
          <p className="dashboard-global-header-app">NovaFitness</p>
          <h1 className="dashboard-global-header-title">{title}</h1>
        </div>
      </div>

      <div className="dashboard-global-header-actions">
        <NotificationBell />

        <button
          type="button"
          className={`dashboard-global-header-btn ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => onTabChange('profile')}
          aria-label="Ir a perfil"
        >
          <UserRound size={16} />
          <span>{role === 'trainer' ? 'Mi Perfil' : 'Perfil'}</span>
        </button>

        <button
          type="button"
          className="dashboard-global-header-btn logout"
          onClick={onLogout}
          aria-label="Cerrar sesión"
        >
          <LogOut size={16} />
          <span>Salir</span>
        </button>
      </div>
    </header>
  )
}

export default DashboardHeader
