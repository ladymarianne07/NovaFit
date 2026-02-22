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
    
    # Validation error messages
    PASSWORD_TOO_SHORT = f"Password must be at least {8} characters long"
    PASSWORD_TOO_LONG = f"Password cannot exceed {72} characters (bcrypt limitation)"
    INVALID_EMAIL_FORMAT = "Invalid email format"
    NAME_TOO_SHORT = "Name cannot be empty"
    NAME_TOO_LONG = f"Name cannot exceed {100} characters"
    INVALID_AGE_RANGE = f"Age must be between {1} and {120} years"
    INVALID_WEIGHT_RANGE = f"Weight must be between {20.0} and {300.0} kg"
    INVALID_HEIGHT_RANGE = f"Height must be between {100.0} and {250.0} cm"
    INVALID_ACTIVITY_LEVEL = "Invalid activity level selected"


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
    MAX_PASSWORD_LENGTH = 72  # bcrypt limitation - truncate if longer
    MAX_EMAIL_LENGTH = 254    # RFC 5321 standard
    MIN_NAME_LENGTH = 1
    
    # Character limits for validation
    PASSWORD_BYTE_LIMIT = 72  # bcrypt cannot handle more than 72 bytes
    

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


class SkinfoldConstants:
    """Skinfold calculation and validation constants (Jackson & Pollock + Siri)."""
    MIN_AGE = 10
    MAX_AGE = 90
    RECOMMENDED_MIN_AGE = 18
    RECOMMENDED_MAX_AGE = 61

    MIN_WEIGHT_KG = 30.0
    MAX_WEIGHT_KG = 250.0

    MIN_SKINFOLD_MM = 0.0
    MAX_SKINFOLD_MM = 80.0
    SOFT_WARNING_SKINFOLD_MM = 60.0

    ROUND_PERCENT_DECIMALS = 1
    ROUND_KG_DECIMALS = 1
    ROUND_DENSITY_DECIMALS = 5

    JP7_SITE_NAMES = (
        "chest_mm",
        "midaxillary_mm",
        "triceps_mm",
        "subscapular_mm",
        "abdomen_mm",
        "suprailiac_mm",
        "thigh_mm",
    )

    JP3_SITE_NAMES = (
        "chest_mm",
        "abdomen_mm",
        "thigh_mm",
    )


class ProgressEvaluationConstants:
    """Constants for physical progress evaluation scoring and interpretation."""

    # Minimum records required for trend evaluation
    MIN_HISTORY_RECORDS = 2

    # Trend smoothing window
    RECENT_WINDOW_DAYS = 28

    # Supported analysis periods
    PERIOD_WEEK = "semana"
    PERIOD_MONTH = "mes"
    PERIOD_YEAR = "anio"

    PERIOD_WINDOW_DAYS = {
        PERIOD_WEEK: 7,
        PERIOD_MONTH: 30,
        PERIOD_YEAR: 365,
    }

    PERIOD_SCORE_MULTIPLIER = {
        PERIOD_WEEK: 0.5,
        PERIOD_MONTH: 1.0,
        PERIOD_YEAR: 1.2,
    }

    PERIOD_WEIGHT_FLUCTUATION_KG = {
        PERIOD_WEEK: 0.5,
        PERIOD_MONTH: 0.3,
        PERIOD_YEAR: 0.2,
    }

    PERIOD_BODY_COMP_FLUCTUATION_PERCENT = {
        PERIOD_WEEK: 0.5,
        PERIOD_MONTH: 0.3,
        PERIOD_YEAR: 0.2,
    }

    # Significant annual transformation criteria
    ANNUAL_SIGNIFICANT_FAT_CHANGE_PERCENT = 3.0
    ANNUAL_SIGNIFICANT_LEAN_MASS_KG = 3.0

    # Ignore normal fluctuations under these thresholds
    MIN_WEIGHT_FLUCTUATION_KG = 0.3
    MIN_BODY_COMP_FLUCTUATION_PERCENT = 0.3

    # Maintenance tolerance
    MAINTENANCE_MAX_WEIGHT_DEVIATION_PERCENT = 1.0
    MAINTENANCE_MAX_FAT_DEVIATION_PERCENT = 1.0

    # Trend blend: baseline delta + recent 4-week delta
    BASELINE_WEIGHT_FACTOR = 0.7
    RECENT_WEIGHT_FACTOR = 0.3

    # Classification thresholds
    POSITIVE_SCORE_THRESHOLD = 20
    STABLE_SCORE_MIN = -20

    # Score clamping
    MIN_SCORE = -100.0
    MAX_SCORE = 100.0
    

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
