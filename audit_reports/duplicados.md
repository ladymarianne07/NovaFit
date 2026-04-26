# Auditoría de Código Duplicado — NovaFitness Backend
**Fecha:** 2026-04-04 | **Tipo:** Solo lectura

## Resumen Ejecutivo

Se identificaron **10 categorías de código duplicado o casi-duplicado** en el proyecto. El impacto estimado de refactorización: reducción de **300–400 líneas** y mejora significativa de mantenibilidad.

---

## 1. Patrón de Manejo de Excepciones (CRÍTICO)

**Archivos afectados:**
- `app/api/diet.py` — líneas 84–92, 118–127, 149–157, 179–187, 211–219, 237–242, 268–274, 306–316
- `app/api/routine.py` — líneas 70–82, 119–127, 152–162, 184–192, 221–229, 256–264
- `app/api/workout.py` — líneas 61–71, 88–94, 115–121, 141–147

**Patrón repetido:**
```python
except DietNotFoundError as exc:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
except DietParsingError as exc:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
except HTTPException:
    raise
except Exception:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to ...")
```

**Propuesta:** Decorador unificado `@handle_service_exceptions(default_error_message: str)`  
**Módulo sugerido:** `app/core/exception_handlers.py` (nuevo)  
**Líneas duplicadas estimadas:** 50+

---

## 2. Validación de Acción (complete/skip)

**Archivos afectados:**
- `app/api/diet.py` — línea 202–203
- `app/api/routine.py` — línea 204–208

**Patrón:**
```python
if payload.action not in ("complete", "skip"):
    raise HTTPException(status_code=400, detail="action must be 'complete' or 'skip'")
```

**Propuesta:** `validate_action_complete_or_skip(action: str) -> None`  
**Módulo sugerido:** `app/services/validation_service.py`

---

## 3. Extracción de Datos Biométricos del Usuario

**Archivos afectados:**
- `app/api/diet.py` — líneas 52–63
- `app/api/routine.py` — líneas 102–108

**Patrón:**
```python
user_bio: dict[str, Any] = {
    "age": getattr(current_user, "age", None),
    "gender": getattr(current_user, "gender", None),
    "weight_kg": getattr(current_user, "weight_kg", None),
    "height_cm": getattr(current_user, "height_cm", None),
    ...
}
```

**Propuesta:** `extract_user_bio(user: User, include_fields: list[str] | None = None) -> dict[str, Any]`  
**Módulo sugerido:** `app/services/user_service.py`  
**Líneas duplicadas estimadas:** 12

---

## 4. Consulta de Recurso Activo del Usuario

**Archivos afectados:**
- `app/services/diet_service.py` — líneas 805–810
- `app/services/routine_service.py` — líneas 456–465

**Patrón:**
```python
# En DietService:
diet = db.query(UserDiet).filter(UserDiet.user_id == user_id).first()
if diet is None:
    raise DietNotFoundError("No active diet plan found.")
return diet

# En RoutineService (idéntico):
routine = db.query(UserRoutine).filter(UserRoutine.user_id == user_id).first()
if routine is None:
    raise RoutineNotFoundError("No active routine found.")
return routine
```

**Propuesta:** `get_user_active_resource(db, user_id, model_class, not_found_error_class, resource_name)`  
**Módulo sugerido:** `app/services/base_service.py` (nuevo)  
**Líneas duplicadas estimadas:** 10

---

## 5. Workflow de Generación/Edición con Gemini

**Archivos afectados:**
- `app/services/diet_service.py` — líneas 719–763, 766–802
- `app/services/routine_service.py` — líneas 372–411, 416–451

**Patrón (ambos servicios siguen exactamente esta secuencia):**
1. Crear/upsert registro con status PROCESSING
2. `db.commit()`
3. `try:` → llamar Gemini → generar HTML → setear status READY
4. `except:` → setear status ERROR + error_message
5. `db.commit()` + `db.refresh()`

