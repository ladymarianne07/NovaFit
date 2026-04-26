# ERROR_HANDLING.md — Contrato de errores

> Cómo se manejan los errores en el backend de NovaFitness, qué excepciones existen, qué shape de respuesta produce cada una, y cómo agregar errores nuevos.

---

## Principio

**Los servicios lanzan excepciones de dominio (subclases de `NovaFitnessException`). Los routers usan `service_error_handler` y dejan que los handlers globales formateen la respuesta.** Casi nunca un router debería tener un `try/except` propio.

---

## Jerarquía de excepciones

Todas viven en [`app/core/custom_exceptions.py`](../app/core/custom_exceptions.py).

```
Exception
└── NovaFitnessException                  ← base de todas las del dominio
    ├── UserAlreadyExistsError            → 409 USER_ALREADY_EXISTS
    ├── UserNotFoundError                 → 400 (manejada por handler genérico)
    ├── InvalidCredentialsError           → 401 INVALID_CREDENTIALS
    ├── InactiveUserError                 → 400
    ├── BiometricValidationError          → 422 BIOMETRIC_VALIDATION_ERROR (con `errors` dict)
    ├── IncompleteBiometricDataError      → 400 INCOMPLETE_BIOMETRIC_DATA (con `missing_fields`)
    ├── BiometricCalculationError         → 500 BIOMETRIC_CALCULATION_ERROR
    ├── TokenValidationError              → 400
    ├── ValidationError                   → 422 VALIDATION_ERROR (base de las de validación)
    │   ├── PasswordValidationError       → 422 PASSWORD_VALIDATION_ERROR
    │   ├── EmailValidationError          → 422 EMAIL_VALIDATION_ERROR
    │   ├── NameValidationError           → 422 NAME_VALIDATION_ERROR
    │   ├── InputValidationError          → 422 INPUT_VALIDATION_ERROR (con `field`)
    │   └── WorkoutValidationError        → 422 (manejada por la base ValidationError)
    │
    ├── WorkoutActivityNotFoundError      → 400
    ├── WorkoutWeightRequiredError        → 400
    │
    ├── RoutineNotFoundError              → 400 (mapeada en endpoint a 404)
    ├── RoutineParsingError               → 400 (mapeada en endpoint a 422)
    ├── RoutineFileTooLargeError          → 400 (mapeada en endpoint a 413)
    ├── RoutineInvalidFileTypeError       → 400 (mapeada en endpoint a 415)
    │
    ├── TrainerOnlyError                  → 403 TRAINER_ONLY
    ├── InviteNotFoundError               → 404 INVITE_NOT_FOUND
    ├── InviteAlreadyUsedError            → 409 INVITE_ALREADY_USED
    ├── InviteExpiredError                → 410 INVITE_EXPIRED
    ├── StudentAlreadyLinkedError         → 409 STUDENT_ALREADY_LINKED
    ├── StudentNotLinkedError             → 404 STUDENT_NOT_LINKED
    │
    ├── DietNotFoundError                 → 400 (mapeada en endpoint a 404)
    └── DietParsingError                  → 400 (mapeada en endpoint a 422)
```

