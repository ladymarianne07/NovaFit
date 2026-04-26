# Auditoría de Nomenclatura — NovaFitness Backend
**Fecha:** 2026-04-04 | **Tipo:** Solo lectura

## Resumen Ejecutivo

Se identificaron **15 inconsistencias de nomenclatura** en 5 archivos. Todas son cambios no-breaking. Impacto: ninguno en funcionalidad, alto en mantenibilidad.

---

## Categoría 1: Violaciones de PEP8 / Abreviaciones Inconsistentes

| Nombre Actual | Nombre Sugerido | Archivo | Línea | Issue |
|---------------|-----------------|---------|-------|-------|
| `bmr_bpm` | `bmr` | `app/db/models.py` | 36 | "bpm" (beats per minute) es irrelevante; debería ser simplemente `bmr` (Basal Metabolic Rate) |
| `met_low` | `met_value_low` | `app/db/models.py` | 202 | Inconsistente con otros campos verbosos (`duration_minutes`, `weight_kg`). Debería ser verbose. |
| `met_medium` | `met_value_medium` | `app/db/models.py` | 203 | Idem |
| `met_high` | `met_value_high` | `app/db/models.py` | 204 | Idem |
| `kcal_min` | `calories_min` | `app/db/models.py` | 272, 323 | Prefijo abreviado inconsistente con el naming del resto del proyecto |
| `kcal_max` | `calories_max` | `app/db/models.py` | 273, 324 | Idem |
| `kcal_est` | `calories_estimated` | `app/db/models.py` | 274, 325 | Idem |
| `total_kcal_min` | `total_calories_min` | `app/db/models.py` | 236 | Idem |
| `total_kcal_max` | `total_calories_max` | `app/db/models.py` | 237 | Idem |
| `total_kcal_est` | `total_calories_estimated` | `app/db/models.py` | 238 | Idem |

---

## Categoría 2: Mezcla de Idiomas (Español/Inglés)

| Nombre Actual | Nombre Sugerido | Archivo | Línea | Issue |
|---------------|-----------------|---------|-------|-------|
| `label_es` | `label` | `app/db/models.py` | 200 | Sufijo de idioma inapropiado en schema de base de datos |
| `PERIOD_YEAR = "anio"` | `PERIOD_YEAR = "year"` ó `PERIOD_YEAR_ES = "anio"` | `app/constants.py` | 128 | Nombre en inglés con valor en español. Inconsistente. |
| `PERIOD_WEEK = "semana"` | `PERIOD_WEEK = "week"` ó `PERIOD_WEEK_ES = "semana"` | `app/constants.py` | 126 | Idem |
| `PERIOD_MONTH = "mes"` | `PERIOD_MONTH = "month"` ó `PERIOD_MONTH_ES = "mes"` | `app/constants.py` | 127 | Idem |

---

## Categoría 3: Nombres no Descriptivos

| Nombre Actual | Nombre Sugerido | Archivo | Línea | Issue |
|---------------|-----------------|---------|-------|-------|
| `_404` | `ERROR_NOT_FOUND_RESPONSES` | `app/api/diet.py` | 30 | Nombre de variable poco descriptivo. El lector no puede entender la intención |
| `_422` | `ERROR_UNPROCESSABLE_RESPONSES` | `app/api/diet.py` | 31 | Idem |
| `_500` | `ERROR_SERVER_RESPONSES` | `app/api/diet.py` | 32 | Idem |
| `_404` | `ERROR_NOT_FOUND_RESPONSES` | `app/api/routine.py` | 34 | Idem (duplicado del issue en diet.py) |
| `_422` | `ERROR_UNPROCESSABLE_RESPONSES` | `app/api/routine.py` | 36 | Idem |
| `_500` | `ERROR_SERVER_RESPONSES` | `app/api/routine.py` | 38 | Idem |
| `result` | `current_meal` / `meal_log_response` / `alternative_meal` | `app/api/diet.py` | 174, 205, 234 | Variable genérica. Debería reflejar el tipo de dato que contiene |
| `user_data` | (usar `current_user` directamente) | `app/api/routine.py` | 101, 210, 242 | Variable intermedia redundante: `user_data = current_user` no aporta claridad |
| `payload` | `generate_request` / `edit_request` / etc. | `app/api/diet.py`, `routine.py` | 46, 104, 95, 139 | Nombre genérico para parámetro. Debería reflejar el schema específico |

---

## Categoría 4: Discrepancias Endpoint–Función Handler

| Endpoint | Función Handler | Archivo | Línea | Issue |
|----------|----------------|---------|-------|-------|
| `POST /meals/alternative` | `get_meal_alternative()` | `app/api/diet.py` | 228 | **Engañoso:** "get" implica recuperación, pero es un POST que genera. Debería ser `generate_meal_alternative()` |

---

## Categoría 5: Inconsistencias de Patrón de Retrieval

| Patrón 1 | Patrón 2 | Archivos |
|----------|----------|---------|
| `get_active_diet()`, `get_active_routine()` | `get_current_meal()` | `app/api/diet.py`, `app/api/routine.py` |

`active` implica basado en estado; `current` implica temporal. Se mezclan sin distinción semántica. Estandarizar a uno de los dos.

---

## Recomendaciones por Prioridad

### Alta (claridad de código)
1. Renombrar variables `_404`, `_422`, `_500` a nombres descriptivos en `diet.py` y `routine.py`
2. Renombrar `get_meal_alternative()` a `generate_meal_alternative()` para reflejar la acción POST

### Media (consistencia y mantenibilidad)
3. Estandarizar abreviaciones de campos en modelos: `kcal_*` → `calories_*`, `met_*` → `met_value_*`
4. Resolver mezcla de idiomas en constants: elegir inglés o sufijo `_ES`
5. Eliminar variable redundante `user_data` en `routine.py`

### Baja (mejoras menores)
6. Estandarizar naming de retrieval: `active_*` vs `current_*`
7. Usar nombres específicos en lugar de `result` y `payload`
8. Remover sufijo de idioma de campos (`label_es` → `label`)

---

## Notas de Implementación

- Todos los cambios son **no-breaking** en la lógica
- Los nombres de columnas de base de datos **no deben renombrarse** sin migración
- Los renombres de funciones públicas en servicios requieren actualizar los callers en `app/api/`
- Se recomienda ejecutar el suite de tests completo tras los renombres
