# DOMAIN_GLOSSARY.md — Glosario de dominio del backend

> Términos del backend que aparecen en código, schemas y modelos. Si te encontrás escribiendo `daily_consumed`, `intake_data`, `aggressiveness_level`, etc., y no estás 100% seguro qué significan, leelo acá antes de inventar.

---

## A

### `aggressiveness_level`
- **Tipo:** `int` ∈ `{1, 2, 3}` (default `2`).
- **Dónde vive:** columna en `users` (`User.aggressiveness_level`).
- **Para qué:** ajusta el delta calórico aplicado al TDEE para alcanzar el objetivo.
  - `1` = conservador (delta chico, ~10%)
  - `2` = moderado (default, ~15%)
  - `3` = agresivo (delta grande, ~20%)
- **Aplicado en:** `BiometricService.get_calorie_delta_by_objective(objective, aggressiveness_level)`.
- **Validación:** `1 ≤ aggressiveness_level ≤ 3` en `ObjectiveUpdate` schema.

### `activity_level`
- **Tipo:** `float` (factor TDEE), enum semántico en `ActivityLevel` schema.
- **Valores típicos:** `1.2` sedentario · `1.375` ligero · `1.55` moderado · `1.725` activo · `1.9` muy activo.
- **Para qué:** multiplicador sobre BMR para obtener TDEE (Total Daily Energy Expenditure).
- **Fórmula:** `daily_caloric_expenditure = bmr_bpm × activity_level`.

---

## B

### `bmr_bpm` (Basal Metabolic Rate)
- **Tipo:** `float` (kcal/día).
- **Dónde vive:** `User.bmr_bpm` columna.
- **Cómo se calcula:** Mifflin-St Jeor, vía `BiometricService.calculate_bmr(weight_kg, height_cm, age, gender)`.
- **El sufijo `_bpm` es legacy** (originalmente "beats per minute", confusión histórica). Card de cleanup pendiente para renombrar a `bmr_kcal_day`.

---

## C

### `current_meal_index` y `current_meal_date`
- **Dónde vive:** columnas en `user_diets` (`UserDiet.current_meal_index`, `UserDiet.current_meal_date`).
- **Para qué:** trackean qué comida del plan le toca al usuario "ahora".
  - `current_meal_index` = índice (0-based) en `diet_data.days[<day_type>].meals`.
  - `current_meal_date` = fecha del último `complete` o `skip` (para detectar rollover de día).
- **Rollover:** cuando se detecta nuevo día, `current_meal_index` vuelve a 0.

### `current_session_index`
- **Dónde vive:** `user_routines.current_session_index` (columna).
- **Para qué:** índice (0-based) de la próxima sesión a hacer del array `routine_data.sessions`.
- **Avance:** sube +1 con `RoutineService.advance_session(action="skip")` o tras un `log_session`.
- **Sin wraparound:** si llega al final, queda en `len(sessions) - 1` (no vuelve a 0).

---

## D

### `daily_caloric_expenditure` (TDEE)
- **Tipo:** `float` (kcal/día).
- **Dónde vive:** `User.daily_caloric_expenditure`.
- **Cómo se calcula:** `bmr_bpm × activity_level`.
- **Es la "torta total"** de calorías que el usuario quema en un día (descanso + actividad). El `target_calories` se deriva de esto + `objective` + `aggressiveness_level`.

### `daily_consumed` (en UserDiet)
- **Tipo:** `dict[str, dict]` JSON column, ej: `{"2026-04-26": {"calories": 1450, "protein_g": 100, "carbs_g": 180, "fat_g": 40}}`.
- **Dónde vive:** `UserDiet.daily_consumed`.
- **Para qué:** acumulador de macros por fecha, escrito por `DietService.log_meal`.
- ⚠ **Source of truth dual conocida**: `DailyNutrition` table también acumula. Ver `NUMERIC_RELIABILITY.md` y Card #7 del Backlog.

### `daily_overrides`
- **Tipo:** `dict[str, dict[str, dict]]` JSON column.
  - Estructura: `{"<YYYY-MM-DD>": {"<meal_index>": <DietMeal>}}`
  - Ej: `{"2026-04-26": {"2": {"name": "Salmón al horno", "foods": [...], ...}}}`
- **Dónde vive:** `UserDiet.daily_overrides`.
- **Para qué:** sustituir comidas específicas del plan **solo para un día puntual** sin tocar el plan base.
- **Generado por:** `DietService.apply_meal_alternative(scope="today")`. El usuario abre el modal de "Cambiar esta comida hoy" y elige una alternativa que Gemini propone.
- **Lifecycle:** persiste hasta que el usuario lo borre explícitamente o se elimine la dieta. NO se autoexpira al día siguiente.

