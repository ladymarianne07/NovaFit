"""
Validation service for input data validation
Follows NovaFitness Backend Guidelines - centralized business logic in service layer
"""
import re
from typing import List, Optional
from ..constants import DatabaseConstants, BiometricConstants, ErrorMessages
from ..core.custom_exceptions import (
    PasswordValidationError, 
    EmailValidationError, 
    NameValidationError,
    InputValidationError,
    BiometricValidationError
)


class ValidationService:
    """Service for input data validation following business rules"""
    
    # Email regex pattern (RFC 5322 compliant)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    )
    
    @classmethod
    def validate_password(cls, password: str) -> None:
        """
        Validate password according to business rules
        
        Args:
            password: Password to validate
            
        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        if not password:
            raise PasswordValidationError("Password is required")
        
        if len(password) < DatabaseConstants.MIN_PASSWORD_LENGTH:
            raise PasswordValidationError(ErrorMessages.PASSWORD_TOO_SHORT)
        
        # Check byte length for bcrypt compatibility
        if len(password.encode('utf-8')) > DatabaseConstants.PASSWORD_BYTE_LIMIT:
            raise PasswordValidationError(ErrorMessages.PASSWORD_TOO_LONG)
    
    @classmethod
    def validate_email(cls, email: str) -> None:
        """
        Validate email format and length
        
        Args:
            email: Email to validate
            
        Raises:
            EmailValidationError: If email is invalid
        """
        if not email:
            raise EmailValidationError("Email is required")
        
        if len(email) > DatabaseConstants.MAX_EMAIL_LENGTH:
            raise EmailValidationError(f"Email cannot exceed {DatabaseConstants.MAX_EMAIL_LENGTH} characters")
        
        if not cls.EMAIL_PATTERN.match(email):
            raise EmailValidationError(ErrorMessages.INVALID_EMAIL_FORMAT)
    
    @classmethod
    def validate_name(cls, name: str, field_name: str = "Name") -> None:
        """
        Validate name fields (first_name, last_name)
        
        Args:
            name: Name to validate
            field_name: Name of the field for error messages
            
        Raises:
            NameValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise NameValidationError(f"{field_name} is required")
        
        if len(name.strip()) < DatabaseConstants.MIN_NAME_LENGTH:
            raise NameValidationError(f"{field_name} cannot be empty")
        
        if len(name) > DatabaseConstants.MAX_NAME_LENGTH:
            raise NameValidationError(f"{field_name} cannot exceed {DatabaseConstants.MAX_NAME_LENGTH} characters")
    
    @classmethod
    def validate_age(cls, age: int) -> None:
        """
        Validate age within acceptable range
        
        Args:
            age: Age to validate
            
        Raises:
            InputValidationError: If age is invalid
        """
        if not isinstance(age, int):
            raise InputValidationError("age", "Age must be a number")
        
        if age < BiometricConstants.MIN_AGE or age > BiometricConstants.MAX_AGE:
            raise InputValidationError("age", ErrorMessages.INVALID_AGE_RANGE)
    
    @classmethod
    def validate_weight(cls, weight: float) -> None:
        """
        Validate weight within acceptable range
        
        Args:
            weight: Weight to validate
            
        Raises:
            InputValidationError: If weight is invalid
        """
        if not isinstance(weight, (int, float)):
            raise InputValidationError("weight", "Weight must be a number")
        
        if weight < BiometricConstants.MIN_WEIGHT or weight > BiometricConstants.MAX_WEIGHT:
            raise InputValidationError("weight", ErrorMessages.INVALID_WEIGHT_RANGE)
    
    @classmethod
    def validate_height(cls, height: float) -> None:
        """
        Validate height within acceptable range
        
        Args:
            height: Height to validate
            
        Raises:
            InputValidationError: If height is invalid
        """
        if not isinstance(height, (int, float)):
            raise InputValidationError("height", "Height must be a number")
        
        if height < BiometricConstants.MIN_HEIGHT or height > BiometricConstants.MAX_HEIGHT:
            raise InputValidationError("height", ErrorMessages.INVALID_HEIGHT_RANGE)
    
    @classmethod
    def validate_activity_level(cls, activity_level: float) -> None:
        """
        Validate activity level is within accepted values
        
        Args:
            activity_level: Activity level to validate
            
        Raises:
            InputValidationError: If activity level is invalid
        """
        if not isinstance(activity_level, (int, float)):
            raise InputValidationError("activity_level", "Activity level must be a number")
        
        valid_levels = list(BiometricConstants.ACTIVITY_LEVELS.keys())
        if activity_level not in valid_levels:
            raise InputValidationError("activity_level", ErrorMessages.INVALID_ACTIVITY_LEVEL)
    
    @classmethod
    def validate_gender(cls, gender: str) -> None:
        """
        Validate gender is either 'male' or 'female'
        
        Args:
            gender: Gender to validate
            
        Raises:
            InputValidationError: If gender is invalid
        """
        if not gender:
            raise InputValidationError("gender", "Gender is required")
        
        valid_genders = ['male', 'female']
        if gender.lower() not in valid_genders:
            raise InputValidationError("gender", f"Gender must be one of: {', '.join(valid_genders)}")
    
    @classmethod
    def validate_user_data(cls, email: str, password: str, first_name: str, last_name: str) -> None:
        """
        Validate all user registration data
        
        Args:
            email: User email
            password: User password
            first_name: User first name
            last_name: User last name
            
        Raises:
            Various validation errors if data is invalid
        """
        cls.validate_email(email)
        cls.validate_password(password)
        cls.validate_name(first_name, "First name")
        cls.validate_name(last_name, "Last name")
    
    @classmethod
    def validate_biometric_data(cls, age: int, gender: str, weight: float, height: float, activity_level: float) -> None:
        """
        Validate all biometric data
        
        Args:
            age: User age
            gender: User gender
            weight: User weight
            height: User height
            activity_level: User activity level
            
        Raises:
            Various validation errors if data is invalid
        """
        cls.validate_age(age)
        cls.validate_gender(gender)
        cls.validate_weight(weight)
        cls.validate_height(height)
        cls.validate_activity_level(activity_level)
    
    @classmethod
    def truncate_password_if_needed(cls, password: str) -> str:
        """
        Truncate password to bcrypt limits if necessary
        
        Args:
            password: Original password
            
        Returns:
            Password truncated to bcrypt byte limit if needed
        """
        password_bytes = password.encode('utf-8')
        if len(password_bytes) <= DatabaseConstants.PASSWORD_BYTE_LIMIT:
            return password
            
        # Truncate to 72 bytes - simple approach that works for bcrypt
        # bcrypt will handle this properly even if we cut in middle of UTF-8 char
        truncated_bytes = password_bytes[:DatabaseConstants.PASSWORD_BYTE_LIMIT]
        
        # Try to decode, but if it fails (broken UTF-8), just use latin-1 which preserves bytes
        try:
            return truncated_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # If UTF-8 fails, use latin-1 which preserves all byte values
            # bcrypt will hash the bytes correctly regardless
            return truncated_bytes.decode('latin-1')