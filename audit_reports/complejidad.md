# Auditoría de Complejidad de Funciones — NovaFitness Backend
**Fecha:** 2026-04-04 | **Tipo:** Solo lectura

## Resumen Ejecutivo

Se identificaron **9 funciones candidatas a dividir**. Las dos más críticas son los métodos `_generate_html()` en ambos servicios (169 y 279 líneas respectivamente), que mezclan HTML, CSS y JavaScript con lógica de negocio.

---

## 1. `_generate_html()` en `routine_service.py` — CRÍTICO

**Archivo:** `app/services/routine_service.py`  
**Líneas:** 729–1007 (**279 líneas**)

**Qué hace actualmente:**
1. Extracción y normalización de datos (40 líneas)
2. Generación de month_data fallback para rutinas legacy
3. Serialización JSON para inyección en JavaScript
4. Definición de temas y CSS (95 líneas de CSS inline)
5. Construcción de estructura HTML (50 líneas)
6. JavaScript para theme switching y month tabs (70 líneas)
7. Llamadas a 4 helpers que construyen sub-secciones

**Cómo dividirla:**

| Función Sugerida | Responsabilidad | Líneas Est. |
|-----------------|-----------------|-------------|
| `_validate_and_normalize_routine(data)` | Extrae y valida campos con defaults | 30 |
| `_generate_month_data_for_legacy_routine(sessions)` | Genera month_data para rutinas sin él | 15 |
| `_prepare_routine_json_payload(month_data, sessions)` | Serialización JSON para JS | 10 |
| `_build_routine_styling()` | CSS y variables de tema únicamente | 100 |
| `_build_routine_theme_switcher_js()` | JavaScript para tema | 30 |
| `_build_routine_month_tabs_js()` | JavaScript para tabs de meses | 30 |
| `_assemble_routine_document(parts)` | Concatenación final | 15 |
| `_generate_html()` (refactorizado) | Orquestador únicamente | 25 |

---

## 2. `_generate_diet_html()` en `diet_service.py` — CRÍTICO

**Archivo:** `app/services/diet_service.py`  
**Líneas:** 287–455 (**169 líneas**)

**Qué hace actualmente:**
1. Extracción y validación de datos del dict diet_data
2. Definición de función interna para renderizar comidas con HTML
3. CSS y variables de tema (95 líneas inline)
4. Construcción de estructura HTML
5. Script de theme switching

**Cómo dividirla:**

| Función Sugerida | Responsabilidad | Líneas Est. |
|-----------------|-----------------|-------------|
| `_build_diet_stylesheet(themes)` | Bloque `<style>` completo | 100 |
| `_render_meal_section(day_type, day_data)` | Renderizado de un día de comidas | 30 |
| `_build_diet_header_html(title, description, objective)` | Sección `<header>` | 15 |
| `_build_diet_recommendations_html(health_notes, supplements, summary)` | Sección de notas | 15 |
| `_build_theme_switcher_js(available_themes)` | Bloque `<script>` | 15 |
| `_generate_diet_html()` (refactorizado) | Composición final | 20 |

---

## 3. `setup_exception_handlers()` en `main.py` — ALTA

**Archivo:** `app/main.py`  
**Líneas:** 196–400 (**205 líneas**)

**Qué hace actualmente:** Define 15+ handlers de excepción siguiendo un patrón idéntico repetido:
```python
@app.exception_handler(SomeException)
async def handler(request, exc):
    return JSONResponse(status_code=..., content={"detail": ..., "error_code": "..."})
```

**Cómo dividirla:**

| Función Sugerida | Responsabilidad |
|-----------------|-----------------|
| `_create_simple_error_handler(status_code, error_code)` | Factory que genera handlers |
| `_register_exception_handlers(app, handlers_config)` | Registra todos los handlers |
| Tabla de configuración `EXCEPTION_HANDLERS_CONFIG` | Lista de (ExcClass, status_code, error_code) |
| `setup_exception_handlers()` (refactorizado) | Orquestador de 10 líneas |

**Resultado:** 205 líneas → ~35 líneas + tabla de datos legible

---

## 4. `_enrich_diet_with_fatsecret()` en `diet_service.py` — ALTA

**Archivo:** `app/services/diet_service.py`  
**Líneas:** 591–707 (**117 líneas**)

**Qué hace actualmente:**
1. Colección de alimentos de dicts anidados (loops de 3 niveles)
2. Ejecución paralela con ThreadPoolExecutor
3. Manejo de errores para dos servicios (FatSecret → USDA fallback)
4. Parsing de porciones y extracción de gramos
5. Cálculo y escalado de macros
6. Recálculo de totales de comidas y días

**Cómo dividirla:**

| Función Sugerida | Responsabilidad |
|-----------------|-----------------|
| `_collect_food_items(diet_data)` | Solo extrae alimentos de la estructura anidada |
| `_resolve_food_nutrition(name)` | Lookup de un alimento con fallback |
| `_fetch_food_macros_parallel(names)` | Ejecución paralela del lookup |
| `_scale_macros_to_portion(result, grams)` | Escalado matemático de macros |
| `_apply_nutrition_to_foods(food_items, lookup_results)` | Escribe macros en los dicts |
| `_refresh_diet_totals(diet_data)` | Recalcula totales |

---

## 5. `log_meal()` en `diet_service.py` — ALTA

**Archivo:** `app/services/diet_service.py`  
**Líneas:** 858–927 (**70 líneas**)

**Qué hace actualmente:**
1. Reset del tracker de comidas si es día nuevo
2. Resolución del tipo de día desde lista de training days
3. Resolución de la comida (con chequeo de overrides)
4. Acumulación de macros
5. Dos actualizaciones separadas de estructuras de datos (diet.daily_consumed + DailyNutrition)
6. Import circular workaround (`nutrition_service` importado localmente)

