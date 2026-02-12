import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .api import auth, users, events
from .db.database import create_tables
from .constants import AppConstants, StatusCodes
from .core.custom_exceptions import (
    NovaFitnessException, 
    BiometricValidationError,
    IncompleteBiometricDataError,
    BiometricCalculationError,
    ValidationError,
    PasswordValidationError,
    EmailValidationError,
    NameValidationError,
    InputValidationError,
    UserAlreadyExistsError,
    InvalidCredentialsError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Application factory pattern for better testability and configuration
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Private pilot fitness tracking API",
        debug=settings.DEBUG
    )
    
    # Initialize database tables
    try:
        create_tables()
        logger.info("✅ Database tables initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Error initializing database tables: {e}")
        # In production, you might want to exit the application here
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include API routes
    setup_routes(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Setup application middleware"""
    # CORS middleware for PWA support
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=AppConstants.ALLOWED_HTTP_METHODS,
        allow_headers=["*"],
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers"""
    
    # FastAPI default validation error handler (handles Pydantic validation errors)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI request validation errors (Pydantic validation failures)"""
        # Extract the first error message for user-friendly display  
        if exc.errors():
            first_error = exc.errors()[0]
            field_name = " -> ".join([str(loc) for loc in first_error["loc"][1:]])  # Skip 'body'
            error_msg = first_error["msg"]
            detail = f"{field_name}: {error_msg}" if field_name else error_msg
        else:
            detail = "Invalid input data"
        
        return JSONResponse(
            status_code=422,
            content={
                "detail": detail,
                "error_code": "VALIDATION_ERROR"
            }
        )
    
    # Validation error handlers (most specific first)
    @app.exception_handler(PasswordValidationError)
    async def password_validation_exception_handler(request: Request, exc: PasswordValidationError):
        """Handle password validation errors"""
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.message,
                "error_code": "PASSWORD_VALIDATION_ERROR"
            }
        )
    
    @app.exception_handler(EmailValidationError)
    async def email_validation_exception_handler(request: Request, exc: EmailValidationError):
        """Handle email validation errors"""
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.message,
                "error_code": "EMAIL_VALIDATION_ERROR"
            }
        )
    
    @app.exception_handler(NameValidationError)
    async def name_validation_exception_handler(request: Request, exc: NameValidationError):
        """Handle name validation errors"""
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.message,
                "error_code": "NAME_VALIDATION_ERROR"
            }
        )
    
    @app.exception_handler(InputValidationError)
    async def input_validation_exception_handler(request: Request, exc: InputValidationError):
        """Handle input validation errors"""
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.message,
                "field": exc.field,
                "error_code": "INPUT_VALIDATION_ERROR"
            }
        )
    
    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_exception_handler(request: Request, exc: UserAlreadyExistsError):
        """Handle user already exists errors"""
        return JSONResponse(
            status_code=StatusCodes.CONFLICT,
            content={
                "detail": exc.message,
                "error_code": "USER_ALREADY_EXISTS"
            }
        )
    
    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_exception_handler(request: Request, exc: InvalidCredentialsError):
        """Handle invalid credentials errors"""
        return JSONResponse(
            status_code=StatusCodes.UNAUTHORIZED,
            content={
                "detail": exc.message,
                "error_code": "INVALID_CREDENTIALS"
            }
        )
    
    # General validation error handler
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle general validation errors"""
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.message,
                "error_code": "VALIDATION_ERROR"
            }
        )
    
    @app.exception_handler(BiometricValidationError)
    async def biometric_validation_exception_handler(request: Request, exc: BiometricValidationError):
        """Handle biometric validation errors with detailed field information"""
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={
                "detail": "Biometric validation failed",
                "errors": exc.errors,
                "error_code": "BIOMETRIC_VALIDATION_ERROR"
            }
        )
    
    @app.exception_handler(IncompleteBiometricDataError)
    async def incomplete_biometric_data_exception_handler(request: Request, exc: IncompleteBiometricDataError):
        """Handle incomplete biometric data errors"""
        return JSONResponse(
            status_code=StatusCodes.BAD_REQUEST,
            content={
                "detail": exc.message,
                "missing_fields": exc.missing_fields,
                "error_code": "INCOMPLETE_BIOMETRIC_DATA"
            }
        )
    
    @app.exception_handler(BiometricCalculationError)
    async def biometric_calculation_exception_handler(request: Request, exc: BiometricCalculationError):
        """Handle biometric calculation errors"""
        return JSONResponse(
            status_code=StatusCodes.INTERNAL_SERVER_ERROR,
            content={
                "detail": exc.message,
                "error_code": "BIOMETRIC_CALCULATION_ERROR"
            }
        )
    
    @app.exception_handler(NovaFitnessException)
    async def nova_fitness_exception_handler(request: Request, exc: NovaFitnessException):
        """Handle custom NovaFitness exceptions"""
        return JSONResponse(
            status_code=StatusCodes.BAD_REQUEST,
            content={
                "detail": exc.message,
                "error_code": exc.error_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=StatusCodes.INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


def setup_routes(app: FastAPI) -> None:
    """Setup application routes"""
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(events.router)
    
    @app.get("/")
    async def root():
        """Health check endpoint"""
        return {
            "app": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "healthy"
        }

    @app.get("/health")
    async def health_check():
        """Detailed health check with actual timestamp"""
        return {
            "status": AppConstants.STATUS_HEALTHY,
            "database": AppConstants.STATUS_CONNECTED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.VERSION
        }


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=AppConstants.DEFAULT_HOST,  # Allow external connections (for tunnel)
        port=AppConstants.DEFAULT_PORT,
        reload=settings.DEBUG,
        log_level=AppConstants.LOG_LEVEL_INFO
    )