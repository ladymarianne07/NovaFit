/**
 * Frontend validation service to match backend validation rules
 * Provides consistent validation across client and server
 */

// Constants matching backend
const VALIDATION_CONSTANTS = {
  MIN_PASSWORD_LENGTH: 8,
  MAX_PASSWORD_LENGTH: 72, // bcrypt limitation  
  MAX_EMAIL_LENGTH: 254,
  MIN_NAME_LENGTH: 1,
  MAX_NAME_LENGTH: 100,
  MIN_AGE: 1,
  MAX_AGE: 120,
  MIN_WEIGHT: 20.0,
  MAX_WEIGHT: 300.0,
  MIN_HEIGHT: 100.0,
  MAX_HEIGHT: 250.0,
  VALID_ACTIVITY_LEVELS: [1.20, 1.35, 1.50, 1.65, 1.80],
  VALID_GENDERS: ['male', 'female'],
  VALID_OBJECTIVES: ['maintenance', 'fat_loss', 'muscle_gain', 'body_recomp', 'performance'],
  VALID_AGGRESSIVENESS_LEVELS: [1, 2, 3]
}

// Error messages matching backend
const ERROR_MESSAGES = {
  PASSWORD_TOO_SHORT: `Password must be at least ${VALIDATION_CONSTANTS.MIN_PASSWORD_LENGTH} characters long`,
  PASSWORD_TOO_LONG: `Password cannot exceed ${VALIDATION_CONSTANTS.MAX_PASSWORD_LENGTH} characters (bcrypt limitation)`,
  INVALID_EMAIL_FORMAT: 'Invalid email format',
  NAME_TOO_SHORT: 'Name cannot be empty',
  NAME_TOO_LONG: `Name cannot exceed ${VALIDATION_CONSTANTS.MAX_NAME_LENGTH} characters`,
  INVALID_AGE_RANGE: `Age must be between ${VALIDATION_CONSTANTS.MIN_AGE} and ${VALIDATION_CONSTANTS.MAX_AGE} years`,
  INVALID_WEIGHT_RANGE: `Weight must be between ${VALIDATION_CONSTANTS.MIN_WEIGHT} and ${VALIDATION_CONSTANTS.MAX_WEIGHT} kg`,
  INVALID_HEIGHT_RANGE: `Height must be between ${VALIDATION_CONSTANTS.MIN_HEIGHT} and ${VALIDATION_CONSTANTS.MAX_HEIGHT} cm`,
  INVALID_ACTIVITY_LEVEL: 'Invalid activity level selected',
  INVALID_GENDER: 'Gender must be either male or female',
  INVALID_OBJECTIVE: 'Invalid fitness objective selected',
  INVALID_AGGRESSIVENESS_LEVEL: 'Aggressiveness level must be 1 (conservative), 2 (moderate), or 3 (aggressive)',
  FIELD_REQUIRED: 'This field is required'
}

// Email regex pattern (RFC 5322 compliant) - matches backend
const EMAIL_PATTERN = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

export interface ValidationResult {
  isValid: boolean
  error?: string
}

