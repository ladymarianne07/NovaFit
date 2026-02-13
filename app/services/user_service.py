"""
User service layer - handles all user-related business logic
Separates business logic from controllers and database operations
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..db.models import User
from ..schemas.user import UserCreate, Gender, ActivityLevel, UserBiometricsUpdate
from ..core.security import get_password_hash, verify_password
from ..services.biometric_service import BiometricService
from ..services.validation_service import ValidationService
from ..constants import ErrorMessages
from ..core.custom_exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
    InactiveUserError
)


class UserService:
    """Service for user-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_all_users(self) -> list[User]:
        """Get all users (for admin/development purposes)"""
        return self.db.query(User).all()
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with biometric data and calculations
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user instance
            
        Raises:
            UserAlreadyExistsError: If user with email already exists
            PasswordValidationError: If password doesn't meet requirements
            EmailValidationError: If email is invalid
            NameValidationError: If names are invalid
            InputValidationError: If biometric data is invalid
        """
        # STEP 1: Validate all input data (following Backend Guidelines)
        ValidationService.validate_user_data(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        # Validate biometric data
        ValidationService.validate_biometric_data(
            age=user_data.age,
            gender=user_data.gender.value,
            weight=user_data.weight,
            height=user_data.height,
            activity_level=user_data.activity_level.value
        )
        
        # STEP 2: Check if user already exists
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError(ErrorMessages.EMAIL_ALREADY_EXISTS)
        
        # STEP 3: Calculate metrics (all biometric data is now required and validated)
        bmr, daily_caloric_expenditure = self._calculate_user_metrics(user_data)
        
        # STEP 4: Truncate password if needed for bcrypt compatibility
        safe_password = ValidationService.truncate_password_if_needed(user_data.password)
        
        # STEP 5: Create user instance
        hashed_password = get_password_hash(safe_password)
        
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            age=user_data.age,
            gender=user_data.gender.value if user_data.gender else None,
            weight=user_data.weight,
            height=user_data.height,
            activity_level=user_data.activity_level.value if user_data.activity_level else None,
            bmr=bmr,
            daily_caloric_expenditure=daily_caloric_expenditure,
            objective=user_data.objective.value if user_data.objective else None,
            aggressiveness_level=user_data.aggressiveness_level
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # STEP 6: Calculate objective-based targets if objective is specified
        if db_user.objective:
            objective_targets = BiometricService.calculate_and_store_objective_targets(db_user)
            self.db.commit()
            self.db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Authenticated user
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            InactiveUserError: If user is inactive
        """
        user = self.get_user_by_email(email)
        if not user:
            raise InvalidCredentialsError(ErrorMessages.INVALID_CREDENTIALS)
        
        if not verify_password(password, str(user.hashed_password)):
            raise InvalidCredentialsError(ErrorMessages.INVALID_CREDENTIALS)
        
        if not user.is_active:
            raise InactiveUserError(ErrorMessages.INACTIVE_USER)
        
        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        
        return user
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """
        Update user password
        
        Args:
            user_id: User ID
            new_password: New plain text password
            
        Returns:
            True if successful, False if user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True
    
    def update_user_profile(self, user: User, **updates) -> User:
        """
        Update user profile fields
        
        Args:
            user: User instance to update
            **updates: Fields to update
            
        Returns:
            Updated user instance
        """
        for field, value in updates.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def _has_complete_biometric_data(self, user_data: UserCreate) -> bool:
        """
        Check if user data contains complete biometric information
        """
        return all([
            user_data.age is not None,
            user_data.gender is not None,
            user_data.weight is not None,
            user_data.height is not None,
            user_data.activity_level is not None
        ])
    
    def _calculate_user_metrics(self, user_data: UserCreate) -> tuple[Optional[float], Optional[float]]:
        """
        Calculate BMR and daily caloric expenditure for user data
        """
        if not self._has_complete_biometric_data(user_data):
            return None, None
        
        return BiometricService.calculate_user_metrics(
            weight=user_data.weight,
            height=user_data.height,
            age=user_data.age,
            gender=user_data.gender,
            activity_level=user_data.activity_level
        )
        
    def update_user_biometrics(self, user: User, biometric_data: UserBiometricsUpdate) -> User:
        """
        Update user biometric data and automatically recalculate BMR and TDEE
        
        This method follows the requirement that when any biometric field is updated,
        the caloric expenditure calculations must be recalculated automatically.
        
        Args:
            user: User instance to update
            biometric_data: New biometric data
            
        Returns:
            Updated user instance with recalculated metrics
            
        Raises:
            BiometricValidationError: If validation fails
        """
        # Prepare update dictionary with only non-None values
        updates = {}
        
        if biometric_data.age is not None:
            updates['age'] = biometric_data.age
        if biometric_data.gender is not None:
            updates['gender'] = biometric_data.gender.value
        if biometric_data.weight is not None:
            updates['weight'] = biometric_data.weight
        if biometric_data.height is not None:
            updates['height'] = biometric_data.height
        if biometric_data.activity_level is not None:
            updates['activity_level'] = biometric_data.activity_level.value
        
        # If any biometric field is being updated, recalculate metrics
        if updates:
            # Calculate new BMR and daily expenditure with updated values
            new_bmr, new_daily_expenditure = BiometricService.update_user_biometrics_with_recalculation(
                current_user=user,
                **updates
            )
            
            # Update the user instance
            for field, value in updates.items():
                setattr(user, field, value)
            
            # Update calculated values
            user.bmr = new_bmr
            user.daily_caloric_expenditure = new_daily_expenditure
            
            # Commit changes
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def update_user_profile_with_biometrics(self, user: User, **updates) -> User:
        """
        Update user profile fields including biometric data with automatic recalculation
        
        Args:
            user: User instance to update
            **updates: Fields to update (includes both profile and biometric fields)
            
        Returns:
            Updated user instance
        """
        # Separate biometric fields from profile fields
        biometric_fields = {'age', 'gender', 'weight', 'height', 'activity_level'}
        biometric_updates = {k: v for k, v in updates.items() if k in biometric_fields and v is not None}
        profile_updates = {k: v for k, v in updates.items() if k not in biometric_fields and v is not None}
        
        # Update profile fields
        for field, value in profile_updates.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        # Update biometric fields with recalculation if any biometric data changed
        if biometric_updates:
            # Calculate new metrics
            new_bmr, new_daily_expenditure = BiometricService.update_user_biometrics_with_recalculation(
                current_user=user,
                **biometric_updates
            )
            
            # Apply biometric updates
            for field, value in biometric_updates.items():
                if field == 'gender' and isinstance(value, Gender):
                    setattr(user, field, value.value)
                elif field == 'activity_level' and isinstance(value, ActivityLevel):
                    setattr(user, field, value.value)
                else:
                    setattr(user, field, value)
            
            # Update calculated values
            user.bmr = new_bmr
            user.daily_caloric_expenditure = new_daily_expenditure
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_calculated_metrics(self, user: User, bmr: float, daily_expenditure: float) -> User:
        """Update user's calculated BMR and daily expenditure metrics"""
        user.bmr = bmr
        user.daily_caloric_expenditure = daily_expenditure
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user_objective(
        self, 
        user: User, 
        objective: str, 
        aggressiveness_level: Optional[int] = None
    ) -> User:
        """
        Update user's fitness objective and recalculate targets
        
        Args:
            user: User instance to update
            objective: Fitness objective (maintenance, fat_loss, muscle_gain, body_recomp, performance)
            aggressiveness_level: Optional level 1-3 for intensity (None uses default)
            
        Returns:
            Updated user instance with recalculated targets
            
        Raises:
            ValueError: If user doesn't have complete biometric data
        """
        # Store new objective values
        user.objective = objective
        user.aggressiveness_level = aggressiveness_level
        
        # Calculate and store new targets
        try:
            BiometricService.calculate_and_store_objective_targets(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e