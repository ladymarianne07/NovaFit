import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .api import auth, users, events, nutrition, workout, routine, trainer, notifications, invite, diet
from .routers import food
from .db.database import create_tables, get_missing_user_columns
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
    InvalidCredentialsError,
    TrainerOnlyError,
    InviteNotFoundError,
    InviteAlreadyUsedError,
    InviteExpiredError,
    StudentAlreadyLinkedError,
    StudentNotLinkedError,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_OPENAPI_TAGS = [
    {
        "name": "authentication",
        "description": "Register, login and logout. Returns a **Bearer JWT** that must be sent in `Authorization` header for all protected routes.",
    },
    {
        "name": "users",
        "description": (
            "User profile, biometrics and fitness configuration. "
            "Updating biometrics automatically recalculates BMR/TDEE. "
            "Setting an objective automatically calculates macro targets."
        ),
    },
    {
        "name": "nutrition",
        "description": "Daily macronutrient tracking — consumed vs. targets. Also exposes the free-text meal logging endpoint.",
    },
    {
        "name": "diet",
        "description": (
            "AI-powered personalized diet plan generation and editing (Google Gemini). "
            "Includes meal tracker (complete/skip), daily macro accumulation, "
            "24-hour meal overrides and AI-generated meal alternatives."
        ),
    },
    {
        "name": "routines",
        "description": (
            "Workout routine management. Upload a PDF/image/text file or generate from an intake form — "
            "Gemini parses the content, extracts sessions and exercises, "
            "estimates calories and generates an HTML plan. "
            "Includes session progression tracker."
        ),
    },
    {
        "name": "workout",
        "description": (
            "Manual workout session logging with MET-based calorie estimation. "
            "Each session can contain multiple exercise blocks. "
            "Daily energy aggregation is available per date."
        ),
    },
    {
        "name": "food",
        "description": (
            "Free-text food parsing via Gemini AI → USDA/FatSecret calorie lookup. "
            "Also supports multi-source food search (USDA, FatSecret, OpenFoodFacts)."
        ),
    },
    {
        "name": "trainer",
        "description": (
            "Trainer-only endpoints. Trainers can invite students via a 7-day code, "
            "view their full profiles, and remotely update biometrics, objectives and nutrition targets. "
            "All changes notify the trainer."
        ),
    },
    {
        "name": "invite",
        "description": "Accept a trainer's invite code to link the student account to the trainer.",
    },
    {
        "name": "events",
        "description": "Append-only activity timeline. Events are never truly deleted (soft-delete only).",
    },
    {
        "name": "notifications",
        "description": "In-app notifications (invite accepted, biometric updates, etc.).",
    },
]

_OPENAPI_DESCRIPTION = """
## NovaFitness API

Fitness tracking and AI-powered nutrition/routine planning backend.

### Key features

| Module | Description |
|---|---|
| **Auth** | JWT-based authentication (PBKDF2-SHA256 passwords) |
| **Diet** | AI diet plan generation + meal tracker (Gemini) |
| **Routines** | PDF/image routine parsing + AI generation (Gemini) |
| **Nutrition** | Daily macro tracking (consumed vs. targets) |
| **Workout** | MET-based calorie estimation per session |
| **Food** | Free-text → calories via USDA / FatSecret / OpenFoodFacts |
| **Trainer** | Student management, invite codes, remote profile editing |

### Authentication

Send the JWT token as a Bearer header:

```
Authorization: Bearer <access_token>
```

Tokens are valid for **1 year** by default.

### External integrations

- **Google Gemini** — food parsing, routine/diet generation & editing, meal alternatives
- **USDA FoodData Central** — per-100g macro lookup
- **FatSecret** — branded food search (OAuth2)
- **OpenFoodFacts** — barcode-based product lookup
"""


