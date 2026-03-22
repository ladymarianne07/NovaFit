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


class ValidationError(NovaFitnessException):
    """Base class for validation errors"""
    pass


class PasswordValidationError(ValidationError):
    """Raised when password validation fails"""
    pass


class EmailValidationError(ValidationError):
    """Raised when email validation fails"""
    pass


class NameValidationError(ValidationError):
    """Raised when name validation fails"""
    pass


class InputValidationError(ValidationError):
    """Raised when general input validation fails"""
    
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error for {field}: {message}")


class WorkoutValidationError(ValidationError):
    """Raised when workout session input data is invalid."""
    pass


class WorkoutActivityNotFoundError(NovaFitnessException):
    """Raised when activity mapping cannot resolve a valid activity key."""
    pass


class WorkoutWeightRequiredError(NovaFitnessException):
    """Raised when calories calculation requires user weight and none is available."""
    pass


class RoutineNotFoundError(NovaFitnessException):
    """Raised when the user has no active routine."""
    pass


class RoutineParsingError(NovaFitnessException):
    """Raised when Gemini fails to parse the routine file."""
    pass


class RoutineFileTooLargeError(NovaFitnessException):
    """Raised when the uploaded routine file exceeds the size limit."""
    pass


class RoutineInvalidFileTypeError(NovaFitnessException):
    """Raised when the uploaded file type is not supported."""
    pass


# ── Trainer module exceptions ──────────────────────────────────────────────────

class TrainerOnlyError(NovaFitnessException):
    """Raised when a non-trainer user attempts a trainer-only action."""
    pass


class InviteNotFoundError(NovaFitnessException):
    """Raised when an invite code does not exist."""
    pass


class InviteAlreadyUsedError(NovaFitnessException):
    """Raised when an invite code has already been redeemed."""
    pass


class InviteExpiredError(NovaFitnessException):
    """Raised when an invite code is past its expiry date."""
    pass


class StudentAlreadyLinkedError(NovaFitnessException):
    """Raised when a student is already linked to an active trainer."""
    pass


class StudentNotLinkedError(NovaFitnessException):
    """Raised when a student is not linked to the requesting trainer."""
    pass