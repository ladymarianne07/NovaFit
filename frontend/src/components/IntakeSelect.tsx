/**
 * IntakeSelect — Shared portal-based custom dropdown for intake forms.
 * Used by both RoutineModule and DietModule.
 */
import React, { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Check, ChevronDown } from 'lucide-react'

export interface IntakeSelectOption {
  value: string
  label: string
}

export interface IntakeSelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: IntakeSelectOption[]
  required?: boolean
  disabled?: boolean
}

const IntakeSelect: React.FC<IntakeSelectProps> = ({
  label,
  value,
  onChange,
  options,
  required,
  disabled,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const [panelStyle, setPanelStyle] = useState<React.CSSProperties>({})
  const selectedLabel = options.find((o) => o.value === value)?.label ?? ''

  useEffect(() => {
    if (!isOpen) return
    const handleClick = (e: MouseEvent) => {
      if (triggerRef.current && !triggerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [isOpen])

  const handleOpen = () => {
    if (disabled) return
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPanelStyle({
        position: 'fixed',
        top: rect.bottom + 6,
        left: rect.left,
        width: rect.width,
        zIndex: 1300,
      })
    }
    setIsOpen((prev) => !prev)
  }

  return (
    <div className="routine-intake-field">
      <label className="routine-intake-label">
        {label}{required && <span className="routine-required"> *</span>}
      </label>
      <button
        ref={triggerRef}
        type="button"
        className="routine-intake-select routine-select-trigger"
        onClick={handleOpen}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span>{selectedLabel}</span>
        <ChevronDown
          size={15}
          style={{
            flexShrink: 0,
            transform: isOpen ? 'rotate(180deg)' : undefined,
            transition: 'transform 0.2s ease',
          }}
        />
      </button>
      {isOpen && createPortal(
        <div className="custom-select-panel" style={panelStyle} role="listbox">
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              role="option"
              aria-selected={opt.value === value}
              className={`custom-select-option ${opt.value === value ? 'selected' : ''}`}
              onClick={() => { onChange(opt.value); setIsOpen(false) }}
            >
              <span className="custom-select-option-text">
                <span className="custom-select-option-label">{opt.label}</span>
              </span>
              {opt.value === value && <Check size={15} className="custom-select-check" />}
            </button>
          ))}
        </div>,
        document.body,
      )}
    </div>
  )
}

export default IntakeSelect
