from typing import Optional
from sqlalchemy.orm import Session
from ..db.models import User
from ..core.security import verify_password, get_password_hash
from ..core.biometrics import calculate_bmr, calculate_daily_caloric_expenditure, validate_biometric_data
from ..schemas.user import Gender
from datetime import datetime, timezone


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        return None
    
    # Update last login timestamp
    setattr(user, 'last_login', datetime.now(timezone.utc))
    db.commit()
    
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password: str, first_name: Optional[str] = None, 
                last_name: Optional[str] = None, age: Optional[int] = None, gender: Optional[Gender] = None,
                weight: Optional[float] = None, height: Optional[float] = None, 
                activity_level: Optional[float] = None) -> User:
    """
    Create a new user with optional biometric data.
    If biometric data is provided, calculate BMR and daily caloric expenditure.
    """
    # Check if user already exists
    if get_user_by_email(db, email):
        raise ValueError("User with this email already exists")
    
    hashed_password = get_password_hash(password)
    
    # Initialize BMR and caloric expenditure
    bmr = None
    daily_caloric_expenditure = None
    
    # If biometric data is provided, validate and calculate metrics
    if all([age is not None, gender is not None, weight is not None, height is not None, activity_level is not None]):
        validate_biometric_data(age=age, gender=gender, weight=weight, height=height, activity_level=activity_level)
        bmr = calculate_bmr(weight=weight, height=height, age=age, gender=gender)
        daily_caloric_expenditure = calculate_daily_caloric_expenditure(bmr=bmr, activity_level=activity_level)
    
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        age=age,
        gender=gender.value if gender else None,
        weight=weight,
        height=height,
        activity_level=activity_level,
        bmr=bmr,
        daily_caloric_expenditure=daily_caloric_expenditure
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_user_password(db: Session, user_id: int, new_password: str) -> bool:
    """Update user password"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    setattr(user, 'hashed_password', get_password_hash(new_password))
    db.commit()
    return True