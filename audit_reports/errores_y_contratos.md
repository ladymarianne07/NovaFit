# Auditoría de Manejo de Errores y Contratos de API — NovaFitness Backend
**Fecha:** 2026-04-04 | **Tipo:** Solo lectura

## Resumen Ejecutivo

Se identificaron **16 inconsistencias** en manejo de errores y contratos de API. El proyecto tiene buenas intenciones (jerarquía de excepciones, exception handlers) pero **falta enforcement**. La inconsistencia más grave: el mismo error de validación devuelve 400 en un endpoint y 422 en otro.

---

## Sección 1: Inconsistencias en Estructura de Respuesta de Error

### 1.1 Mismo tipo de error → diferentes status codes

**El error más crítico:** La validación de campo `action` devuelve HTTP 400 en diet y HTTP 422 en routine.

| Error | Endpoint | Status Code |
|-------|----------|-------------|
| Validación de `action` (complete/skip) | `POST /v1/diet/log-meal` | **400** |
| Validación de `action` (complete/skip) | `POST /v1/routines/advance-session` | **422** |

**Archivos:**
- `app/api/diet.py:202–203`
- `app/api/routine.py:204–208`

---

### 1.2 Tres estructuras de respuesta de error distintas

**Patrón A — Solo string (mayoría de endpoints):**
```json
{"detail": "No active diet plan found."}
```

**Patrón B — Con error_code (exception handlers en main.py):**
```json
{
  "detail": "Biometric validation failed",
  "errors": {"field": "error message"},
  "error_code": "BIOMETRIC_VALIDATION_ERROR"
}
```

**Patrón C — Con campo extra:**
```json
{
  "detail": "Invalid input data",
  "field": "email"
}
```

**Archivos:**
- Patrón A: `app/api/diet.py:85, 118, 150, 180, 212, 238, 269`
- Patrón B: `app/main.py:222–340`
- Patrón C: `app/main.py:255–263`

---

### 1.3 Fallas silenciosas en servicios

En `app/services/diet_service.py`:
- Líneas 756–759: cuando la generación falla, el método captura todas las excepciones y setea `error_message` **en lugar de propagar**
- Líneas 795–798: cuando la edición falla, mismo patrón

Esto crea un mismatch: la capa de servicio **traga excepciones**, la capa de endpoint las **re-lanza**. El endpoint no puede distinguir si el servicio falló silenciosamente.

---

## Sección 2: Validación de Inputs Faltante

### 2.1 Lógica de validación en endpoints en lugar de schemas

| Endpoint | Validación | Ubicación actual | Debería estar en |
|----------|-----------|-----------------|-----------------|
| `POST /v1/diet/log-meal` | `action` enum | `diet.py:202` | Schema `DietLogMealRequest` |
| `POST /v1/diet/modify-meal` | `action` enum + campos condicionales | `diet.py:289–294` | Schema `DietModifyMealRequest` |
| `POST /v1/routines/advance-session` | `action` enum | `routine.py:204` | Schema `RoutineAdvanceSessionRequest` |
| `POST /v1/diet/meals/alternative` | `action` enum | `diet.py:257` | Schema correspondiente |

### 2.2 Ausencia de validación de rango en service layer

`DietService.modify_meal()` acepta `day_type`, `meal_id`, `food_index` sin validación de rango. Depende del acceso a arrays para fallar con errores genéricos. No hay pre-checks para valores válidos de `day_type` (debería ser `"training_day"` o `"rest_day"`).

---

## Sección 3: Type Hints Faltantes en Funciones Públicas

### DietService — métodos con type hints incompletos

| Método | Problema |
|--------|---------|
| `get_current_meal()` | Retorna `dict[str, Any]` — vago; estructura de keys no especificada |
| `log_meal()` | Retorna `dict[str, Any]` — estructura de retorno poco clara |
| `get_meal_alternative()` | Retorna `dict[str, Any]` — estructura no especificada |
| `apply_meal_alternative()` | **Missing return type completamente** (línea 1023) |
| `modify_meal()` | Falta anotación de retorno completa |

### RoutineService — métodos con type hints incompletos

| Método | Problema |
|--------|---------|
| `advance_session()` | Retorna `dict[str, Any]` — estructura vaga |

---

## Sección 4: Análisis de Jerarquía de Excepciones

### Lo que está bien
- Clase base `NovaFitnessException` existe en `app/core/custom_exceptions.py:6`
- Excepciones específicas por dominio definidas (`DietNotFoundError`, `RoutineParsingError`, etc.)
- Exception handlers en `app/main.py:196–399`

### Lo que falta
- Los exception handlers en `main.py` no son aplicados consistentemente: endpoints a veces lanzan `HTTPException` directamente en lugar de usar la jerarquía
- Sin formato de respuesta de error estándar enforceado
- Error codes no aplicados consistentemente
- Sin niveles de severidad de errores

---

## Sección 5: Mapa Completo de Inconsistencias