### `DailyNutrition`
- **Tipo:** tabla SQL (`daily_nutrition`).
- **Para qué:** snapshot diario del consumo del usuario. Una fila por usuario+fecha.
- **Columnas clave:** `user_id`, `date`, `calories_consumed`, `protein_consumed`, `carbs_consumed`, `fat_consumed`, `calories_target`, `protein_target`, `carbs_target`, `fat_target`.
- **Escrito por:** `NutritionService.log_meal`, `NutritionService.delete_meal`, `food_service.parse_and_log_meals`.
- ⚠ **Targets se snapshotean al crear el record del día** y no se actualizan con cambios posteriores de objective/biometric — Card #8 del Backlog corrige esto.

### `diet_data`
- **Tipo:** `dict` JSON column.
- **Estructura producida por Gemini:** `{title, days: {training_day: {meals: [...]}, rest_day: {meals: [...]}}, total_calories, total_protein_g, ...}`.
- **Dónde vive:** `UserDiet.diet_data`.

---

## E

### `Event`
- **Tipo:** tabla SQL (`events`), append-only timeline.
- **Para qué:** log inmutable de actividades del usuario (logged meals, weight updates, etc.). **Soft-delete only** — `is_deleted` flag, nunca DROP.
- **Tipos comunes:** `meal`, `weight_update`, `objective_change`, `biometric_change`.

### `event_type` (en `Event`)
- **Valores en uso:** `meal`, `weight_update`, `objective_change`, etc. No hay enum estricto en código todavía — string libre.

---

## F

### `FoodEntry`
- **Tipo:** tabla SQL (`food_entries`).
- **Para qué:** caché global de items parseados (texto + USDA/FatSecret resolved).
- ⚠ **NO tiene `user_id`** — es un caché compartido, no histórico por usuario. Decisión consciente, ver `DECISIONS.md`.

### `FoodPortionCache`
- **Tipo:** tabla SQL (`food_portion_cache`).
- **Para qué:** cache de `(food_name, unit) → grams` para resoluciones tipo "1 cup of rice → 195g".
- **Escrito por:** `PortionResolverService` cuando consulta a USDA/FatSecret/OpenFoodFacts.

---

## I

### `intake_data`
- **Aparece en:** `user_routines.intake_data` y `user_diets.intake_data` (ambos JSON columns).
- **Contenido:** snapshot del **formulario de intake** que el usuario llenó al generar la rutina/dieta. Sirve para regenerar (ej: `generate_from_text` con la misma intake).
- **Routine intake típico:** `{frequency, duration_months, equipment, experience, health_conditions, injuries, ...}`.
- **Diet intake típico:** `{meals_count, dietary_restrictions, food_allergies, training_days, budget_level, cooking_time, ...}`.
- **Card #10 (cerrada)** agregó `avg_kcal_per_training_session` al `routine_data`, NO al `intake_data` — el campo es server-computed, no input del usuario.

---

## M

### MET (Metabolic Equivalent of Task)
- **Unidad:** múltiplo de la tasa metabólica en reposo (1 MET = 1 kcal/kg/h aproximadamente).
- **En código:** valores low/medium/high por actividad en tabla `exercise_activities`.
- **Fórmula:** `kcal = MET × weight_kg × duration_hours`.
- **Default para sesiones de rutina:** `fuerza_general` activity, `medium` intensity → MET window `(5.0, 6.0)` → `met_est = 5.5`. Usado por `RoutineService._calc_routine_kcal` y `_compute_avg_kcal_per_training_session`.

### `met_low` / `met_medium` / `met_high`
- **Tipo:** columnas float en `exercise_activities`.
- **Usadas por:** `WorkoutService._resolve_met_window(activity, intensity_level)`:
  - `low` → `(met_low, met_medium)`
  - `medium` → `(met_medium, met_high)`
  - `high` → `(met_high, met_high)`
- Después `met_est = (met_min + met_max) / 2`. Ver `WorkoutService.calculate_block_metrics`.

---

## N

### `NovaFitnessException`
- Base de toda excepción de dominio del backend. Detalle en [`ERROR_HANDLING.md`](ERROR_HANDLING.md).

---

## O

### `objective` (fitness objective)
- **Tipo:** `str` ∈ `{fat_loss, maintenance, muscle_gain, body_recomp, performance}` (enum `FitnessObjective`).
- **Dónde vive:** `User.objective`.
- **Determina:** delta calórico (vía `aggressiveness_level`) y proteína g/kg (vía `BiometricService.get_protein_factor_by_objective`).

