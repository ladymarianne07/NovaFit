"""
Nutrition Service - Business logic for macronutrient tracking and calculations

This service handles:
- Daily macronutrient target calculations  
- Meal logging and nutrition tracking
- Progress calculations for macros
- AI-powered nutrition suggestions
"""
from datetime import date, datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.models import User, DailyNutrition, Event
from ..schemas.nutrition import (
    MacronutrientResponse, 
    MacronutrientTargets, 
    DailyNutritionCreate,
    DailyNutritionResponse,
    MealLogCreate,
    MealLogResponse
)
from ..core.custom_exceptions import UserNotFoundError, ValidationError


class NutritionService:
    """Service for nutrition and macronutrient operations"""
    
    # Macronutrient ratios (industry standard for balanced diet)
    DEFAULT_CARB_RATIO = 0.50    # 50% of calories from carbs
    DEFAULT_PROTEIN_RATIO = 0.25  # 25% of calories from protein  
    DEFAULT_FAT_RATIO = 0.25     # 25% of calories from fat
    
    # Calories per gram for each macronutrient
    CARB_CALORIES_PER_GRAM = 4
    PROTEIN_CALORIES_PER_GRAM = 4
    FAT_CALORIES_PER_GRAM = 9


    @classmethod
    def calculate_macronutrient_targets(cls, user: User) -> MacronutrientTargets:
        """
        Calculate daily macronutrient targets based on user's TDEE
        
        Args:
            user: User with calculated daily_caloric_expenditure
            
        Returns:
            MacronutrientTargets with carbs, protein, fat in grams
        """
        if not user.daily_caloric_expenditure:
            raise ValidationError("User must have calculated daily caloric expenditure")
        
        total_calories = user.daily_caloric_expenditure
        
        # Calculate calories for each macro
        carb_calories = total_calories * cls.DEFAULT_CARB_RATIO
        protein_calories = total_calories * cls.DEFAULT_PROTEIN_RATIO
        fat_calories = total_calories * cls.DEFAULT_FAT_RATIO
        
        # Convert to grams
        carbs_grams = carb_calories / cls.CARB_CALORIES_PER_GRAM
        protein_grams = protein_calories / cls.PROTEIN_CALORIES_PER_GRAM  
        fat_grams = fat_calories / cls.FAT_CALORIES_PER_GRAM
        
        return MacronutrientTargets(
            carbs=round(carbs_grams, 1),
            protein=round(protein_grams, 1), 
            fat=round(fat_grams, 1)
        )


    @classmethod
    def get_or_create_daily_nutrition(
        cls, 
        db: Session, 
        user_id: int, 
        target_date: Optional[date] = None
    ) -> DailyNutrition:
        """
        Get or create daily nutrition record for user
        
        Args:
            db: Database session
            user_id: User ID
            target_date: Date to track (defaults to today)
            
        Returns:
            DailyNutrition record
        """
        if target_date is None:
            target_date = date.today()
            
        # Convert date to datetime for database query
        start_date = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_date = start_date + timedelta(days=1)
        
        # Try to find existing record
        nutrition = db.query(DailyNutrition).filter(
            DailyNutrition.user_id == user_id,
            DailyNutrition.date >= start_date,
            DailyNutrition.date < end_date
        ).first()
        
        if nutrition:
            return nutrition
            
        # Create new record with calculated targets
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
            
        targets = cls.calculate_macronutrient_targets(user)
        
        nutrition = DailyNutrition(
            user_id=user_id,
            date=start_date,
            carbs_target=targets.carbs,
            protein_target=targets.protein,
            fat_target=targets.fat,
            carbs_consumed=0.0,
            protein_consumed=0.0, 
            fat_consumed=0.0,
            total_calories=0.0
        )
        
        db.add(nutrition)
        db.commit()
        db.refresh(nutrition)
        
        return nutrition


    @classmethod
    def get_macronutrient_progress(
        cls, 
        db: Session, 
        user_id: int,
        target_date: Optional[date] = None
    ) -> MacronutrientResponse:
        """
        Get current macronutrient progress for user
        
        Args:
            db: Database session  
            user_id: User ID
            target_date: Date to check (defaults to today)
            
        Returns:
            MacronutrientResponse with progress percentages
        """
        nutrition = cls.get_or_create_daily_nutrition(db, user_id, target_date)
        
        # Calculate percentages
        carb_percentage = (nutrition.carbs_consumed / nutrition.carbs_target * 100) if nutrition.carbs_target > 0 else 0
        protein_percentage = (nutrition.protein_consumed / nutrition.protein_target * 100) if nutrition.protein_target > 0 else 0
        fat_percentage = (nutrition.fat_consumed / nutrition.fat_target * 100) if nutrition.fat_target > 0 else 0
        
        # Calculate total calories from consumed macros
        total_calories = (
            nutrition.carbs_consumed * cls.CARB_CALORIES_PER_GRAM +
            nutrition.protein_consumed * cls.PROTEIN_CALORIES_PER_GRAM +  
            nutrition.fat_consumed * cls.FAT_CALORIES_PER_GRAM
        )
        
        # Get user's calorie target
        user = db.query(User).filter(User.id == user_id).first()
        calories_target = user.daily_caloric_expenditure if user else 2000
        calories_percentage = (total_calories / calories_target * 100) if calories_target > 0 else 0
        
        return MacronutrientResponse(
            carbs=nutrition.carbs_consumed,
            protein=nutrition.protein_consumed,
            fat=nutrition.fat_consumed,
            carbs_target=nutrition.carbs_target,
            protein_target=nutrition.protein_target,
            fat_target=nutrition.fat_target,
            carbs_percentage=round(carb_percentage, 1),
            protein_percentage=round(protein_percentage, 1),
            fat_percentage=round(fat_percentage, 1),
            total_calories=round(total_calories, 1),
            calories_target=round(calories_target, 1),
            calories_percentage=round(calories_percentage, 1)
        )


    @classmethod
    def log_meal(
        cls, 
        db: Session, 
        user_id: int, 
        meal_data: MealLogCreate
    ) -> MealLogResponse:
        """
        Log a meal and update daily nutrition
        
        Args:
            db: Database session
            user_id: User ID
            meal_data: Meal information
            
        Returns:
            MealLogResponse with calculated nutrition
        """
        # Calculate nutritional values for consumed quantity
        quantity_ratio = meal_data.quantity_grams / 100.0
        
        total_calories = meal_data.calories_per_100g * quantity_ratio
        total_carbs = meal_data.carbs_per_100g * quantity_ratio
        total_protein = meal_data.protein_per_100g * quantity_ratio
        total_fat = meal_data.fat_per_100g * quantity_ratio
        
        # Create meal event
        meal_event = Event(
            user_id=user_id,
            event_type="meal",
            title=f"Meal: {meal_data.food_name}",
            description=f"Consumed {meal_data.quantity_grams}g",
            data={
                "food_name": meal_data.food_name,
                "quantity_grams": meal_data.quantity_grams,
                "calories_per_100g": meal_data.calories_per_100g,
                "carbs_per_100g": meal_data.carbs_per_100g,
                "protein_per_100g": meal_data.protein_per_100g,
                "fat_per_100g": meal_data.fat_per_100g,
                "total_calories": total_calories,
                "total_carbs": total_carbs,
                "total_protein": total_protein,
                "total_fat": total_fat
            },
            event_timestamp=datetime.now(timezone.utc)
        )
        
        db.add(meal_event)
        
        # Update daily nutrition
        nutrition = cls.get_or_create_daily_nutrition(db, user_id)
        nutrition.carbs_consumed += total_carbs
        nutrition.protein_consumed += total_protein
        nutrition.fat_consumed += total_fat
        nutrition.total_calories += total_calories
        
        db.commit()
        db.refresh(meal_event)
        
        return MealLogResponse(
            id=meal_event.id,
            user_id=user_id,
            food_name=meal_data.food_name,
            quantity_grams=meal_data.quantity_grams,
            calories_per_100g=meal_data.calories_per_100g,
            carbs_per_100g=meal_data.carbs_per_100g,
            protein_per_100g=meal_data.protein_per_100g,
            fat_per_100g=meal_data.fat_per_100g,
            total_calories=round(total_calories, 1),
            total_carbs=round(total_carbs, 1),
            total_protein=round(total_protein, 1),
            total_fat=round(total_fat, 1),
            event_timestamp=meal_event.event_timestamp
        )


    @classmethod  
    def get_ai_nutrition_suggestion(
        cls, 
        db: Session, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        Generate AI-powered nutrition suggestion based on user's progress
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict with suggestion text and metadata
        """
        progress = cls.get_macronutrient_progress(db, user_id)
        
        suggestions = []
        
        # Analyze macronutrient balance
        if progress.carbs_percentage < 80:
            suggestions.append("Agrega carbohidratos complejos como avena o quinoa para aumentar tu energía")
        elif progress.carbs_percentage > 120:
            suggestions.append("Considera reducir los carbohidratos refinados y enfocarte en proteína")
            
        if progress.protein_percentage < 80:
            suggestions.append("Incluye fuentes magras de proteína como pollo o pescado")
        elif progress.protein_percentage > 120:
            suggestions.append("¡Excelente ingesta de proteína! Equilibra con grasas saludables")
            
        if progress.fat_percentage < 70:
            suggestions.append("Agrega grasas saludables como aguacate o frutos secos")
        elif progress.fat_percentage > 130:
            suggestions.append("Modera la ingesta de grasas y enfócate en carbohidratos complejos")
        
        # Overall calorie analysis
        if progress.calories_percentage < 85:
            suggestions.append("Intenta comer comidas pequeñas y frecuentes para alcanzar tus objetivos calóricos")
        elif progress.calories_percentage > 110:
            suggestions.append("Considera un entrenamiento HIIT para impulsar la quema de calorías")
        
        # Default suggestion if everything is balanced
        if not suggestions:
            suggestions = [
                "¡Excelente balance! Intenta hacer un entrenamiento HIIT hoy para impulsar tu quema de calorías y mejorar tu forma cardiovascular.",
                "¡Tu nutrición va bien! Considera agregar algo de estiramiento ligero después de las comidas.",
                "¡Balance de macronutrientes perfecto! Mantente hidratado y sigue con el excelente trabajo."
            ]
        
        # Select first suggestion (could be randomized)
        suggestion_text = suggestions[0]
        
        return {
            "suggestion": suggestion_text,
            "type": "nutrition",
            "priority": "medium",
            "created_at": datetime.now(timezone.utc).isoformat()
        }