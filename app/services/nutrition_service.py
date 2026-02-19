"""
Nutrition Service - Business logic for macronutrient tracking and calculations

This service handles:
- Daily macronutrient target calculations  
- Meal logging and nutrition tracking
- Progress calculations for macros
- AI-powered nutrition suggestions
"""
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Optional, Dict, Any, Iterable, cast
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.models import User, DailyNutrition, Event
from ..config import settings
from ..schemas.nutrition import (
    MacronutrientResponse,
    MacronutrientTargets,
    DailyNutritionCreate,
    DailyNutritionResponse,
    MealLogCreate,
    MealLogResponse,
    MealGroupResponse,
    MealItemResponse,
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
    def _get_app_timezone(cls):
        """Return configured app timezone; fallback to UTC if invalid."""
        try:
            return ZoneInfo(settings.APP_TIMEZONE)
        except ZoneInfoNotFoundError:
            return timezone.utc

    @classmethod
    def _resolve_tracking_date(cls, target_date: Optional[date] = None) -> date:
        """Resolve tracking date using configured app timezone."""
        if target_date is not None:
            return target_date

        app_tz = cls._get_app_timezone()
        return datetime.now(app_tz).date()

    @classmethod
    def _get_utc_day_bounds(cls, tracking_date: date) -> tuple[datetime, datetime]:
        """Compute UTC [start, end) range for a local day in app timezone."""
        app_tz = cls._get_app_timezone()
        local_start = datetime.combine(tracking_date, datetime.min.time()).replace(tzinfo=app_tz)
        local_end = local_start + timedelta(days=1)
        return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


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
        tracking_date = cls._resolve_tracking_date(target_date)

        # Convert local-day boundaries to UTC for consistent storage/querying.
        start_date, end_date = cls._get_utc_day_bounds(tracking_date)
        
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
        meal_data: MealLogCreate,
        auto_commit: bool = True,
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
        meal_type = (meal_data.meal_type or "meal").strip().lower()
        meal_group_id = meal_data.meal_group_id or uuid4().hex
        meal_label = meal_data.meal_label or meal_type.capitalize()
        
        total_calories = meal_data.calories_per_100g * quantity_ratio
        total_carbs = meal_data.carbs_per_100g * quantity_ratio
        total_protein = meal_data.protein_per_100g * quantity_ratio
        total_fat = meal_data.fat_per_100g * quantity_ratio
        
        # Create meal event
        meal_event = Event(
            user_id=user_id,
            event_type="meal",
            title=f"{meal_type.capitalize()}: {meal_data.food_name}",
            description=f"Consumed {meal_data.quantity_grams}g",
            data={
                "meal_type": meal_type,
                "meal_group_id": meal_group_id,
                "meal_label": meal_label,
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
        
        # Update daily nutrition for the local day corresponding to this event timestamp.
        app_tz = cls._get_app_timezone()
        tracking_date = meal_event.event_timestamp.astimezone(app_tz).date()
        nutrition = cls.get_or_create_daily_nutrition(db, user_id, tracking_date)
        nutrition.carbs_consumed += total_carbs
        nutrition.protein_consumed += total_protein
        nutrition.fat_consumed += total_fat
        nutrition.total_calories += total_calories
        
        if auto_commit:
            db.commit()
            db.refresh(meal_event)
        else:
            db.flush()
        
        return MealLogResponse(
            meal_type=meal_type,
            meal_group_id=meal_group_id,
            meal_label=meal_label,
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
    def get_daily_meals(
        cls,
        db: Session,
        user_id: int,
        target_date: Optional[date] = None,
    ) -> list[MealGroupResponse]:
        """Return grouped meal events for a specific local day."""
        tracking_date = cls._resolve_tracking_date(target_date)
        start_date, end_date = cls._get_utc_day_bounds(tracking_date)

        events = (
            db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.event_type == "meal",
                Event.is_deleted == False,  # noqa: E712
                Event.event_timestamp >= start_date,
                Event.event_timestamp < end_date,
            )
            .order_by(Event.event_timestamp.desc())
            .all()
        )

        grouped: dict[str, dict[str, Any]] = {}

        for event in events:
            data = cast(dict[str, Any], event.data) if isinstance(event.data, dict) else {}
            group_id = str(data.get("meal_group_id") or event.id)
            meal_type = str(data.get("meal_type") or "meal")
            meal_label = str(data.get("meal_label") or meal_type.capitalize())

            entry = grouped.get(group_id)
            if entry is None:
                entry = {
                    "id": group_id,
                    "meal_type": meal_type,
                    "meal_label": meal_label,
                    "event_timestamp": event.event_timestamp,
                    "items": [],
                    "total_quantity_grams": 0.0,
                    "total_calories": 0.0,
                    "total_carbs": 0.0,
                    "total_protein": 0.0,
                    "total_fat": 0.0,
                }
                grouped[group_id] = entry

            entry["event_timestamp"] = min(entry["event_timestamp"], event.event_timestamp)

            item = cls._event_to_meal_item(event)
            entry["items"].append(item)
            entry["total_quantity_grams"] += item.quantity_grams
            entry["total_calories"] += item.total_calories
            entry["total_carbs"] += item.total_carbs
            entry["total_protein"] += item.total_protein
            entry["total_fat"] += item.total_fat

        groups = [
            MealGroupResponse(
                id=group_data["id"],
                meal_type=group_data["meal_type"],
                meal_label=group_data["meal_label"],
                event_timestamp=group_data["event_timestamp"],
                items=group_data["items"],
                total_quantity_grams=round(group_data["total_quantity_grams"], 2),
                total_calories=round(group_data["total_calories"], 2),
                total_carbs=round(group_data["total_carbs"], 2),
                total_protein=round(group_data["total_protein"], 2),
                total_fat=round(group_data["total_fat"], 2),
            )
            for group_data in grouped.values()
        ]

        return sorted(groups, key=lambda group: group.event_timestamp, reverse=True)


    @classmethod
    def delete_meal(cls, db: Session, user_id: int, meal_group_id: str) -> bool:
        """Soft delete a grouped meal event and roll back its nutrition impact."""
        events_query = (
            db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.event_type == "meal",
                Event.is_deleted == False,  # noqa: E712
            )
        )

        events = [
            event
            for event in events_query
            if isinstance(event.data, dict)
            and str(event.data.get("meal_group_id")) == meal_group_id
        ]

        if not events and meal_group_id.isdigit():
            event = events_query.filter(Event.id == int(meal_group_id)).first()
            if event is not None:
                events = [event]

        if not events:
            return False

        app_tz = cls._get_app_timezone()
        tracking_date = events[0].event_timestamp.astimezone(app_tz).date()
        nutrition = cls.get_or_create_daily_nutrition(db, user_id, tracking_date)

        total_calories = 0.0
        total_carbs = 0.0
        total_protein = 0.0
        total_fat = 0.0

        for event in events:
            data = cast(dict[str, Any], event.data) if isinstance(event.data, dict) else {}
            total_calories += cls._safe_float(data.get("total_calories"))
            total_carbs += cls._safe_float(data.get("total_carbs"))
            total_protein += cls._safe_float(data.get("total_protein"))
            total_fat += cls._safe_float(data.get("total_fat"))
            setattr(event, "is_deleted", True)

        carbs_current = cls._safe_float(nutrition.carbs_consumed)
        protein_current = cls._safe_float(nutrition.protein_consumed)
        fat_current = cls._safe_float(nutrition.fat_consumed)
        calories_current = cls._safe_float(nutrition.total_calories)

        setattr(nutrition, "carbs_consumed", max(0.0, carbs_current - total_carbs))
        setattr(nutrition, "protein_consumed", max(0.0, protein_current - total_protein))
        setattr(nutrition, "fat_consumed", max(0.0, fat_current - total_fat))
        setattr(nutrition, "total_calories", max(0.0, calories_current - total_calories))

        db.commit()
        return True


    @classmethod
    def _event_to_meal_item(cls, event: Event) -> MealItemResponse:
        data = cast(dict[str, Any], event.data) if isinstance(event.data, dict) else {}
        food_name = str(data.get("food_name") or event.title or "meal")
        quantity_grams = cls._safe_float(data.get("quantity_grams"))
        calories_per_100g = cls._safe_float(data.get("calories_per_100g"))
        carbs_per_100g = cls._safe_float(data.get("carbs_per_100g"))
        protein_per_100g = cls._safe_float(data.get("protein_per_100g"))
        fat_per_100g = cls._safe_float(data.get("fat_per_100g"))
        total_calories = cls._safe_float(data.get("total_calories"))
        total_carbs = cls._safe_float(data.get("total_carbs"))
        total_protein = cls._safe_float(data.get("total_protein"))
        total_fat = cls._safe_float(data.get("total_fat"))

        return MealItemResponse(
            food_name=food_name,
            quantity_grams=quantity_grams,
            calories_per_100g=calories_per_100g,
            carbs_per_100g=carbs_per_100g,
            protein_per_100g=protein_per_100g,
            fat_per_100g=fat_per_100g,
            total_calories=round(total_calories, 1),
            total_carbs=round(total_carbs, 1),
            total_protein=round(total_protein, 1),
            total_fat=round(total_fat, 1),
        )


    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


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
        
        suggestions: list[str] = []
        
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