**Cómo dividirla:**

| Función Sugerida | Responsabilidad |
|-----------------|-----------------|
| `_reset_tracker_on_new_day(diet, today)` | Solo el reset basado en fecha |
| `_get_effective_meal(diet, day_key, index)` | Obtiene comida con soporte de override |
| `_calculate_meal_macros_consumed(meal)` | Extrae totales de una comida |
| `_record_consumed_in_diet(diet, date_str, macros)` | Actualiza diet.daily_consumed |
| `_record_consumed_in_daily_nutrition(db, user_id, macros)` | Actualiza tabla DailyNutrition |

---

## 6. `log_session()` en `routine_service.py` — ALTA

**Archivo:** `app/services/routine_service.py`  
**Líneas:** 502–582 (**81 líneas**)

**Qué hace actualmente:**
1. Fetch y validación de rutina
2. Lookup de sesión en datos anidados
3. Cálculo de calorías (matemática compleja basada en MET)
4. Adición de macros de ejercicios extra
5. Creación de objeto WorkoutSession con dict ai_output anidado
6. Dos operaciones de base de datos separadas (sesión + agregación diaria)

**Cómo dividirla:**

| Función Sugerida | Responsabilidad |
|-----------------|-----------------|
| `_find_routine_session(routine, session_id)` | Solo busca y valida la sesión |
| `_estimate_session_total_calories(...)` | Todo el cálculo de calorías |
| `_create_workout_session_record(...)` | Creación del objeto (sin DB ops) |
| `_save_workout_and_update_daily_log(db, session, user_id, date)` | Solo persistencia |

---

## 7. `ensure_schema_compatibility()` en `database.py` — MEDIA

**Archivo:** `app/db/database.py`  
**Líneas:** 90–129 (**40 líneas**)

**Qué hace actualmente:**
1. Chequeo de compatibilidad de schema (inspecta tablas)
2. Creación de tablas faltantes
3. Migración de columnas para 3 tablas distintas (users, user_routines, user_diets)
4. Operaciones de base de datos con manejo de transacciones anidado
5. Logging en cada paso

**Cómo dividirla:**

| Función Sugerida | Responsabilidad |
|-----------------|-----------------|
| `_check_schema_state()` | Solo inspección del schema (puro) |
| `_migrate_user_columns(columns)` | DDL de tabla users |
| `_migrate_routine_columns(columns)` | DDL de tabla routines |
| `_migrate_diet_columns(columns)` | DDL de tabla diets |
| `ensure_schema_compatibility()` (refactorizado) | Orquestador de 10 líneas |

---

## 8. `advance_session()` en `routine_service.py` — MEDIA

**Archivo:** `app/services/routine_service.py`  
**Líneas:** 587–642 (**56 líneas**)

**Qué hace actualmente:** Máquina de estados + lógica de negocio: fetch, validación, logging condicional (solo si action='complete'), avance de índice con wrapping, commit a DB.

**Cómo dividirla:**

| Función Sugerida | Responsabilidad |
|-----------------|-----------------|
| `_get_routine_session_by_index(routine, index)` | Lookup de sesión (puro) |
| `_perform_routine_session_logging(action, db, user_id, index, weight)` | Logging condicional |
| `_wrap_routine_session_index(current, total)` | Avance de índice con wrapping (puro) |

---

## 9. `get_meal_alternative()` en `diet_service.py` — MEDIA

**Archivo:** `app/services/diet_service.py`  
**Líneas:** 930–1000+ (**70+ líneas**)

**Qué hace actualmente:** IO (fetch DB) + extracción de preferencias + construcción de prompt + llamada API + parsing de respuesta.

**Cómo dividirla:**

| Función Sugerida | Responsabilidad |
|-----------------|-----------------|
| `_normalize_intake_data(raw_intake)` | Normaliza preferencias del usuario |
| `_create_meal_alternative_prompt(meal, preferences)` | Formatea prompt para Gemini |
| `_postprocess_alternative_meal(meal_json)` | Post-proceso de respuesta |

---

## Tabla Resumen

| Función | Archivo | Líneas | Niveles Indent. | Prioridad |
|---------|---------|--------|-----------------|-----------|
| `_generate_html()` | routine_service.py | 279 | 3–4 | **CRÍTICA** |
| `_generate_diet_html()` | diet_service.py | 169 | 4–5 | **CRÍTICA** |
| `setup_exception_handlers()` | main.py | 205 | 2 (DRY violation) | **ALTA** |
| `_enrich_diet_with_fatsecret()` | diet_service.py | 117 | 5 | **ALTA** |
| `log_session()` | routine_service.py | 81 | 3 | **ALTA** |
| `log_meal()` | diet_service.py | 70 | 4 | **ALTA** |
| `get_meal_alternative()` | diet_service.py | 70+ | 3 | Media |
| `advance_session()` | routine_service.py | 56 | 3 | Media |
| `ensure_schema_compatibility()` | database.py | 40 | 4 | Media |

---

## Fases de Refactorización Sugeridas

### Fase 1 — Quick wins
- Refactorizar `setup_exception_handlers()` con patrón factory
- Dividir `ensure_schema_compatibility()` en funciones por tabla

### Fase 2 — Alto impacto
- Extraer generación HTML de ambos `_generate_html()` a partes separadas
- Mover CSS/JS a archivos o constantes separadas

### Fase 3 — Claridad de lógica de negocio
- Refactorizar `log_meal()` separando concerns
- Separar `log_session()` en validación → cálculo → persistencia
