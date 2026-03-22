import React from 'react'
import { useTheme, AppTheme } from '../contexts/ThemeContext'

interface ThemeOption {
  id: AppTheme
  name: string
  description: string
  previewBg: string
  previewAccent: string
  previewText: string
  previewCardBg: string
  previewNavBg: string
}

const THEME_OPTIONS: ThemeOption[] = [
  {
    id: 'original',
    name: 'Original',
    description: 'El diseño clásico de NovaFitness con gradientes violeta',
    previewBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
    previewAccent: '#a855f7',
    previewText: '#ffffff',
    previewCardBg: 'rgba(255,255,255,0.1)',
    previewNavBg: 'rgba(139, 92, 246, 0.3)',
  },
  {
    id: 'dark',
    name: 'Dark Mode',
    description: 'Diseño oscuro profundo con acentos cyan neón eléctrico',
    previewBg: 'linear-gradient(135deg, #020a0d 0%, #060e12 60%, #0c1a1f 100%)',
    previewAccent: '#00f5ff',
    previewText: '#e0f8fa',
    previewCardBg: 'rgba(0,245,255,0.06)',
    previewNavBg: 'rgba(0,245,255,0.1)',
  },
  {
    id: 'light',
    name: 'Light Mode',
    description: 'Diseño luminoso y fresco con acentos aqua tecnológicos',
    previewBg: 'linear-gradient(135deg, #ccfcff 0%, #e8feff 50%, #b0f0f4 100%)',
    previewAccent: '#00c8d8',
    previewText: '#0a1a1e',
    previewCardBg: 'rgba(255,255,255,0.85)',
    previewNavBg: 'rgba(0,200,216,0.15)',
  },
]

const ThemePreview: React.FC<{ option: ThemeOption; selected: boolean }> = ({ option, selected }) => (
  <div
    style={{
      width: '100%',
      height: '80px',
      borderRadius: '0.75rem',
      background: option.previewBg,
      position: 'relative',
      overflow: 'hidden',
      border: selected ? `2px solid ${option.previewAccent}` : '2px solid transparent',
      boxShadow: selected ? `0 0 12px ${option.previewAccent}55` : 'none',
      transition: 'all 0.2s ease',
    }}
  >
    {/* Mini header bar */}
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '22px',
        background: 'rgba(0,0,0,0.18)',
        display: 'flex',
        alignItems: 'center',
        paddingLeft: '8px',
        gap: '4px',
      }}
    >
      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: option.previewAccent }} />
      <div style={{ width: '24px', height: '4px', borderRadius: '2px', background: option.previewText, opacity: 0.5 }} />
    </div>
    {/* Mini card */}
    <div
      style={{
        position: 'absolute',
        top: '30px',
        left: '8px',
        right: '8px',
        height: '22px',
        borderRadius: '6px',
        background: option.previewCardBg,
        border: `1px solid ${option.previewAccent}33`,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: '8px',
        gap: '6px',
      }}
    >
      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: option.previewAccent }} />
      <div style={{ width: '40px', height: '3px', borderRadius: '2px', background: option.previewText, opacity: 0.4 }} />
    </div>
    {/* Mini nav */}
    <div
      style={{
        position: 'absolute',
        bottom: '4px',
        left: '8px',
        right: '8px',
        height: '14px',
        borderRadius: '8px',
        background: option.previewNavBg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
      }}
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: i === 1 ? '8px' : '6px',
            height: i === 1 ? '8px' : '5px',
            borderRadius: '50%',
            background: i === 1 ? option.previewAccent : option.previewText,
            opacity: i === 1 ? 1 : 0.35,
          }}
        />
      ))}
    </div>
  </div>
)

const ThemePickerModal: React.FC = () => {
  const { theme, setTheme, markChosen } = useTheme()

  const handleSelect = (selected: AppTheme) => {
    setTheme(selected)
    markChosen()
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(0,0,0,0.75)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '420px',
          background: 'linear-gradient(145deg, rgba(17,24,39,0.98), rgba(76,29,149,0.95))',
          border: '1px solid rgba(255,255,255,0.15)',
          borderRadius: '1.5rem',
          padding: '1.75rem 1.5rem',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          boxShadow: '0 24px 60px rgba(0,0,0,0.6)',
          animation: 'fadeIn 0.35s ease',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, #a855f7, #ec4899)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '0.75rem',
              fontSize: '1.5rem',
            }}
          >
            🎨
          </div>
          <h2
            style={{
              margin: 0,
              color: '#ffffff',
              fontSize: '1.3rem',
              fontWeight: 800,
              letterSpacing: '-0.01em',
            }}
          >
            Elige tu estilo
          </h2>
          <p
            style={{
              margin: '0.4rem 0 0',
              color: 'rgba(255,255,255,0.62)',
              fontSize: '0.85rem',
              lineHeight: 1.4,
            }}
          >
            Selecciona la apariencia de tu app. Puedes cambiarla desde tu perfil.
          </p>
        </div>

        {/* Theme Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '1.25rem' }}>
          {THEME_OPTIONS.map((option) => {
            const selected = theme === option.id
            return (
              <button
                key={option.id}
                onClick={() => handleSelect(option.id)}
                style={{
                  width: '100%',
                  background: selected
                    ? `linear-gradient(135deg, ${option.previewAccent}18, ${option.previewAccent}08)`
                    : 'rgba(255,255,255,0.04)',
                  border: selected
                    ? `1.5px solid ${option.previewAccent}66`
                    : '1.5px solid rgba(255,255,255,0.1)',
                  borderRadius: '1rem',
                  padding: '0.9rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.22s ease',
                  boxShadow: selected ? `0 4px 20px ${option.previewAccent}22` : 'none',
                }}
              >
                <ThemePreview option={option} selected={selected} />

                <div style={{ marginTop: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.5rem' }}>
                  <div>
                    <p
                      style={{
                        margin: 0,
                        color: selected ? option.previewAccent : '#ffffff',
                        fontSize: '0.95rem',
                        fontWeight: 700,
                        transition: 'color 0.2s',
                      }}
                    >
                      {option.name}
                    </p>
                    <p
                      style={{
                        margin: '0.2rem 0 0',
                        color: 'rgba(255,255,255,0.5)',
                        fontSize: '0.75rem',
                        lineHeight: 1.35,
                      }}
                    >
                      {option.description}
                    </p>
                  </div>
                  {selected && (
                    <div
                      style={{
                        flexShrink: 0,
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: option.previewAccent,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginTop: '2px',
                      }}
                    >
                      <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                        <path d="M2 6l3 3 5-5" stroke="#000" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>

        {/* Confirm button */}
        <button
          onClick={() => handleSelect(theme)}
          style={{
            width: '100%',
            padding: '0.85rem',
            background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
            border: 'none',
            borderRadius: '0.9rem',
            color: '#ffffff',
            fontSize: '0.95rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            letterSpacing: '0.01em',
          }}
        >
          Continuar con {THEME_OPTIONS.find((o) => o.id === theme)?.name}
        </button>
      </div>
    </div>
  )
}

export default ThemePickerModal
