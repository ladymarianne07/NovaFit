"""
Application constants to eliminate magic numbers and hardcoded values
"""
from enum import Enum


# HTTP Status Messages
class ErrorMessages:
    """Centralized error messages"""
    EMAIL_ALREADY_EXISTS = "Email already registered"
    INVALID_CREDENTIALS = "Incorrect email or password"
    USER_NOT_FOUND = "User not found"
    INACTIVE_USER = "Inactive user"
    INVALID_TOKEN = "Could not validate credentials"
    BIOMETRIC_DATA_INCOMPLETE = "Incomplete biometric data for calculations"


# Success Messages
class SuccessMessages:
    """Centralized success messages"""
    USER_REGISTERED = "User registered successfully"
    LOGIN_SUCCESS = "Login successful"
    LOGOUT_SUCCESS = "Logout successful"
    PROFILE_UPDATED = "Profile updated successfully"
    

# Database Constants
class DatabaseConstants:
    """Database-related constants"""
    MAX_STRING_LENGTH = 255
    MAX_NAME_LENGTH = 100
    MAX_TITLE_LENGTH = 200
    MIN_PASSWORD_LENGTH = 8
    

# Biometric Constants
class BiometricConstants:
    """Biometric calculation constants"""
    # Mifflin-St Jeor equation constants
    WEIGHT_MULTIPLIER = 10.0
    HEIGHT_MULTIPLIER = 6.25
    AGE_MULTIPLIER = 5.0
    MALE_ADJUSTMENT = 5.0
    FEMALE_ADJUSTMENT = -161.0
    
    # Validation ranges
    MIN_AGE = 1
    MAX_AGE = 120
    MIN_WEIGHT = 20.0
    MAX_WEIGHT = 300.0
    MIN_HEIGHT = 100.0
    MAX_HEIGHT = 250.0
    
    # Calculation precision
    ROUNDING_PRECISION = 1
    
    # Activity levels with descriptions
    ACTIVITY_LEVELS = {
        1.20: "Sedentario real - Trabajo de escritorio, sin ejercicio",
        1.35: "Ligeramente activo - Ejercicio ligero 1-3 días/semana",
        1.50: "Moderadamente activo - Ejercicio moderado 3-5 días/semana",
        1.65: "Activo - Ejercicio intenso 6-7 días/semana",
        1.80: "Muy activo - Ejercicio muy intenso, trabajo físico"
    }
    

# Application Constants
class AppConstants:
    """General application constants"""
    DEFAULT_TOKEN_TYPE = "bearer"
    TIMEZONE_UTC = "UTC"
    JSON_INDENT = 2
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORT = 8000
    
    # Health check responses
    STATUS_HEALTHY = "healthy"
    STATUS_CONNECTED = "connected"
    
    # HTTP Methods
    ALLOWED_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    
    # Log levels
    LOG_LEVEL_INFO = "info"
    

# HTTP Status Codes
class StatusCodes:
    """Standard HTTP status codes for consistency"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