---

## R

### `routine_data`
- **Tipo:** `dict` JSON column en `user_routines`.
- **Estructura producida por Gemini:** `{title, subtitle, health_analysis, phases, schedule, month_data, sessions: [...]}`.
- **Server-augmented:** `avg_kcal_per_training_session` (Card #10) se inyecta al final del workflow de generación/edición.

---

## S

### `source_type` (en `UserRoutine`)
- **Valores:** `"ai_text"` (generada por IA con texto libre del usuario) · `"file"` (subida un archivo PDF/imagen y Gemini lo parseó).
- **Cambia el flujo:** archivos van por `RoutineService.parse_and_save`; texto libre por `BaseAIGenerationService.generate_from_text`.

### `service_error_handler`
- Context manager en [`app/core/exception_handlers.py`](../app/core/exception_handlers.py). Detalle en [`ERROR_HANDLING.md`](ERROR_HANDLING.md).

### `status` (en records con generación AI)
- **Valores:** `"processing"` (Gemini en curso) · `"ready"` (listo para mostrar) · `"error"` (Gemini falló o JSON inválido).
- **Aplicado a:** `UserDiet.status`, `UserRoutine.status`.

---

## T

### `target_calories`
- **Tipo:** `float` (kcal/día), columna en `User.target_calories`.
- **Cómo se calcula:** `daily_caloric_expenditure × (1 + calorie_delta(objective, aggressiveness_level))`. Round a entero.
- **Es lo que el usuario "debería" comer al día**, no lo que ya consumió.

### `training_days`
- **Tipo:** `list[str]` en `intake_data` de `UserDiet`.
- **Valores:** nombres de días, ej: `["Lunes", "Miércoles", "Viernes"]`.
- **Para qué:** Gemini usa esto para elegir si la dieta del día sea de tipo `training_day` (con kcal extras) o `rest_day`. Si el array está vacío, los dos tipos son idénticos.

---

## U

### `User`
- Tabla `users`. Centro del modelo de datos. Casi toda otra tabla tiene FK a `user_id`.
- Tiene tres columnas calculadas separadas que dependen entre sí:
  1. `bmr_bpm` ← f(weight, height, age, gender)
  2. `daily_caloric_expenditure` ← f(bmr_bpm, activity_level)
  3. `target_calories` ← f(daily_caloric_expenditure, objective, aggressiveness_level)
- Cuando se actualiza una biométrica, las 3 se recalculan en cascada vía `BiometricService.update_user_biometrics_with_recalculation` + `UserService.update_user_metrics`.

### `UserDiet`
- Tabla `user_diets`. UNIQUE en `user_id` (un usuario, una dieta activa).
- Contiene `diet_data` (Gemini output), `intake_data` (form input), `daily_consumed` (acumulador), `daily_overrides` (sustituciones puntuales), `current_meal_index`, `current_meal_date`.

### `UserRoutine`
- Tabla `user_routines`. UNIQUE en `user_id`.
- Contiene `routine_data` (Gemini output enriquecido con `avg_kcal_per_training_session`), `intake_data`, `current_session_index`, `health_analysis`, `html_content`.

---

## W

### `WorkoutCorrectionFactor`
- **Tipo:** tabla SQL.
- **Para qué:** factor de corrección **por usuario** sobre los METs estimados, para calibrar las kcal a lo que el usuario realmente quema (basado en feedback de heart rate / wearables / observación).
- **Scopes:** `global` (aplica a todo), `category` (cardio/fuerza/etc.), `activity_key` (uno solo).
- **Resolución:** `WorkoutService._resolve_correction_factor` toma el más específico vigente.

### `WorkoutSession`
- Tabla `workout_sessions`. Una sesión real ejecutada por el usuario (no una sesión planificada de la rutina).
- Tiene `WorkoutSessionBlock` (1:N) con cada ejercicio + duración + intensidad.
- Generada por: `RoutineService.log_session` (cuando completa una sesión de rutina) o `WorkoutService.create_session` (entreno libre tipo "fui a correr").

---

## Términos NO usados

Algunos términos podrían parecer del dominio pero no lo son:

- **"plan"** — no es un término oficial; usar `routine` o `diet` según corresponda.
- **"ejercicio realizado"** — usar `WorkoutSession` o `WorkoutSessionBlock`.
- **"meta"** — usar `target_calories`, `protein_target_g`, `objective`, etc. según el contexto.
