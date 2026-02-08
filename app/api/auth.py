from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..dependencies import get_user_service
from ..services.user_service import UserService
from ..core.security import create_access_token
from ..schemas.user import UserCreate, UserResponse, Token, UserLogin
from ..config import settings
from ..constants import ErrorMessages, SuccessMessages
from ..core.custom_exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InactiveUserError,
    BiometricValidationError
)


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user with biometric data"""
    try:
        user = user_service.create_user(user_data)
        return user
        
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BiometricValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Biometric validation failed: {e.errors}"
        )


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """Login user and return JWT token"""
    try:
        user = user_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except (InvalidCredentialsError, InactiveUserError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login-form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """Login with OAuth2 password form (for compatibility)"""
    try:
        user = user_service.authenticate_user(form_data.username, form_data.password)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except (InvalidCredentialsError, InactiveUserError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except (InvalidCredentialsError, InactiveUserError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token invalidation)
    
    Since we use stateless JWT tokens, logout is handled client-side
    by removing the token from storage. This endpoint confirms the logout.
    """
    return {
        "message": SuccessMessages.LOGOUT_SUCCESS,
        "instruction": "Remove the access token from your client storage"
    }