export class ValidationService {
  /**
   * Validate password according to business rules
   */
  static validatePassword(password: string): ValidationResult {
    if (!password) {
      return { isValid: false, error: ERROR_MESSAGES.FIELD_REQUIRED }
    }
    
    if (password.length < VALIDATION_CONSTANTS.MIN_PASSWORD_LENGTH) {
      return { isValid: false, error: ERROR_MESSAGES.PASSWORD_TOO_SHORT }
    }
    
    // Check byte length for bcrypt compatibility
    const passwordBytes = new TextEncoder().encode(password)
    if (passwordBytes.length > VALIDATION_CONSTANTS.MAX_PASSWORD_LENGTH) {
      return { isValid: false, error: ERROR_MESSAGES.PASSWORD_TOO_LONG }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate email format and length
   */
  static validateEmail(email: string): ValidationResult {
    if (!email) {
      return { isValid: false, error: ERROR_MESSAGES.FIELD_REQUIRED }
    }
    
    if (email.length > VALIDATION_CONSTANTS.MAX_EMAIL_LENGTH) {
      return { isValid: false, error: `Email cannot exceed ${VALIDATION_CONSTANTS.MAX_EMAIL_LENGTH} characters` }
    }
    
    if (!EMAIL_PATTERN.test(email)) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_EMAIL_FORMAT }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate name fields (first_name, last_name)
   */
  static validateName(name: string): ValidationResult {
    if (!name || !name.trim()) {
      return { isValid: false, error: ERROR_MESSAGES.NAME_TOO_SHORT }
    }
    
    if (name.trim().length < VALIDATION_CONSTANTS.MIN_NAME_LENGTH) {
      return { isValid: false, error: ERROR_MESSAGES.NAME_TOO_SHORT }
    }
    
    if (name.length > VALIDATION_CONSTANTS.MAX_NAME_LENGTH) {
      return { isValid: false, error: ERROR_MESSAGES.NAME_TOO_LONG }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate age within acceptable range
   */
  static validateAge(age: string | number): ValidationResult {
    const ageNum = typeof age === 'string' ? parseInt(age) : age
    
    if (isNaN(ageNum)) {
      return { isValid: false, error: 'Age must be a number' }
    }
    
    if (ageNum < VALIDATION_CONSTANTS.MIN_AGE || ageNum > VALIDATION_CONSTANTS.MAX_AGE) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_AGE_RANGE }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate weight within acceptable range
   */
  static validateWeight(weight: string | number): ValidationResult {
    const weightNum = typeof weight === 'string' ? parseFloat(weight) : weight
    
    if (isNaN(weightNum)) {
      return { isValid: false, error: 'Weight must be a number' }
    }
    
    if (weightNum < VALIDATION_CONSTANTS.MIN_WEIGHT || weightNum > VALIDATION_CONSTANTS.MAX_WEIGHT) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_WEIGHT_RANGE }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate height within acceptable range
   */
  static validateHeight(height: string | number): ValidationResult {
    const heightNum = typeof height === 'string' ? parseFloat(height) : height
    
    if (isNaN(heightNum)) {
      return { isValid: false, error: 'Height must be a number' }
    }
    
    if (heightNum < VALIDATION_CONSTANTS.MIN_HEIGHT || heightNum > VALIDATION_CONSTANTS.MAX_HEIGHT) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_HEIGHT_RANGE }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate activity level is within accepted values
   */
  static validateActivityLevel(activityLevel: string | number): ValidationResult {
    const level = typeof activityLevel === 'string' ? parseFloat(activityLevel) : activityLevel
    
    if (isNaN(level)) {
      return { isValid: false, error: 'Activity level must be a number' }
    }
    
    if (!VALIDATION_CONSTANTS.VALID_ACTIVITY_LEVELS.includes(level)) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_ACTIVITY_LEVEL }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate gender is either 'male' or 'female'
   */
  static validateGender(gender: string): ValidationResult {
    if (!gender) {
      return { isValid: false, error: ERROR_MESSAGES.FIELD_REQUIRED }
    }
    
    if (!VALIDATION_CONSTANTS.VALID_GENDERS.includes(gender.toLowerCase())) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_GENDER }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate fitness objective
   */
  static validateObjective(objective: string): ValidationResult {
    if (!objective) {
      return { isValid: false, error: ERROR_MESSAGES.FIELD_REQUIRED }
    }
    
    if (!VALIDATION_CONSTANTS.VALID_OBJECTIVES.includes(objective.toLowerCase())) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_OBJECTIVE }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate aggressiveness level (1-3)
   */
  static validateAggressivenessLevel(level: number | string): ValidationResult {
    const levelNum = typeof level === 'string' ? parseInt(level) : level
    
    if (isNaN(levelNum)) {
      return { isValid: false, error: 'Aggressiveness level must be a number' }
    }
    
    if (!VALIDATION_CONSTANTS.VALID_AGGRESSIVENESS_LEVELS.includes(levelNum)) {
      return { isValid: false, error: ERROR_MESSAGES.INVALID_AGGRESSIVENESS_LEVEL }
    }
    
    return { isValid: true }
  }
  
  /**
   * Validate all user registration data
   */
  static validateUserRegistration(data: {
    email: string
    password: string
    confirmPassword: string
    firstName: string
    lastName: string
    age: string | number
    gender: string
    weight: string | number
    height: string | number
    activityLevel: string | number
  }): { isValid: boolean; errors: Record<string, string> } {
    const errors: Record<string, string> = {}
    
    // Validate basic user data
    const emailResult = this.validateEmail(data.email)
    if (!emailResult.isValid) errors.email = emailResult.error!
    
    const passwordResult = this.validatePassword(data.password)
    if (!passwordResult.isValid) errors.password = passwordResult.error!
    
    // Confirm password match
    if (data.password !== data.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }
    
    const firstNameResult = this.validateName(data.firstName)
    if (!firstNameResult.isValid) errors.firstName = firstNameResult.error!
    
    const lastNameResult = this.validateName(data.lastName)
    if (!lastNameResult.isValid) errors.lastName = lastNameResult.error!
    
    // Validate biometric data
    const ageResult = this.validateAge(data.age)
    if (!ageResult.isValid) errors.age = ageResult.error!
    
    const genderResult = this.validateGender(data.gender)
    if (!genderResult.isValid) errors.gender = genderResult.error!
    
    const weightResult = this.validateWeight(data.weight)
    if (!weightResult.isValid) errors.weight = weightResult.error!
    
    const heightResult = this.validateHeight(data.height)
    if (!heightResult.isValid) errors.height = heightResult.error!
    
    const activityResult = this.validateActivityLevel(data.activityLevel)
    if (!activityResult.isValid) errors.activityLevel = activityResult.error!
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    }
  }
  
  /**
   * Truncate password if needed for bcrypt compatibility (matches backend)
   */
  static truncatePasswordIfNeeded(password: string): string {
    const passwordBytes = new TextEncoder().encode(password)
    if (passwordBytes.length > VALIDATION_CONSTANTS.MAX_PASSWORD_LENGTH) {
      // Truncate to 72 bytes, being careful not to break UTF-8 encoding
      const truncated = passwordBytes.slice(0, VALIDATION_CONSTANTS.MAX_PASSWORD_LENGTH)
      try {
        return new TextDecoder().decode(truncated)
      } catch {
        // If we broke a multi-byte character, truncate further
        for (let i = VALIDATION_CONSTANTS.MAX_PASSWORD_LENGTH - 3; i < VALIDATION_CONSTANTS.MAX_PASSWORD_LENGTH; i++) {
          try {
            return new TextDecoder().decode(passwordBytes.slice(0, i))
          } catch {
            continue
          }
        }
        // Fallback
        return new TextDecoder('utf-8', { fatal: false }).decode(passwordBytes.slice(0, VALIDATION_CONSTANTS.MAX_PASSWORD_LENGTH - 3))
      }
    }
    return password
  }
}

export default ValidationService