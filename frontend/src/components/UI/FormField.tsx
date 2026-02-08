import React, { useState, useCallback } from 'react'
import { Input, InputProps } from './Input'

export interface FormFieldProps extends Omit<InputProps, 'error'> {
  validate?: (value: string) => string
  onChange?: (value: string, isValid: boolean) => void
  value?: string
  error?: string
}

export const FormField: React.FC<FormFieldProps> = ({
  validate,
  onChange,
  value: controlledValue,
  error: externalError,
  ...inputProps
}) => {
  const [internalValue, setInternalValue] = useState('')
  const [internalError, setInternalError] = useState('')
  const [hasBlurred, setHasBlurred] = useState(false)

  const isControlled = controlledValue !== undefined
  const currentValue = isControlled ? controlledValue : internalValue
  const currentError = externalError || (hasBlurred ? internalError : '')

  const validateValue = useCallback((value: string) => {
    if (!validate) return ''
    return validate(value)
  }, [validate])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    
    if (!isControlled) {
      setInternalValue(newValue)
    }

    const errorMessage = validateValue(newValue)
    const isValid = !errorMessage

    if (!isControlled) {
      setInternalError(errorMessage)
    }

    if (onChange) {
      onChange(newValue, isValid)
    }
  }, [isControlled, validateValue, onChange])

  const handleBlur = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    setHasBlurred(true)
    
    const errorMessage = validateValue(currentValue)
    if (!isControlled) {
      setInternalError(errorMessage)
    }

    if (inputProps.onBlur) {
      inputProps.onBlur(e)
    }
  }, [currentValue, validateValue, isControlled, inputProps.onBlur])

  return (
    <Input
      {...inputProps}
      value={currentValue}
      onChange={handleChange}
      onBlur={handleBlur}
      error={currentError}
    />
  )
}