Las excepciones que dicen "→ 400" sin `error_code` específico caen en el **handler genérico de `NovaFitnessException`** ([`app/main.py:272-277`](../app/main.py#L272-L277)) que devuelve `{detail, error_code}` con `error_code` tomado del atributo de la excepción (puede ser `None` si no se setea).

---

## Shape canónica de respuesta

### Caso simple (mayoría de errores)

```json
{
  "detail": "<mensaje human-readable>",
  "error_code": "<UPPERCASE_SNAKE_CASE>"
}
```

### Caso con campo (`InputValidationError`)

```json
{
  "detail": "Validation error for <field>: <reason>",
  "field": "<field_name>",
  "error_code": "INPUT_VALIDATION_ERROR"
}
```

### Caso con errors dict (`BiometricValidationError`)

```json
{
  "detail": "Biometric validation failed",
  "errors": {"weight": "must be > 0", "height": "must be > 0"},
  "error_code": "BIOMETRIC_VALIDATION_ERROR"
}
```

### Caso con missing fields (`IncompleteBiometricDataError`)

```json
{
  "detail": "Required biometric fields missing: weight, height",
  "missing_fields": ["weight", "height"],
  "error_code": "INCOMPLETE_BIOMETRIC_DATA"
}
```

### Validación de Pydantic (FastAPI maneja el `RequestValidationError`)

```json
{
  "detail": "<field_path>: <pydantic msg>",
  "error_code": "VALIDATION_ERROR"
}
```

### Catch-all (último recurso)

```json
{
  "detail": "An unexpected error occurred",
  "error_code": "INTERNAL_SERVER_ERROR"
}
```

> ⚠ **Pendiente (Card #11 del Backlog):** unificar las shapes con `field` / `errors` / `missing_fields` bajo una estructura única (probablemente `details: object` opcional). Hoy hay 4 shapes en uso.

---

## Cómo se conectan las piezas

### Path 1 — Excepción de dominio en service → handler global

```python
# 1. Service lanza la excepción específica
class DietService:
    @classmethod
    def get_active_diet(cls, db, *, user_id):
        diet = db.query(UserDiet).filter(...).first()
        if not diet:
            raise DietNotFoundError("No active diet found.")
        return diet
```

```python
# 2. Endpoint usa service_error_handler — sin try/except artesanal
from ..core.exception_handlers import service_error_handler

@router.get("/v1/diet/active")
async def get_active_diet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    with service_error_handler():
        return DietService.get_active_diet(db, user_id=current_user.id)
```

```python
# 3. main.py tiene el handler global
@app.exception_handler(NovaFitnessException)
async def nova_fitness_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message, "error_code": exc.error_code},
    )
```

### Path 2 — Mapeo a status code específico (404, 413, etc.)

Cuando un router quiere mapear a un código HTTP distinto del default del handler global (ej: `RoutineNotFoundError` debería ser 404 desde el endpoint, no 400), se captura específicamente:

```python
@router.get("/v1/routines/active")
async def get_active_routine(...):
    try:
        return RoutineService.get_active_routine(db, user_id=current_user.id)
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
```

Esto es el patrón vigente en `app/api/diet.py`, `app/api/routine.py`, `app/api/workout.py`. **Limitación conocida:** rompe la consistencia del shape (el handler global devuelve `{detail, error_code}`, el `HTTPException` devuelve sólo `{detail}`). Card #11 del Backlog lo va a unificar.

---

## `service_error_handler` — qué hace

Context manager en [`app/core/exception_handlers.py`](../app/core/exception_handlers.py):

| Caso | Acción |
|---|---|
| El service lanza `HTTPException` | Re-raise tal cual (FastAPI lo procesa) |
| El service lanza `NovaFitnessException` o subclase | Re-raise tal cual (handlers globales formatean) |
| El service lanza cualquier otra `Exception` | Convierte a `HTTPException(500)` con detail genérico |

Esto **elimina** los dos bloques `except` boilerplate que existían en cada endpoint. Está adoptado en `api/diet.py`, `api/routine.py`, `api/workout.py`, `api/auth.py`, `api/users.py`, `routers/food.py`. Routers chicos (`events`, `invite`, `notifications`, `trainer`) siguen sin él pero no es prioritario.

---

## Cómo agregar un error nuevo

### Caso A — error que sigue el shape simple `{detail, error_code}`

1. Definí la clase en [`app/core/custom_exceptions.py`](../app/core/custom_exceptions.py):
   ```python
   class MyNewError(NovaFitnessException):
       """Raised when X happens."""
       pass
   ```

2. Agregalo a la tabla `_SIMPLE_ERROR_HANDLERS` en [`app/main.py`](../app/main.py):
   ```python
   _SIMPLE_ERROR_HANDLERS: list[tuple[type, int, str]] = [
       ...
       (MyNewError, StatusCodes.BAD_REQUEST, "MY_NEW_ERROR"),
   ]
   ```

3. Lanzala desde el service donde corresponde:
   ```python
   raise MyNewError("Specific human-readable detail")
   ```

4. El endpoint NO necesita capturarla — el handler global y el factory se encargan.

### Caso B — error que necesita un shape custom (campos extra)

1. Definí la clase con los atributos extras:
   ```python
   class MyCustomShapeError(NovaFitnessException):
       def __init__(self, my_extra_field: str, message: str):
           self.my_extra_field = my_extra_field
           super().__init__(message)
   ```

2. Agregá un handler explícito en `setup_exception_handlers`:
   ```python
   @app.exception_handler(MyCustomShapeError)
   async def my_custom_handler(request, exc):
       return JSONResponse(
           status_code=422,
           content={
               "detail": exc.message,
               "my_extra_field": exc.my_extra_field,
               "error_code": "MY_CUSTOM_SHAPE_ERROR",
           },
       )
   ```

3. Documentá el shape acá en `ERROR_HANDLING.md` (el listado de shapes arriba).

> Aceptar shapes custom con prudencia. Cada shape distinto que se agrega es un parser que el frontend va a tener que mantener.

---

## Principios

1. **Excepciones de dominio van al service**, no al endpoint. El endpoint solo orquesta y delega.
2. **No usar `except Exception`** salvo en el handler global o en `service_error_handler`. Capturar sólo lo que sabés cómo manejar.
3. **`error_code` siempre en UPPER_SNAKE**, identificador estable que el frontend puede comparar como string. **El `detail` puede cambiar**; el `error_code` no.
4. **Un error agregado al handler global** automáticamente queda con shape consistente — usar el factory antes de inventar shape nuevo.
5. **Después de modificar el manejo de errores**, aplicar regla de `CLAUDE_INSTRUCTIONS.md` sección 3.1: diff código vs este doc; si divergen, decidir cuál es ground truth.

---

## Pendiente (cards activas)

- [Card #11](https://trello.com/c/...) — Unificar las shapes restantes (`field`, `errors`, `missing_fields`) bajo un único `details: object | null` opcional.
- Adoptar `service_error_handler` en routers chicos (`events`, `invite`, `notifications`, `trainer`) — beneficio bajo, no urgente.