**Propuesta:** Clase base abstracta con `_execute_gemini_generation_workflow()`  
**Módulo sugerido:** `app/services/gemini_base_service.py` (nuevo abstracto)  
**Líneas duplicadas estimadas:** 200+

---

## 6. Constante de URL de la API de Gemini

**Archivos afectados:**
- `app/services/diet_service.py` — línea 23
- `app/services/routine_service.py` — línea 29
- `app/services/ai_parser_service.py` — línea 23

**Duplicado:**
```python
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
```

**Propuesta:** Mover a `app/constants.py` bajo `GeminiConstants.API_BASE_URL`

---

## 7. Extracción de Peso del Usuario

**Archivos afectados:**
- `app/api/routine.py` — líneas 210–211, 242–243
- `app/api/workout.py` — líneas 34–37

**Patrón:**
```python
weight_kg = float(getattr(user_data, "weight_kg", 0.0) or 0.0)
```

**Propuesta:** `extract_weight_kg(user: User) -> float`  
**Módulo sugerido:** `app/services/user_service.py`

---

## 8. Extracción de User ID

**Archivos afectados:** Todos los archivos de API (`diet.py`, `routine.py`, `workout.py`, `nutrition.py`, `users.py`)

**Patrón repetido:**
```python
user_id=int(getattr(current_user, "id"))
```

**Propuesta:** `get_user_id(user: User) -> int`  
**Módulo sugerido:** `app/dependencies.py`  
**Líneas duplicadas estimadas:** 30+

---

## 9. Templates JSON de Instrucciones para Gemini

**Archivos afectados:**
- `app/services/diet_service.py` — líneas 27–98
- `app/services/routine_service.py` — líneas 33–121

Ambos servicios tienen bloques grandes de instrucciones de esquema JSON con reglas y estructuras superpuestas ("Return ONLY valid JSON", reglas de validación).

**Propuesta:** Extraer a `app/services/gemini_templates.py`  
**Líneas duplicadas estimadas:** 150+

---

## 10. Constantes de Status

**Archivos afectados:**
- `app/services/diet_service.py` — líneas 714–716
- `app/services/routine_service.py` (implícito)

Los valores `"processing"`, `"ready"`, `"error"` están definidos inline en lugar de usar las constantes existentes en `app/constants.py`.

**Propuesta:** Usar `DietConstants.STATUS_READY` etc. consistentemente

---

## Tabla Resumen

| Issue | Severidad | Archivos | Líneas Dup. | Módulo Sugerido |
|-------|-----------|----------|-------------|-----------------|
| Patrón try-except en endpoints | **ALTA** | 8 archivos | 50+ | `app/core/exception_handlers.py` |
| Validación action complete/skip | Media | 2 | 3 | `app/services/validation_service.py` |
| Extracción user bio | Media | 2 | 12 | `app/services/user_service.py` |
| Consulta recurso activo | Media | 2 servicios | 10 | `app/services/base_service.py` |
| Workflow generate/edit Gemini | **ALTA** | 2 servicios | 200+ | `app/services/gemini_base_service.py` |
| URL API Gemini | Baja | 3 | 1 | `app/constants.py` |
| Extracción weight_kg | Baja | 3 | 3 | `app/services/user_service.py` |
| Extracción user_id | Media | 6+ | 30+ | `app/dependencies.py` |
| Templates JSON schema | Media | 2 servicios | 150+ | `app/services/gemini_templates.py` |
| Constantes de status | Baja | 2+ | varios | Usar constants existentes |

---

## Orden de Refactorización Sugerido

1. **Fase 1 (Alto impacto):** Decorador de excepciones, clase base workflow Gemini
2. **Fase 2 (Medio impacto):** Helpers user bio/id, base service con recurso activo
3. **Fase 3 (Bajo impacto):** Mover constantes, templates JSON, unificar status
