# 🏗️ NovaFitness Development Guidelines

## Overview
This document establishes the architectural patterns, coding standards, and best practices for the NovaFitness FastAPI application. Follow these guidelines to maintain code quality, consistency, and scalability.

## 🎯 Core Principles

### 1. Clean Code Fundamentals
- **Single Responsibility**: Each function/class should have one reason to change
- **DRY (Don't Repeat Yourself)**: Eliminate code duplication
- **Explicit Naming**: Names should reveal intent without comments
- **Small Functions**: Keep functions focused and concise
- **No Magic Numbers**: Use constants for all hardcoded values

### 2. SOLID Principles
- **S**ingle Responsibility Principle
- **O**pen/Closed Principle  
- **L**iskov Substitution Principle
- **I**nterface Segregation Principle
- **D**ependency Inversion Principle

## 🏛️ Architecture Pattern

### Service Layer Architecture
```
┌─────────────────┐
│   Controllers   │  ← API Routes (Presentation Layer)
│   (API Layer)   │
└─────────────────┘
          │
┌─────────────────┐
│    Services     │  ← Business Logic Layer
│ (Business Layer)│
└─────────────────┘
          │
┌─────────────────┐
│     Models      │  ← Data Access Layer
│  (Data Layer)   │
└─────────────────┘
```

### Layer Responsibilities

#### Controllers (API Layer)
- **Purpose**: Handle HTTP requests/responses
- **Responsibilities**: 
  - Request validation
  - Response formatting
  - HTTP status codes
  - Authentication/authorization
- **NOT Allowed**: Business logic, calculations, data validation

#### Services (Business Layer)
- **Purpose**: Implement business logic
- **Responsibilities**:
  - Core business rules
  - Data validation
  - Calculations and algorithms
  - Orchestrating multiple operations
- **NOT Allowed**: HTTP-specific code, direct database access

#### Models (Data Layer)
- **Purpose**: Data persistence and structure
- **Responsibilities**:
  - Database schema definition
  - Data relationships
  - Query optimization
- **NOT Allowed**: Business logic

## 📁 File Organization

### Directory Structure
```
app/
├── constants.py              # All constants and configuration values
├── core/
│   ├── __init__.py
│   └── custom_exceptions.py  # Custom exception hierarchy
├── services/
│   ├── __init__.py
│   ├── base_service.py       # Base service class (if needed)
│   ├── biometric_service.py  # Health calculations
│   ├── user_service.py       # User management
│   └── [feature]_service.py  # Feature-specific services
├── api/
│   ├── __init__.py
│   ├── auth.py              # Authentication endpoints
│   └── [feature].py         # Feature-specific endpoints
├── db/
│   ├── __init__.py
│   ├── database.py          # Database configuration
│   └── models.py            # SQLAlchemy models
├── schemas/
│   ├── __init__.py
│   ├── user.py              # User-related schemas
│   └── [feature].py         # Feature-specific schemas
├── dependencies.py          # Dependency injection
└── main.py                  # Application factory
```

### File Naming Conventions
- **Services**: `[feature]_service.py` (e.g., `user_service.py`)
- **Controllers**: `[feature].py` (e.g., `auth.py`)
- **Models**: Use descriptive names (e.g., `user.py`, `event.py`)
- **Schemas**: Match model names (e.g., `user.py`)

## 🔧 Implementation Guidelines

### 1. Constants Management

#### ✅ DO: Centralize all constants
```python
# constants.py
class BiometricConstants:
    WEIGHT_MULTIPLIER = 10
    HEIGHT_MULTIPLIER = 6.25
    AGE_MULTIPLIER = 5
    MALE_FACTOR = 5
    FEMALE_FACTOR = -161
    
    MIN_WEIGHT = 20.0
    MAX_WEIGHT = 300.0
```

#### ❌ DON'T: Use magic numbers
```python
# Bad
bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
```

### 2. Service Implementation

#### ✅ DO: Create focused services
```python
# services/biometric_service.py
from app.constants import BiometricConstants
from app.core.custom_exceptions import InvalidBiometricDataError

class BiometricService:
    def calculate_bmr(self, weight: float, height: float, age: int, gender: str) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation."""
        self._validate_biometric_data(weight, height, age)
        
        base_metabolic = (
            BiometricConstants.WEIGHT_MULTIPLIER * weight +
            BiometricConstants.HEIGHT_MULTIPLIER * height -
            BiometricConstants.AGE_MULTIPLIER * age
        )
        
        gender_factor = (
            BiometricConstants.MALE_FACTOR if gender.lower() == 'male'
            else BiometricConstants.FEMALE_FACTOR
        )
        
        return base_metabolic + gender_factor
    
    def _validate_biometric_data(self, weight: float, height: float, age: int) -> None:
        """Validate biometric input data."""
        if not (BiometricConstants.MIN_WEIGHT <= weight <= BiometricConstants.MAX_WEIGHT):
            raise InvalidBiometricDataError(f"Weight must be between {BiometricConstants.MIN_WEIGHT}-{BiometricConstants.MAX_WEIGHT} kg")
```

#### ❌ DON'T: Put business logic in controllers
```python
# Bad - in controller
@router.post("/register")
async def register(user_data: UserCreate):
    # Business logic should not be here
    bmr = (10 * user_data.weight) + (6.25 * user_data.height) - (5 * user_data.age) + 5
    # ... more business logic
```

### 3. Controller Implementation

#### ✅ DO: Keep controllers thin
```python
# api/auth.py
from app.services.user_service import UserService
from app.core.custom_exceptions import UserAlreadyExistsError
from fastapi import HTTPException

@router.post("/register", status_code=201)
async def register(user_data: UserCreate, user_service: UserService = Depends(get_user_service)):
    """Register a new user."""
    try:
        user = await user_service.create_user(user_data)
        return {"message": "User registered successfully", "user": user}
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

### 4. Exception Handling

#### ✅ DO: Use custom exceptions
```python
# core/custom_exceptions.py
class NovaFitnessException(Exception):
    """Base exception for NovaFitness application."""
    pass

class ValidationError(NovaFitnessException):
    """Base class for validation errors."""
    pass

class InvalidBiometricDataError(ValidationError):
    """Raised when biometric data is invalid."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
```

#### Global Exception Handler
```python
# main.py
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

## 📝 Coding Standards

### 1. Function Guidelines
```python
# ✅ Good function structure
def calculate_daily_calories(bmr: float, activity_level: str) -> float:
    """
    Calculate daily calorie needs based on BMR and activity level.
    
    Args:
        bmr: Basal Metabolic Rate in kcal/day
        activity_level: Activity level (sedentary, light, moderate, active, very_active)
    
    Returns:
        Daily calorie needs in kcal/day
        
    Raises:
        InvalidActivityLevelError: If activity level is not recognized
    """
    if activity_level not in ActivityConstants.ACTIVITY_MULTIPLIERS:
        raise InvalidActivityLevelError(f"Invalid activity level: {activity_level}")
    
    multiplier = ActivityConstants.ACTIVITY_MULTIPLIERS[activity_level]
    return bmr * multiplier
```

### 2. Class Guidelines
```python
# ✅ Good class structure
class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: AsyncSession, biometric_service: BiometricService):
        self.db = db
        self.biometric_service = biometric_service
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user with biometric calculations."""
        # Implementation here
        pass
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials."""
        # Implementation here
        pass
```

### 3. Naming Conventions
- **Classes**: PascalCase (e.g., `UserService`, `BiometricService`)
- **Functions**: snake_case (e.g., `calculate_bmr`, `create_user`)
- **Variables**: snake_case (e.g., `user_data`, `activity_level`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_WEIGHT`, `DEFAULT_ACTIVITY`)
- **Files**: snake_case (e.g., `user_service.py`, `custom_exceptions.py`)

## 🧪 Testing Guidelines

### 1. Test Structure
```python
# tests/test_biometric_service.py
import pytest
from app.services.biometric_service import BiometricService
from app.core.custom_exceptions import InvalidBiometricDataError

class TestBiometricService:
    def setup_method(self):
        self.service = BiometricService()
    
    def test_calculate_bmr_male(self):
        """Test BMR calculation for male user."""
        result = self.service.calculate_bmr(weight=70, height=175, age=30, gender='male')
        expected = 1676.25  # Pre-calculated expected value
        assert abs(result - expected) < 0.01
    
    def test_invalid_weight_raises_exception(self):
        """Test that invalid weight raises appropriate exception."""
        with pytest.raises(InvalidBiometricDataError):
            self.service.calculate_bmr(weight=500, height=175, age=30, gender='male')
```

### 2. Test Categories
- **Unit Tests**: Test individual service methods
- **Integration Tests**: Test service interactions
- **API Tests**: Test endpoint responses
- **End-to-End Tests**: Test complete user flows

## 🚀 Adding New Features

### Step-by-Step Process

#### 1. Define Constants
```python
# constants.py
class NewFeatureConstants:
    DEFAULT_VALUE = 100
    MAX_ITEMS = 50
    VALIDATION_PATTERN = r'^[a-zA-Z0-9]+$'
```

#### 2. Create Custom Exceptions
```python
# core/custom_exceptions.py
class NewFeatureError(NovaFitnessException):
    """Base exception for new feature."""
    pass
```

#### 3. Create Database Model
```python
# db/models.py
class NewFeature(Base):
    __tablename__ = "new_features"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(DatabaseConstants.STRING_MEDIUM), nullable=False)
```

#### 4. Create Pydantic Schemas
```python
# schemas/new_feature.py
class NewFeatureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=NewFeatureConstants.MAX_NAME_LENGTH)

class NewFeatureResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
```

#### 5. Create Service Layer
```python
# services/new_feature_service.py
class NewFeatureService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_new_feature(self, data: NewFeatureCreate) -> NewFeature:
        """Create a new feature."""
        # Business logic here
        pass
```

#### 6. Create API Controller
```python
# api/new_feature.py
from fastapi import APIRouter, Depends
from app.services.new_feature_service import NewFeatureService

router = APIRouter()

@router.post("/", response_model=NewFeatureResponse)
async def create_new_feature(
    data: NewFeatureCreate,
    service: NewFeatureService = Depends(get_new_feature_service)
):
    """Create a new feature."""
    return await service.create_new_feature(data)
```

#### 7. Add Dependency Injection
```python
# dependencies.py
async def get_new_feature_service(db: AsyncSession = Depends(get_db)) -> NewFeatureService:
    return NewFeatureService(db)
```

#### 8. Register Router
```python
# main.py
from app.api import new_feature

app.include_router(new_feature.router, prefix="/new-features", tags=["new-features"])
```

## ⚡ Performance Guidelines

### 1. Database Queries
- Use async/await for all database operations
- Implement pagination for large datasets
- Use database indexes appropriately
- Avoid N+1 query problems

### 2. Service Layer
- Keep services stateless when possible
- Use dependency injection for better testability
- Cache expensive calculations when appropriate

### 3. API Layer
- Use appropriate HTTP status codes
- Implement request/response validation
- Add rate limiting for public endpoints

## 🔒 Security Guidelines

### 1. Input Validation
- Always validate user input at the service layer
- Use Pydantic schemas for request validation
- Sanitize data before database operations

### 2. Authentication/Authorization
- Use JWT tokens with appropriate expiration
- Implement proper password hashing
- Add rate limiting for authentication endpoints

### 3. Error Handling
- Don't expose sensitive information in error messages
- Log security-related events
- Use custom exceptions for business logic errors

## 📚 Documentation Standards

### 1. Code Documentation
- Use docstrings for all classes and functions
- Include type hints for all parameters and return values
- Document exceptions that can be raised

### 2. API Documentation
- FastAPI automatically generates OpenAPI documentation
- Add descriptions to endpoints and models
- Include example request/response data

## 🎯 Code Review Checklist

Before submitting code, ensure:

- [ ] No hardcoded values (use constants)
- [ ] Business logic is in service layer
- [ ] Controllers are thin and focused
- [ ] Custom exceptions are used appropriately
- [ ] Functions have single responsibility
- [ ] Code follows naming conventions
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] No code duplication
- [ ] Type hints are present

## 🔄 Maintenance Guidelines

### Regular Tasks
1. **Review Constants**: Ensure all hardcoded values are in constants
2. **Refactor Services**: Keep business logic centralized
3. **Update Tests**: Maintain test coverage above 80%
4. **Review Dependencies**: Keep dependencies up to date
5. **Monitor Performance**: Profile slow endpoints

### Code Quality Metrics
- **Cyclomatic Complexity**: Keep functions under 10
- **Test Coverage**: Maintain above 80%
- **Code Duplication**: Less than 3%
- **Documentation Coverage**: 100% for public APIs

## 🚀 Conclusion

Following these guidelines ensures that the NovaFitness application remains:
- **Maintainable**: Easy to modify and extend
- **Testable**: Comprehensive test coverage
- **Scalable**: Architecture supports growth
- **Reliable**: Consistent error handling and validation
- **Secure**: Proper authentication and input validation

Remember: **Clean code is not written by following a set of rules. Clean code is written by programmers who care about their craft.**