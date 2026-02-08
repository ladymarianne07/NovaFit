class NovaFitnessException(Exception):
    """Base exception for NovaFitness application"""
    pass


class AuthenticationError(NovaFitnessException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(NovaFitnessException):
    """Raised when user lacks permission for an action"""
    pass


class ValidationError(NovaFitnessException):
    """Raised when input validation fails"""
    pass


class NotFoundError(NovaFitnessException):
    """Raised when requested resource is not found"""
    pass


class ConflictError(NovaFitnessException):
    """Raised when there's a conflict (e.g., duplicate email)"""
    pass