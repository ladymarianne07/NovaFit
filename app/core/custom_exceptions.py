"""
Custom exceptions for the NovaFitness application
"""


class NovaFitnessException(Exception):
    """Base exception for NovaFitness application"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class UserAlreadyExistsError(NovaFitnessException):
    """Raised when trying to create a user that already exists"""
    pass


class UserNotFoundError(NovaFitnessException):
    """Raised when a user is not found"""
    pass


class InvalidCredentialsError(NovaFitnessException):
    """Raised when authentication fails"""
    pass


class InactiveUserError(NovaFitnessException):
    """Raised when trying to authenticate an inactive user"""
    pass


class BiometricValidationError(NovaFitnessException):
    """Raised when biometric data validation fails"""
    
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        message = "Biometric validation failed: " + "; ".join(f"{k}: {v}" for k, v in errors.items())
        super().__init__(message)


class IncompleteBiometricDataError(NovaFitnessException):
    """Raised when required biometric data is missing"""
    
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        message = f"Required biometric fields missing: {', '.join(missing_fields)}"
        super().__init__(message)


class BiometricCalculationError(NovaFitnessException):
    """Raised when biometric calculations fail"""
    pass


class TokenValidationError(NovaFitnessException):
    """Raised when JWT token validation fails"""
    pass