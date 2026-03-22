import React, { createContext, useContext, useState, useEffect } from 'react'

export type AppTheme = 'original' | 'dark' | 'light'

interface ThemeContextType {
  theme: AppTheme
  setTheme: (theme: AppTheme) => void
  hasChosen: boolean
  markChosen: () => void
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'original',
  setTheme: () => {},
  hasChosen: true,
  markChosen: () => {},
})

export const useTheme = () => useContext(ThemeContext)

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<AppTheme>(() => {
    return (localStorage.getItem('nova_theme') as AppTheme) || 'original'
  })

  const [hasChosen, setHasChosen] = useState<boolean>(() => {
    return localStorage.getItem('nova_theme_chosen') === '1'
  })

  useEffect(() => {
    if (theme === 'original') {
      document.documentElement.removeAttribute('data-theme')
    } else {
      document.documentElement.setAttribute('data-theme', theme)
    }
    localStorage.setItem('nova_theme', theme)
  }, [theme])

  const setTheme = (newTheme: AppTheme) => {
    setThemeState(newTheme)
  }

  const markChosen = () => {
    localStorage.setItem('nova_theme_chosen', '1')
    setHasChosen(true)
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, hasChosen, markChosen }}>
      {children}
    </ThemeContext.Provider>
  )
}

export default ThemeContext
