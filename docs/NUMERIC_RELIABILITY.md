# NUMERIC_RELIABILITY.md — Invariantes y reglas numéricas

> **La fiabilidad numérica es la propuesta de valor de NovaFitness.** Los números que la app muestra al usuario tienen que cuadrar entre sí, ser reproducibles, y trazables. Si en algún cambio una de las invariantes de este archivo se rompe, eso es un bug — no una decisión de implementación.

---

## Invariantes obligatorios

### I-1: Suma de macros igual a target calories

```
4 · protein_target_g + 4 · carbs_target_g + 9 · fat_target_g  =  target_calories
```

**Sin tolerancia.** El cálculo de targets debe redondear macros con **rebalanceo** (Card #9 del Backlog implementa esto):
1. Calcular `protein_target_g` y `fat_target_g` redondeados (ver §Reglas de redondeo)
2. Calcular `carbs_target_g = (target_calories - 4·protein_target_g - 9·fat_target_g) / 4`, redondeado
3. **Carbs absorbe la diferencia residual** — confirmado 2026-04-26.

**Aplicado en:** [`app/services/biometric_service.py:calculate_objective_targets`](../app/services/biometric_service.py).

### I-2: Suma de macros consumidos coincide con calorías consumidas (con fibra)

```
4 · protein_consumed + 4 · (carbs_consumed - fiber_consumed) + 2 · fiber_consumed + 9 · fat_consumed
  ≈  calories_consumed  ± 1 kcal
```

**Por qué con fibra explícita:** USDA mide las calorías biológicamente — la fibra contribuye ~2 kcal/g (no 4) porque el cuerpo no la metaboliza completamente. El cálculo Atwater simple `4·prot + 4·carbs + 9·fat` sobre-cuenta calorías en alimentos con fibra (~10% en banana, más en legumbres). Para garantizar consistencia entre el campo directo de USDA y la suma de macros, **trackeamos fibra como cuarto macro** (Card #38, ver `DECISIONS.md` ADR #8).

**Aplicado en:** logging de comidas — `NutritionService.log_meal` y `food_service.parse_and_log_meals`.

> ⚠ **Pendiente Card #38** — el modelo `FoodEntry` y el schema `USDAFoodResult` aún no extraen el campo `fiber_per_100g`. Hasta que la card cierre, el invariante I-2 puede fallar para alimentos con fibra alta.

### I-3: avg_kcal_per_training_session refleja peso del usuario

```
avg_kcal_per_training_session  =  MET × user.weight_kg × duration_hours
```

con MET = 5.5 (medium intensity para `fuerza_general`). Para una rutina con N sesiones, es el promedio sobre N.

**Aplicado en:** [`RoutineService._compute_avg_kcal_per_training_session`](../app/services/routine_service.py).

**Auto-recompute:** Card #40 — cuando `update_user_biometrics` cambia `weight_kg` en más de 2 kg, se dispara recálculo del `avg_kcal_per_training_session` de la rutina activa.

### I-4: kcal de log de sesión coincide con avg_kcal_per_training_session (cuando el usuario sigue el plan)

```
WorkoutSession.total_kcal_est  ≈  avg_kcal_per_training_session
```

cuando el usuario logea una sesión de la rutina sin extras y sin skipped exercises, con el mismo peso que tenía cuando se generó la rutina. Garantiza que el estimado de la dieta y el log real estén alineados.

Implementado vía: ambos comparten `_calc_routine_kcal` con la misma activity (`fuerza_general`) y misma intensidad (`medium`).

### I-5: Targets visibles reflejan el último update de objective/biometrics

```
GET /nutrition/macros          devuelve targets coherentes con
GET /users/me                  en cualquier momento.
```

Hoy NO se cumple — `DailyNutrition.targets` se snapshotean al crear el record del día. Card #8 del Backlog lo arregla.

---

## Reglas de redondeo

**Regla universal:** todo output numérico **visible al usuario** se redondea a **entero** (sin decimales). Confirmado 2026-04-26 (TBD-C resuelto).

| Cantidad | Redondeo |
|---|---|
| `target_calories` | entero (kcal) |
| `protein_target_g`, `carbs_target_g`, `fat_target_g`, `fiber_target_g` | entero (gramos) |
| Macros consumidos | entero (gramos) |
| `total_calories` por comida / por día | entero (kcal) |
| `avg_kcal_per_training_session` | entero (kcal) |
| `kcal_min/max/est` por bloque de workout | entero (kcal) |
| `bmr_bpm`, `daily_caloric_expenditure` | entero (kcal) |

**Excepción**: cantidades **no visibles al usuario** (factores intermedios) pueden mantener decimales:
- MET window (`met_used_min`, `met_used_max`): 3 decimales (cálculos físicos internos)
- `correction_factor` (per-user MET calibration): 3 decimales

> ⚠ **Pendiente Card #39** — auditar el código y reemplazar `round(x, 1)` y `round(x, 2)` por `int(round(x))` en outputs visibles.

---

## Fuentes de verdad

### Macros consumidos (qué comió hoy)

```
DailyNutrition  =  fuente única de verdad
UserDiet.completed_meals  =  flags de qué comidas del plan se completaron hoy (sin números)
```

**Estructura nueva de `completed_meals`** (reemplaza al deprecated `daily_consumed`):
```json
{
  "2026-04-26": [0, 2, 4]    // índices de meals del plan que se completaron hoy
}
```

**No tiene macros**. Los números vienen siempre de `DailyNutrition`. Si el frontend necesita "macros del plan completado" para mostrar progreso ("4/5 comidas, te falta el snack"), los **calcula en runtime** desde:
- el plan (`diet_data.days[<type>].meals[i]`)
- los overrides (`daily_overrides[today][i]` si aplica)
- los flags (`completed_meals[today]`)

> ⚠ **Pendiente Card #7** — implementar la migración de `daily_consumed` → `completed_meals`.

### Macros target (qué debería comer hoy)

```
User.{target_calories, protein_target_g, carbs_target_g, fat_target_g, fiber_target_g}  =  source of truth
DailyNutrition.{calories_target, ...}  =  espejo (debería actualizarse en cambios)
```

Card #8 hace que `DailyNutrition` realmente refleje cambios mid-day.

### Macros nutricionales por alimento

Orden de prioridad cuando un alimento puede resolverse en múltiples fuentes (confirmado 2026-04-26):

```
1. FatSecret (servings size más realista para Argentina/LATAM)
   ↓ fallback si no encuentra
2. USDA FoodData Central (vasta cobertura, base genérica)
   ↓ fallback si no encuentra
3. OpenFoodFacts (con barcode si aplica, branded)
   ↓ fallback si todo falla
4. Cache de FoodEntry o estimación AI (último recurso)
```

Implementado en `FoodService.parse_and_calculate` y `FoodAggregatorService.search_food`.

### Calorías por alimento — campo directo, NO Atwater simple

Cuando una fuente provee `calories_per_100g` Y los macros, **siempre se prioriza el campo directo** (USDA / FatSecret). NO se recalcula desde macros con `4·p + 4·c + 9·f`.

**Razón:** las fuentes usan factores Atwater modificados que descuentan fibra (2 kcal/g en lugar de 4). Recalcular desde macros sin trackear fibra **infla** las calorías ~10% en alimentos con fibra moderada/alta. Es biológicamente incorrecto.

Confirmado 2026-04-26. Ver `DECISIONS.md` ADR #8 (track fiber) para la solución que mantiene I-2 garantizado.

### kcal quemadas en entrenamiento

```
MET tablas de Compendium of Physical Activities
× User.weight_kg actual
× duration_minutes / 60
× WorkoutCorrectionFactor (per-user calibration, default 1.0)
```

No se acepta self-reported kcal (ej: lo que diga un wearable) sin pasar por la fórmula MET.

---

## Reglas de validación de inputs

| Campo | Min | Max | Default |
|---|---|---|---|
| `weight_kg` | 30 | 300 | — |
| `height_cm` | 100 | 250 | — |
| `age` | 13 | 120 | — |
| `aggressiveness_level` | 1 | 3 | 2 |
| `activity_level` | 1.2 | 1.9 | — |
| `target_calories` (custom) | 1000 | 6000 | — |
| `carbs_target_percent`, `protein_target_percent`, `fat_target_percent` | 0 (excl) | 100 (excl) | — |
| Suma de macro percentages | 99.8 | 100.2 | — (validado) |

Inputs fuera de rango deben rechazarse con `422` y mensaje específico (ver `ERROR_HANDLING.md`).

---

## Cosas que NO se permiten

1. **Cálculos numéricos en endpoints/controllers**. La aritmética va en services. Endpoints solo orquestan.
2. **Magic numbers en lógica numérica**. Si necesitás un factor (4, 9, MET), viene de `WorkoutConstants` / `BiometricConstants` o del seed `exercise_activities`.
3. **`float == float` directo** en tests. Usar `pytest.approx`.
4. **Persistir el resultado de un cálculo sin testear que el invariante se cumple**. Cualquier card que toque cálculos numéricos tiene que incluir el test de invariante correspondiente.
5. **Inferir kcal desde Gemini sin pasar por MET tables**. Gemini no es fuente de verdad para números — es fuente de estructura, pero los cálculos van por las fórmulas.
6. **Recalcular calorías desde macros con Atwater simple**. Siempre el campo directo de la fuente. Si hace falta consistencia, agregar fibra al modelo (Card #38).

---

## Pendientes activos relacionados con fiabilidad numérica

| Card | Tema |
|---|---|
| #7 | Reemplazar `daily_consumed` por `completed_meals` (single source of truth = `DailyNutrition`) |
| #8 | `DailyNutrition.targets` debe reflejar cambios de objective en tiempo real |
| #9 | Garantizar invariante I-1 con rebalanceo post-redondeo (carbs absorbe diferencia) |
| #10 | ✅ avg_kcal_per_training_session server-side (cerrada) |
| #38 | Trackear fibra como cuarto macro (modelo + USDA + DailyNutrition + User target) |
| #39 | Redondear todos los outputs numéricos a enteros |
| #40 | Auto-recompute `avg_kcal_per_training_session` cuando `update_user_biometrics` cambia peso >2 kg |
