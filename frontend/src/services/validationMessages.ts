const messageMap: Record<string, string> = {
  'This field is required': 'Este campo es obligatorio',
  'Invalid email format': 'El formato del correo electrónico no es válido',
  'Password must be at least 8 characters long': 'La contraseña debe tener al menos 8 caracteres',
  'Password cannot exceed 72 characters (bcrypt limitation)': 'La contraseña no puede superar los 72 caracteres',
  'Name cannot be empty': 'Este campo no puede estar vacío',
  'Name cannot exceed 100 characters': 'Este campo no puede tener más de 100 caracteres',
  'Age must be a number': 'La edad debe ser un número',
  'Age must be between 1 and 120 years': 'La edad debe estar entre 1 y 120 años',
  'Weight must be a number': 'El peso debe ser un número',
  'Weight must be between 20 and 300 kg': 'El peso debe estar entre 20 y 300 kg',
  'Height must be a number': 'La altura debe ser un número',
  'Height must be between 100 and 250 cm': 'La altura debe estar entre 100 y 250 cm',
  'Activity level must be a number': 'El nivel de actividad debe ser un número',
  'Invalid activity level selected': 'Selecciona un nivel de actividad válido',
  'Gender must be either male or female': 'Selecciona un género válido',
  'Passwords do not match': 'Las contraseñas no coinciden',
  'Please confirm your password': 'Confirma tu contraseña'
}

export const translateValidationMessage = (message?: string): string => {
  if (!message) {
    return 'Por favor, revisa los campos del formulario'
  }

  if (messageMap[message]) {
    return messageMap[message]
  }

  return message
}

export const requiredFieldMessage = (fieldName: string): string => `${fieldName} es obligatorio`
