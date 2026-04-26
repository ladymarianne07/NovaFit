# NUMERIC_RELIABILITY.md — Invariantes y reglas numéricas

> **La fiabilidad numérica es la propuesta de valor de NovaFitness.** Los números que la app muestra al usuario tienen que cuadrar entre sí, ser reproducibles, y trazables. Si en algún cambio una de las invariantes de este archivo se rompe, eso es un bug — no una decisión de implementación.

---

## Invariantes obligatorios

Estos son los invariantes que **todo cambio de cálculo numérico tiene que respetar**. Los tests deben verificarlos.

### I-1: Suma de macros igual a target calories (post-redondeo)

```
4 · protein_target_g + 4 · carbs_target_g + 9 · fat_target_g  ≈  target_calories  ± 1 kcal
```

Tolerancia: ±1 kcal por errores de redondeo natural (Card #9 del Backlog implementa el rebalanceo para garantizar esto).

**Aplicado en:** [`app/services/biometric_service.py:calculate_objective_targets`](../app/services/biometric_service.py).

### I-2: Suma de macros consumidos coincide con calorías consumidas

```
4 · protein_consumed + 4 · carbs_consumed + 9 · fat_consumed  ≈  calories_consumed  ± ε
```

Donde `ε` depende de la precisión de las fuentes upstream (USDA suele tener inconsistencias menores entre macro y total kcal; FatSecret igual). Tolerancia razonable: hasta 5% del total.

**Aplicado en:** logging de comidas — `NutritionService.log_meal` y `food_service.parse_and_log_meals` deberían respetarlo.

### I-3: avg_kcal_per_training_session refleja peso del usuario

```
avg_kcal_per_training_session  =  MET × user.weight_kg × duration_hours
```

con MET = 5.5 (medium intensity para `fuerza_general`). Para una rutina con N sesiones, es el promedio sobre N.

Si el usuario cambia de peso, el avg correspondiente debería poder recalcularse. Hoy no se recalcula automáticamente al `PUT /users/me/biometrics` — el siguiente edit de rutina lo refresca, OR un endpoint dedicado de recompute. Card pendiente para auto-recompute si el peso cambia significativamente (>2 kg).

**Aplicado en:** [`RoutineService._compute_avg_kcal_per_training_session`](../app/services/routine_service.py).

### I-4: kcal de log de sesión coincide con avg_kcal_per_training_session (cuando el usuario sigue el plan)

```
WorkoutSession.total_kcal_est  ≈  avg_kcal_per_training_session
```

cuando el usuario logea una sesión de la rutina sin extras y sin skipped exercises, con el mismo peso que tenía cuando se generó la rutina. Garantiza que el estimado de la dieta y el log real estén "alineados".

Implementado vía: ambos comparten `_calc_routine_kcal` con la misma activity (`fuerza_general`) y misma intensidad (`medium`).

### I-5: Targets visibles reflejan el último update de objective/biometrics

```
GET /nutrition/macros          devuelve targets coherentes con
GET /users/me                  en cualquier momento.
```

Hoy esto NO se cumple — `DailyNutrition.targets` se snapshotean al crear el record del día. **Card #8 del Backlog lo arregla.** Hasta entonces, este invariante no se garantiza.

---

## Reglas de redondeo

> ⚠ **TBD para la usuaria — definir al revisar.** Las reglas de abajo son las que el código aplica HOY (extracto de la realidad), pero algunas pueden ser inconsistentes y conviene formalizar.

### Reglas vigentes (heredadas del código actual)

| Cantidad | Redondeo actual | Justificación |
|---|---|---|
| `target_calories` | entero (kcal) | `round(tdee × (1 + delta))` en `calculate_objective_targets` |
| `bmr_bpm` | 1 decimal | `round(bmr, 1)` en `calculate_bmr` |
| `daily_caloric_expenditure` | 1 decimal | igual |
| `protein_target_g`, `fat_target_g`, `carbs_target_g` | entero (gramos) | `round(weight_kg × factor)` independientemente |
| Macros consumidos por food parsing | 2 decimales (gramos) | `round(per_100g × grams / 100, 2)` |
| Total kcal por food parsing | 2 decimales | igual |
| MET window (corrected) | 3 decimales | `round(corrected_met_min, 3)` en `WorkoutService.calculate_block_metrics` |
| kcal_min/max/est en `WorkoutBlockMetrics` | 2 decimales | `round(kcal_*, 2)` |
| `avg_kcal_per_training_session` | 2 decimales | `round(total_kcal / counted, 2)` |

### TBDs que la usuaria tiene que decidir

> ⚠ **TBD-1**: ¿Querés que `protein_target_g` muestre enteros (como hoy) o medio gramo (`round(x * 2) / 2`)? El "0.5 g" es trivial nutricionalmente pero a veces da mejor sensación de precisión al usuario.

> ⚠ **TBD-2**: Cuando el invariante I-1 falla por redondeo independiente (ej: `4·126 + 4·211 + 9·56 = 1852` vs `target = 1850`), ¿cuál macro absorbe la diferencia? Sugerencia: carbs (es el "buffer" calórico). Card #9 del Backlog implementa esto.

> ⚠ **TBD-3**: Para el campo `total_calories` en una comida cuando los macros vienen de USDA y la suma de `4·p + 4·c + 9·f` ≠ `calories_per_100g × grams / 100` (USDA inconsistency), ¿qué se prioriza? Hoy se prioriza `calories_per_100g` (campo directo). Alternativa: recalcular siempre desde macros para forzar consistencia.

---

## Fuentes de verdad

### Macros consumidos (qué comió hoy)

```
DailyNutrition  =  fuente única de verdad   (después de Card #7)
UserDiet.daily_consumed  =  caché/index de qué comidas del plan se completaron (sin macros)
```

> ⚠ **TBD-4**: Hoy ambos acumulan macros y pueden divergir (ver Card #7 del Backlog). La decisión que sugerí en el card es: `DailyNutrition` queda como single source of truth para macros; `UserDiet.daily_consumed` queda como **flag de completion** (`{date: {meal_index: True}}`) sin números, para responder "¿qué comidas del plan ya cumplió?". Confirmar esto antes de implementar Card #7.

### Macros target (qué debería comer hoy)

```
User.{target_calories, protein_target_g, carbs_target_g, fat_target_g}  =  source of truth
DailyNutrition.{calories_target, ...}  =  espejo (debería actualizarse en cambios)
```

Card #8 hace que `DailyNutrition` realmente refleje cambios mid-day.

### Macros nutricionales por alimento

Orden de prioridad cuando un alimento puede resolverse en múltiples fuentes:

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

> ⚠ **TBD-5**: Confirmar que el orden FatSecret → USDA → OFF es el deseado. El audit del 2026-04-04 indicaba esto pero no estoy 100% seguro de que sea la decisión vigente.

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

---

## Pendientes activos relacionados con fiabilidad numérica

| Card | Tema |
|---|---|
| #7 | Unificar fuente de verdad de macros consumidos (`DailyNutrition` vs `UserDiet.daily_consumed`) |
| #8 | `DailyNutrition.targets` debe reflejar cambios de objective en tiempo real |
| #9 | Garantizar invariante I-1 con rebalanceo post-redondeo |
| #10 | ✅ avg_kcal_per_training_session server-side (cerrada) |

---

## TBDs resumidos

Acá la lista de los TBDs marcados arriba para que los resuelvas en una vuelta:

- **TBD-1**: ¿Enteros o medio gramo en `protein_target_g`?
- **TBD-2**: ¿Qué macro absorbe la diferencia residual de redondeo en I-1? (Sugerencia: carbs)
- **TBD-3**: ¿Recalcular `total_calories` desde macros, o priorizar el campo directo de USDA cuando hay inconsistencia?
- **TBD-4**: Confirmar que `DailyNutrition` queda como source of truth para Card #7
- **TBD-5**: Confirmar orden de prioridad FatSecret → USDA → OFF para resolución de alimentos
