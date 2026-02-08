from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .db.database import get_database_session
from .core.security import extract_user_id_from_token
from .services.user_service import UserService
from .services.biometric_service import BiometricService
from .db.models import User
from .constants import ErrorMessages
from .core.custom_exceptions import TokenValidationError


# Security scheme for Bearer token
security = HTTPBearer()


def get_user_service(db: Session = Depends(get_database_session)) -> UserService:
    """User service dependency injection"""
    return UserService(db)


def get_biometric_service() -> BiometricService:
    """Biometric service dependency injection"""
    return BiometricService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    Get current authenticated user from JWT token.
    Raises HTTP 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ErrorMessages.INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract user ID from token
        user_id = extract_user_id_from_token(credentials.credentials)
        if user_id is None:
            raise credentials_exception
        
        # Get user from database using service
        user = user_service.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise credentials_exception
        
        return user
    except TokenValidationError:
        raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.
    Additional layer for future role-based access control.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=ErrorMessages.INACTIVE_USER
        )
    return current_user