| Escenario | Endpoint 1 | Status | Endpoint 2 | Status | ¿Consistente? |
|-----------|-----------|--------|-----------|--------|--------------|
| Recurso no encontrado | `GET /diet/active` | 404 | `GET /routines/active` | 404 | ✅ |
| Validación campo action | `POST /diet/log-meal` | **400** | `POST /routines/advance-session` | **422** | ❌ |
| Error de parsing/IA | `POST /diet/generate` | 422 | `POST /routines/upload` | 422 | ✅ |
| Media type inválido | N/A | — | `POST /routines/upload` | 415 | Parcial |
| Archivo muy grande | N/A | — | `POST /routines/upload` | 413 | Parcial |

---

## Sección 6: Contrato de Error Estándar Propuesto

### 6.1 Schema de Respuesta Unificado

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "error_type": "validation|not_found|conflict|server_error",
  "timestamp": "2026-04-04T12:34:56Z"
}
```

**Para errores de validación con múltiples campos:**
```json
{
  "detail": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "error_type": "validation",
  "errors": {
    "field_name": "Error message for this field"
  },
  "timestamp": "2026-04-04T12:34:56Z"
}
```

---

### 6.2 Tabla de Status Codes Estandarizados

| Status | Uso | Ejemplo |
|--------|-----|---------|
| **400** | Request malformado o campo inválido | Formato de fecha inválido, campo faltante, action inválido |
| **401** | Autenticación requerida o fallida | JWT missing/inválido |
| **403** | Autenticado pero no autorizado | No-trainer accediendo endpoint de trainer |
| **404** | Recurso no encontrado | Usuario/dieta/rutina no encontrado |
| **409** | Conflicto (recurso ya existe) | Email ya en uso, student ya vinculado |
| **410** | Gone (expirado) | Código de invitación expirado |
| **413** | Payload demasiado grande | Archivo supera límite de tamaño |
| **415** | Media type no soportado | Tipo de archivo incorrecto |
| **422** | Error de IA/parsing | Gemini devolvió JSON inválido |
| **500** | Error de servidor | Excepción inesperada |

**Regla clave:**
- ❌ NO usar 422 para validaciones simples de campo → usar **400**
- ❌ NO usar 400 para errores de parsing/generación de IA → usar **422**

---

### 6.3 Enumeración de Error Codes

```python
class ErrorCode(str, Enum):
    # Validación (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_ACTION = "INVALID_ACTION"
    INCOMPLETE_DATA = "INCOMPLETE_DATA"
    
    # Auth (401)
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Autorización (403)
    FORBIDDEN = "FORBIDDEN"
    TRAINER_ONLY = "TRAINER_ONLY"
    
    # Not Found (404)
    DIET_NOT_FOUND = "DIET_NOT_FOUND"
    ROUTINE_NOT_FOUND = "ROUTINE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # Conflicto (409)
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    STUDENT_ALREADY_LINKED = "STUDENT_ALREADY_LINKED"
    
    # Gone (410)
    INVITE_EXPIRED = "INVITE_EXPIRED"
    
    # File errors (413, 415)
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    
    # Parsing/Generación (422)
    PARSING_ERROR = "PARSING_ERROR"
    GEMINI_ERROR = "GEMINI_ERROR"
    
    # Servidor (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

---

### 6.4 Estrategia para Service Layer

Todos los métodos públicos deben:
1. ✅ Lanzar excepciones de dominio (no retornar None)
2. ✅ Incluir mensajes descriptivos en el texto de excepción
3. ✅ Usar tipos de excepción consistentes para la misma clase de error
4. ✅ Tener anotaciones de tipo en todos los métodos

---

## Sección 7: Ítems de Acción por Prioridad

### Alta Prioridad
1. **Estandarizar status codes** — Cambiar validaciones simples a 400 (no 422)
   - `app/api/routine.py:204–208`
   - `app/api/diet.py:257–258`

2. **Implementar formato de respuesta de error unificado**
   - Crear modelo Pydantic `ErrorResponse`
   - Actualizar todos los exception handlers en `app/main.py:196–399`
   - Enforcar `error_code` en TODAS las respuestas de error

3. **Agregar return type annotations faltantes**
   - `app/services/diet_service.py:813, 858, 930, 1023, 1069`

### Prioridad Media
4. Mover validación de `action` de endpoints a schemas
5. Agregar sanitización de inputs en service layer
6. Documentar formatos de error en OpenAPI con `responses={}` en cada endpoint

### Prioridad Baja
7. Agregar request ID a respuestas de error (para tracing)
8. Implementar logging estructurado con error codes

---

## Tabla Resumen

| Categoría | Issues | Severidad |
|-----------|--------|-----------|
| Status codes inconsistentes | 2 | **Alta** |
| Variaciones en formato de respuesta de error | 3 | **Alta** |
| Type hints faltantes | 5 | Media |
| Validación de inputs faltante | 4 | Media |
| Fallas silenciosas (catch-all en servicios) | 2 | Media |
| **Total** | **16** | |

---

## Evaluación General

El codebase tiene **buena intención** (jerarquía de excepciones, handlers) pero **pobre enforcement**. Implementar el contrato de error unificado mejorará significativamente la confiabilidad de la API y el manejo de errores en el cliente.
