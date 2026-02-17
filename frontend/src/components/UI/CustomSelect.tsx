import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, Check } from 'lucide-react'

export interface CustomSelectOption {
  value: string
  label: string
  description?: string
}

interface CustomSelectProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  options: CustomSelectOption[]
  placeholder: string
  icon?: React.ReactNode
  error?: string
  required?: boolean
  disabled?: boolean
}

const CustomSelect: React.FC<CustomSelectProps> = ({
  id,
  label,
  value,
  onChange,
  options,
  placeholder,
  icon,
  error,
  required = false,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedOption = useMemo(
    () => options.find((option) => option.value === value),
    [options, value]
  )

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  return (
    <div className="login-field" ref={containerRef}>
      <label htmlFor={id} className="login-label">
        {label}{required ? ' *' : ''}
      </label>

      <div className="login-input-container custom-select-container">
        {icon && <div className="login-input-icon">{icon}</div>}

        <button
          id={id}
          type="button"
          className={`login-input custom-select-trigger ${error ? 'error' : ''} ${isOpen ? 'open' : ''}`.trim()}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-invalid={Boolean(error)}
          disabled={disabled}
          onClick={() => setIsOpen((prev) => !prev)}
        >
          <span className={`custom-select-value ${!selectedOption ? 'placeholder' : ''}`}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <ChevronDown className="custom-select-chevron" size={18} />
        </button>

        {isOpen && !disabled && (
          <div className="custom-select-panel" role="listbox" aria-label={label}>
            {options.map((option) => {
              const isSelected = option.value === value
              return (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`custom-select-option ${isSelected ? 'selected' : ''}`.trim()}
                  onClick={() => {
                    onChange(option.value)
                    setIsOpen(false)
                  }}
                >
                  <span className="custom-select-option-text">
                    <span className="custom-select-option-label">{option.label}</span>
                    {option.description && (
                      <span className="custom-select-option-description">{option.description}</span>
                    )}
                  </span>
                  {isSelected && <Check size={16} className="custom-select-check" />}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {error && <span className="login-field-error">{error}</span>}
    </div>
  )
}

export default CustomSelect
