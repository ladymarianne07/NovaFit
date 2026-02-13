"""
Service layer for biometric calculations and validation
Separates business logic from controllers and provides reusable components
"""
from typing import Optional, Tuple, Dict, Any
from ..schemas.user import Gender, ActivityLevel, FitnessObjective
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
    
    # ============================================================================
    # FITNESS OBJECTIVE AND MACRO CALCULATION METHODS
    # ============================================================================
    
    @staticmethod
    def get_calorie_delta_by_objective(objective: Optional[str], aggressiveness_level: Optional[int] = None) -> float:
        """
        Get the calorie delta (multiplier) based on fitness objective and aggressiveness level.
        
        Args:
            objective: The fitness objective (maintenance, fat_loss, muscle_gain, body_recomp, performance)
            aggressiveness_level: Level 1-3 for objectives that support it (None or 2 for default)
            
        Returns:
            Float representing the delta to multiply TDEE with (e.g., -0.25 for aggressive fat loss)
        """
        if not objective:
            return 0.0
        
        # Default to moderate (level 2) if not specified
        if aggressiveness_level is None:
            aggressiveness_level = 2
        
        objective_lower = objective.lower() if isinstance(objective, str) else objective.value
        
        # Define deltas for each objective and aggressiveness level
        objective_deltas = {
            'maintenance': {1: 0.00, 2: 0.00, 3: 0.00},
            'fat_loss': {1: -0.15, 2: -0.20, 3: -0.25},
            'muscle_gain': {1: 0.05, 2: 0.10, 3: 0.15},
            'body_recomp': {1: 0.00, 2: -0.05, 3: -0.10},
            'performance': {1: 0.00, 2: 0.00, 3: 0.05}
        }
        
        return objective_deltas.get(objective_lower, {}).get(aggressiveness_level, 0.0)
    
    @staticmethod
    def get_protein_factor_by_objective(objective: Optional[str]) -> float:
        """
        Get the protein factor (g/kg) based on fitness objective.
        
        Args:
            objective: The fitness objective
            
        Returns:
            Float representing grams of protein per kg of body weight
        """
        if not objective:
            return 1.6  # Default to maintenance
        
        objective_lower = objective.lower() if isinstance(objective, str) else objective.value
        
        protein_factors = {
            'maintenance': 1.6,
            'fat_loss': 2.0,
            'muscle_gain': 1.8,
            'body_recomp': 2.0,
            'performance': 1.6
        }
        
        return protein_factors.get(objective_lower, 1.6)
    
    @staticmethod
    def get_fat_percent_by_objective(objective: Optional[str]) -> float:
        """
        Get the fat percentage of calories based on fitness objective.
        
        Args:
            objective: The fitness objective
            
        Returns:
            Float representing the percentage of calories from fat (0.0-1.0)
        """
        if not objective:
            return 0.30  # Default to maintenance
        
        objective_lower = objective.lower() if isinstance(objective, str) else objective.value
        
        fat_percents = {
            'maintenance': 0.30,
            'fat_loss': 0.25,
            'muscle_gain': 0.25,
            'body_recomp': 0.25,
            'performance': 0.25
        }
        
        return fat_percents.get(objective_lower, 0.30)
    
    @classmethod
    def calculate_objective_targets(
        cls,
        tdee: float,
        weight_kg: float,
        objective: Optional[str] = None,
        aggressiveness_level: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate target calories and macronutrients based on objective.
        
        Args:
            tdee: Total Daily Energy Expenditure (maintenance calories)
            weight_kg: User's weight in kg
            objective: The fitness objective
            aggressiveness_level: Level 1-3 for intensity (None uses default)
            
        Returns:
            Dictionary with target_calories, protein_g, fat_g, carbs_g
        """
        # Calculate target calories based on objective delta
        calorie_delta = cls.get_calorie_delta_by_objective(objective, aggressiveness_level)
        target_calories = round(tdee * (1 + calorie_delta))
        
        # Macronutrient constants
        PROTEIN_CALS_PER_GRAM = 4
        FAT_CALS_PER_GRAM = 9
        CARB_CALS_PER_GRAM = 4
        
        # Calculate protein (g/kg based on objective)
        protein_factor = cls.get_protein_factor_by_objective(objective)
        protein_g = round(weight_kg * protein_factor)
        protein_kcal = protein_g * PROTEIN_CALS_PER_GRAM
        
        # Calculate fat (percentage based on objective)
        fat_percent = cls.get_fat_percent_by_objective(objective)
        fat_kcal = round(target_calories * fat_percent)
        fat_g = round(fat_kcal / FAT_CALS_PER_GRAM)
        
        # Calculate carbs (remainder)
        carb_kcal = target_calories - protein_kcal - fat_kcal
        
        # Ensure carb_kcal is not negative
        if carb_kcal < 0:
            # Reduce fat first, down to minimum 20% of calories
            min_fat_kcal = round(target_calories * 0.20)
            fat_kcal = min_fat_kcal
            fat_g = round(fat_kcal / FAT_CALS_PER_GRAM)
            carb_kcal = target_calories - protein_kcal - fat_kcal
            
            # If still negative, reduce protein slightly
            if carb_kcal < 0:
                protein_kcal = target_calories - fat_kcal  # Carbs get remainder
                protein_g = round(protein_kcal / PROTEIN_CALS_PER_GRAM)
                carb_kcal = 0
        
        carbs_g = round(carb_kcal / CARB_CALS_PER_GRAM)
        
        return {
            'target_calories': target_calories,
            'protein_g': protein_g,
            'fat_g': fat_g,
            'carbs_g': carbs_g
        }
    
    @classmethod
    def calculate_and_store_objective_targets(
        cls,
        user_instance: 'User'
    ) -> Dict[str, Any]:
        """
        Calculate and update objective-based targets for a user.
        
        Args:
            user_instance: User model instance with complete biometric data
            
        Returns:
            Dictionary with all calculated targets
        """
        # Ensure user has complete data
        if not user_instance.daily_caloric_expenditure or not user_instance.weight:
            raise BiometricValidationError(
                {"objective": "User must have complete biometric data (TDEE and weight)"}
            )
        
        # Calculate targets
        targets = cls.calculate_objective_targets(
            tdee=user_instance.daily_caloric_expenditure,
            weight_kg=user_instance.weight,
            objective=user_instance.objective,
            aggressiveness_level=user_instance.aggressiveness_level
        )
        
        # Update user instance
        user_instance.target_calories = targets['target_calories']
        user_instance.protein_target_g = targets['protein_g']
        user_instance.fat_target_g = targets['fat_g']
        user_instance.carbs_target_g = targets['carbs_g']
        
        return {
            'objective': user_instance.objective,
            'aggressiveness_level': user_instance.aggressiveness_level,
            'target_calories': user_instance.target_calories,
            'protein_target_g': user_instance.protein_target_g,
            'fat_target_g': user_instance.fat_target_g,
            'carbs_target_g': user_instance.carbs_target_g
        }