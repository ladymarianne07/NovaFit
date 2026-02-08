"""
Service layer for biometric calculations and validation
Separates business logic from controllers and provides reusable components
"""
from typing import Optional, Tuple
from ..schemas.user import Gender, ActivityLevel
from ..constants import BiometricConstants, ErrorMessages
from ..core.custom_exceptions import BiometricValidationError


class BiometricService:
    """Service for biometric calculations and validation"""
    
    @staticmethod
    def calculate_bmr(weight: float, height: float, age: int, gender: Gender) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation
        
        Args:
            weight: Weight in kg
            height: Height in cm  
            age: Age in years
            gender: Gender (male/female)
        
        Returns:
            BMR in kcal/day
        """
        base = (
            BiometricConstants.WEIGHT_MULTIPLIER * weight +
            BiometricConstants.HEIGHT_MULTIPLIER * height -
            BiometricConstants.AGE_MULTIPLIER * age
        )
        
        if gender == Gender.MALE:
            return base + BiometricConstants.MALE_ADJUSTMENT
        else:
            return base + BiometricConstants.FEMALE_ADJUSTMENT
    
    @staticmethod
    def calculate_daily_caloric_expenditure(bmr: float, activity_level: float) -> float:
        """
        Calculate Total Daily Energy Expenditure (TDEE)
        
        Args:
            bmr: Basal Metabolic Rate in kcal/day
            activity_level: Activity multiplier (1.20 - 1.80)
        
        Returns:
            Daily caloric expenditure in kcal/day
        """
        return bmr * activity_level
    
    @classmethod
    def calculate_user_metrics(
        cls,
        weight: Optional[float],
        height: Optional[float], 
        age: Optional[int],
        gender: Optional[Gender],
        activity_level: Optional[ActivityLevel]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate BMR and daily caloric expenditure for a user
        
        Returns:
            Tuple of (bmr, daily_caloric_expenditure) or (None, None) if data incomplete
        """
        # Check if we have all required data
        if not all([weight is not None, height is not None, age is not None, 
                   gender is not None, activity_level is not None]):
            return None, None
        
        try:
            # Type assertions since we checked for None above
            assert weight is not None
            assert height is not None  
            assert age is not None
            assert gender is not None
            assert activity_level is not None
            
            # Calculate BMR
            bmr = cls.calculate_bmr(weight, height, age, gender)
            
            # Calculate daily expenditure
            activity_value = activity_level.value if isinstance(activity_level, ActivityLevel) else activity_level
            daily_expenditure = cls.calculate_daily_caloric_expenditure(bmr, activity_value)
            
            # Round to 1 decimal place for practical use
            return (round(bmr, 1), round(daily_expenditure, 1))
            
        except (ValueError, TypeError):
            return None, None
    
    @staticmethod
    def get_activity_level_description(activity_level: float) -> str:
        """
        Get human-readable description of activity level
        """
        return BiometricConstants.ACTIVITY_LEVELS.get(
            activity_level, 
            f"Nivel personalizado ({activity_level})"
        )
    
    @staticmethod
    def validate_biometric_data(
        weight: Optional[float] = None,
        height: Optional[float] = None,
        age: Optional[int] = None,
        gender: Optional[Gender] = None,
        activity_level: Optional[ActivityLevel] = None
    ) -> None:
        """
        Validate biometric data and raise BiometricValidationError if invalid
        
        Raises:
            BiometricValidationError: If any validation fails
        """
        errors = {}
        
        if weight is not None:
            if weight < BiometricConstants.MIN_WEIGHT or weight > BiometricConstants.MAX_WEIGHT:
                errors["weight"] = f"El peso debe estar entre {BiometricConstants.MIN_WEIGHT} y {BiometricConstants.MAX_WEIGHT} kg"
        
        if height is not None:
            if height < BiometricConstants.MIN_HEIGHT or height > BiometricConstants.MAX_HEIGHT:
                errors["height"] = f"La altura debe estar entre {BiometricConstants.MIN_HEIGHT} y {BiometricConstants.MAX_HEIGHT} cm"
        
        if age is not None:
            if age < BiometricConstants.MIN_AGE or age > BiometricConstants.MAX_AGE:
                errors["age"] = f"La edad debe estar entre {BiometricConstants.MIN_AGE} y {BiometricConstants.MAX_AGE} años"
        
        if activity_level is not None:
            valid_levels = list(BiometricConstants.ACTIVITY_LEVELS.keys())
            level_value = activity_level.value if isinstance(activity_level, ActivityLevel) else activity_level
            if level_value not in valid_levels:
                errors["activity_level"] = f"Nivel de actividad debe ser uno de: {valid_levels}"
        
        if errors:
            raise BiometricValidationError(errors)
        
    @classmethod
    def update_user_biometrics_with_recalculation(
        cls,
        current_user: 'User',
        **biometric_updates
    ) -> Tuple[float, float]:
        """
        Update user biometric data and automatically recalculate BMR and TDEE
        
        Args:
            current_user: Current user instance
            **biometric_updates: Fields to update (age, gender, weight, height, activity_level)
            
        Returns:
            Tuple of (new_bmr, new_daily_caloric_expenditure)
            
        Raises:
            BiometricValidationError: If any biometric data is invalid
        """
        from ..db.models import User  # Import here to avoid circular import
        
        # Get current values or use updated values
        weight = biometric_updates.get('weight', current_user.weight)
        height = biometric_updates.get('height', current_user.height)
        age = biometric_updates.get('age', current_user.age)
        gender_value = biometric_updates.get('gender', current_user.gender)
        activity_level_value = biometric_updates.get('activity_level', current_user.activity_level)
        
        # Convert string gender back to enum if needed
        if isinstance(gender_value, str):
            gender = Gender.MALE if gender_value.lower() == 'male' else Gender.FEMALE
        else:
            gender = gender_value
            
        # Convert activity level to float if it's an enum
        if isinstance(activity_level_value, ActivityLevel):
            activity_level = activity_level_value.value
        else:
            activity_level = activity_level_value
        
        # Validate all biometric data before updating
        cls.validate_biometric_data(
            weight=weight,
            height=height,
            age=age,
            gender=gender,
            activity_level=ActivityLevel(activity_level) if isinstance(activity_level, float) else activity_level
        )
        
        # Calculate new metrics
        bmr, daily_expenditure = cls.calculate_user_metrics(
            weight=weight,
            height=height,
            age=age,
            gender=gender,
            activity_level=ActivityLevel(activity_level) if isinstance(activity_level, float) else activity_level
        )
        
        return bmr, daily_expenditure
    
    @staticmethod
    def has_complete_biometric_data(
        weight: Optional[float] = None,
        height: Optional[float] = None,
        age: Optional[int] = None,
        gender: Optional[Gender] = None,
        activity_level: Optional[ActivityLevel] = None
    ) -> bool:
        """
        Check if all required biometric data is provided
        
        Returns:
            True if all biometric fields are present and not None
        """
        return all([
            weight is not None,
            height is not None,
            age is not None,
            gender is not None,
            activity_level is not None
        ])
    
    @classmethod
    def recalculate_user_metrics(cls, user_instance) -> Tuple[Optional[float], Optional[float]]:
        """
        Recalculate BMR and daily caloric expenditure for an existing user
        
        Args:
            user_instance: User model instance with biometric data
            
        Returns:
            Tuple of (bmr, daily_caloric_expenditure) or (None, None) if incomplete data
        """
        # Check if user has complete biometric data
        if not cls.has_complete_biometric_data(
            weight=user_instance.weight,
            height=user_instance.height,
            age=user_instance.age,
            gender=Gender(user_instance.gender) if user_instance.gender else None,
            activity_level=ActivityLevel(user_instance.activity_level) if user_instance.activity_level else None
        ):
            return None, None
        
        # Convert to proper types
        gender = Gender(user_instance.gender)
        activity_level = ActivityLevel(user_instance.activity_level)
        
        return cls.calculate_user_metrics(
            weight=user_instance.weight,
            height=user_instance.height,
            age=user_instance.age,
            gender=gender,
            activity_level=activity_level
        )