import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .api import auth, users, events
from .db.database import create_tables
from .constants import AppConstants, StatusCodes
from .core.custom_exceptions import (
    NovaFitnessException, 
    BiometricValidationError,
    IncompleteBiometricDataError,
    BiometricCalculationError
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