def create_application() -> FastAPI:
    """Application factory pattern for better testability and configuration."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description=_OPENAPI_DESCRIPTION,
        openapi_tags=_OPENAPI_TAGS,
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.DEBUG,
        contact={
            "name": "NovaFitness",
            "email": "soporte@novafitness.app",
        },
        license_info={
            "name": "Proprietary",
        },
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


# ── Exception handler factory ─────────────────────────────────────────────────

# Table of (exception_class, http_status, error_code) for handlers that all
# return the same shape: {"detail": exc.message, "error_code": <literal>}.
_SIMPLE_ERROR_HANDLERS: list[tuple[type, int, str]] = [
    (PasswordValidationError,   StatusCodes.UNPROCESSABLE_ENTITY, "PASSWORD_VALIDATION_ERROR"),
    (EmailValidationError,      StatusCodes.UNPROCESSABLE_ENTITY, "EMAIL_VALIDATION_ERROR"),
    (NameValidationError,       StatusCodes.UNPROCESSABLE_ENTITY, "NAME_VALIDATION_ERROR"),
    (UserAlreadyExistsError,    StatusCodes.CONFLICT,             "USER_ALREADY_EXISTS"),
    (InvalidCredentialsError,   StatusCodes.UNAUTHORIZED,         "INVALID_CREDENTIALS"),
    (ValidationError,           StatusCodes.UNPROCESSABLE_ENTITY, "VALIDATION_ERROR"),
    (BiometricCalculationError, StatusCodes.INTERNAL_SERVER_ERROR,"BIOMETRIC_CALCULATION_ERROR"),
    (TrainerOnlyError,          StatusCodes.FORBIDDEN,            "TRAINER_ONLY"),
    (InviteNotFoundError,       StatusCodes.NOT_FOUND,            "INVITE_NOT_FOUND"),
    (InviteAlreadyUsedError,    StatusCodes.CONFLICT,             "INVITE_ALREADY_USED"),
    (InviteExpiredError,        410,                              "INVITE_EXPIRED"),
    (StudentAlreadyLinkedError, StatusCodes.CONFLICT,             "STUDENT_ALREADY_LINKED"),
    (StudentNotLinkedError,     StatusCodes.NOT_FOUND,            "STUDENT_NOT_LINKED"),
]


def _create_simple_error_handler(status_code: int, error_code: str):
    """Return an async handler that replies {detail, error_code} at the given status."""
    async def handler(request: Request, exc: NovaFitnessException) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.message, "error_code": error_code},
        )
    return handler


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers"""

    # Register all simple {detail, error_code} handlers from the table above
    for exc_class, status_code, error_code in _SIMPLE_ERROR_HANDLERS:
        app.add_exception_handler(exc_class, _create_simple_error_handler(status_code, error_code))

    # ── Custom handlers (unique response shapes) ──────────────────────────────

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI request validation errors (Pydantic validation failures)"""
        if exc.errors():
            first_error = exc.errors()[0]
            field_name = " -> ".join([str(loc) for loc in first_error["loc"][1:]])  # Skip 'body'
            error_msg = first_error["msg"]
            detail = f"{field_name}: {error_msg}" if field_name else error_msg
        else:
            detail = "Invalid input data"
        return JSONResponse(
            status_code=422,
            content={"detail": detail, "error_code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(InputValidationError)
    async def input_validation_exception_handler(request: Request, exc: InputValidationError):
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={"detail": exc.message, "field": exc.field, "error_code": "INPUT_VALIDATION_ERROR"},
        )

    @app.exception_handler(BiometricValidationError)
    async def biometric_validation_exception_handler(request: Request, exc: BiometricValidationError):
        return JSONResponse(
            status_code=StatusCodes.UNPROCESSABLE_ENTITY,
            content={"detail": "Biometric validation failed", "errors": exc.errors, "error_code": "BIOMETRIC_VALIDATION_ERROR"},
        )

    @app.exception_handler(IncompleteBiometricDataError)
    async def incomplete_biometric_data_exception_handler(request: Request, exc: IncompleteBiometricDataError):
        return JSONResponse(
            status_code=StatusCodes.BAD_REQUEST,
            content={"detail": exc.message, "missing_fields": exc.missing_fields, "error_code": "INCOMPLETE_BIOMETRIC_DATA"},
        )

    @app.exception_handler(NovaFitnessException)
    async def nova_fitness_exception_handler(request: Request, exc: NovaFitnessException):
        return JSONResponse(
            status_code=StatusCodes.BAD_REQUEST,
            content={"detail": exc.message, "error_code": exc.error_code},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=StatusCodes.INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred", "error_code": "INTERNAL_SERVER_ERROR"},
        )


def setup_routes(app: FastAPI) -> None:
    """Setup application routes"""
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(events.router)
    app.include_router(nutrition.router)
    app.include_router(workout.router)
    app.include_router(routine.router)
    app.include_router(diet.router)
    app.include_router(trainer.router)
    app.include_router(notifications.router)
    app.include_router(invite.router)
    app.include_router(food.router)
    
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
        missing_user_columns = get_missing_user_columns()

        return {
            "status": AppConstants.STATUS_HEALTHY,
            "database": AppConstants.STATUS_CONNECTED,
            "schema": {
                "status": "compatible" if not missing_user_columns else "out_of_sync",
                "missing_user_columns": missing_user_columns,
            },
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