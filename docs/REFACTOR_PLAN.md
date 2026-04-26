# REFACTOR_PLAN.md — Plan de refactor heredado y estado actual

> **Origen:** Auditoría de backend del 2026-04-04 (`audit_reports/` legacy, ahora consolidado acá).
> **Última verificación contra código:** 2026-04-26 vía agente de auditoría de docs + cross-ref con commits del sprint.
> **Estado global:** ~75% ejecutado en `refactor-2026-04-26-WIP`. Queda P1.1 (contrato de error unificado), P3.1 (dividir HTML) y P3.3 (dividir log_meal/log_session) como deuda visible.

---

## Estado por prioridad

### 🔴 P1 — Impacto inmediato en confiabilidad de la API

| Item | Estado | Notas | Archivos |
|---|---|---|---|
| **P1.1** Estandarizar contratos de error | 🟡 Parcial | Handlers globales unificados vía `_SIMPLE_ERROR_HANDLERS` factory + `service_error_handler`. Pero `request_validation`, `input_validation` y `biometric_validation` mantienen shapes únicos (con `field`, `errors`, `missing_fields`). El "Patrón A/B/C" de errores_y_contratos.md ya no es 3 patrones, pero falta unificar el shape final. | Pendiente: Trello card #11 |
| **P1.2** Validación de inputs a schemas Pydantic | ✅ Hecho | `action` y otros enum-like ya son `Literal[...]` en `app/schemas/diet.py:150` y `app/schemas/routine.py:139`. | — |

### 🟠 P2 — Deuda técnica de alto impacto

| Item | Estado | Notas | Archivos |
|---|---|---|---|
| **P2.1** Extraer templates de prompts IA | ✅ Hecho | `app/templates/{diet,routine,food_parser}.py` existen y son importados desde sus services. | — |
| **P2.2** Eliminar workflow Gemini duplicado | ✅ Hecho | `app/services/base_ai_generation_service.py` con `BaseAIGenerationService`. `DietService` y `RoutineService` heredan. `RoutineService.parse_and_save` (file upload) también usa `_set_record_ready`/`_set_record_error` desde Card #10 (commit `ffb3ccf`). | — |
| **P2.3** Decorador de manejo de excepciones | ✅ Hecho (mayormente) | `service_error_handler` (context manager) en `app/core/exception_handlers.py`. Adoptado en `api/diet.py`, `api/routine.py`, `api/workout.py`, `api/auth.py`, `api/users.py`, `routers/food.py`. Los routers chicos (`events`, `invite`, `notifications`, `trainer`) podrían beneficiarse pero no es urgente. | — |

### 🟡 P3 — Calidad de código y legibilidad

| Item | Estado | Notas |
|---|---|---|
| **P3.1** Dividir funciones de generación HTML | 🟡 Probablemente parcial | `routine_service._generate_html` y `diet_service._generate_diet_html` siguen siendo grandes. Verificar antes de dar por hecho. |
| **P3.2** Refactorizar `setup_exception_handlers()` | ✅ Hecho | `app/main.py:200-232` usa `_SIMPLE_ERROR_HANDLERS` table + `_create_simple_error_handler` factory. |
| **P3.3** Dividir `log_meal()` y `log_session()` | 🟡 Por confirmar | Los métodos siguen siendo extensos. La refactorización requiere tests de integración antes del deploy. Trello card pendiente. |

### 🟢 P4 — Limpieza menor

| Item | Estado | Notas |
|---|---|---|
| **P4.1** Renombrar `_404`, `_422`, `_500` | 🟡 Parcial | Hecho para diet (`_RESPONSES_404`/`_422`/`_500`). Las columnas de DB `kcal_*`, `met_*`, `bmr_bpm` siguen así (renombrar requiere migración Alembic — ver advertencia en sección "Cambios con efecto cascada"). |
| **P4.2** Eliminar código muerto | 🟡 Parcial | `drop_tables()` ya no existe en `database.py`. `cast` import en `app/api/routine.py:6` revisar. |
| **P4.3** Helpers de user service | ✅ Hecho | `app/core/user_helpers.py` con `extract_user_bio`, `get_current_user_id`, `extract_weight_kg`. Usado en routers refactoreados. |
| **P4.4** Deuda menor | ❌ Pendiente | Redis cache en `food_aggregator_service.py`; `@abstractmethod` a `BaseConnector`. Crear card si se prioriza. |

---

## Trabajo del sprint actual (2026-04-26+) que cierra puntos del plan

| Card Trello | Cerró | Detalle |
|---|---|---|
| Card #3 (security: /users/all) | + dead code (P4.2) | Eliminó endpoint y service method huérfanos |
| Card #4 (security: /food/*) | P2.3 +2 routers | `food.py` ahora usa pattern del refactor |
| Card #5 (fix except Exception en update_user_objective) | P1.1 progreso | Eliminó try/except redundante; deja ruteo a handlers globales |
| Card #10 (avg_kcal) | P2.2 +1 path | `parse_and_save` ahora delega a `_set_record_ready` (DRY) |

---

## Advertencias de cambios con efecto cascada (vigentes)

1. **Estandarización del contrato de error** (P1.1) — el frontend (`frontend/src/services/api.ts`) puede estar parseando `detail` como string. Si el backend cambia el shape, hay que coordinar el frontend en paralelo. Mitigación: el frontend nuevo (Claude Design) puede consumir el nuevo shape directo.

2. **Renombre de columnas DB** (P4.1) — `kcal_*`, `met_*`, `bmr_bpm` son columnas reales. Renombrar requiere migración Alembic (decisión sobre Alembic vs auto-ALTER en [`DECISIONS.md`](DECISIONS.md)). Mientras siga el auto-ALTER de startup, no renombrar.

3. **Refactor de `log_meal()` y `log_session()`** (P3.3) — tocan múltiples tablas con lógica de estado. Refactorización válida pero exige tests de integración completos antes del deploy.

---

## Items NO incluidos en el plan original pero detectados en el sprint

| Item | Origen | Estado | Card Trello |
|---|---|---|---|
| `Settings` rechaza env vars extra y rompe pytest | Card #3 (descubrimiento lateral) | ❌ Pendiente | #35 |
| Estrategia de prefijos `/api` `/v1/` (doble registro) | Card #1 mapping (regresión del refactor) | ❌ Pendiente | #6 |
| Frontend kcal hardcoded a 70 kg | Mapeo inicial 2026-04-26 | ❌ Pendiente | (sin card aún — crear cuando arranque frontend nuevo) |
| Dual fuente de verdad `UserDiet.daily_consumed` vs `DailyNutrition` | Mapeo inicial | ❌ Pendiente | #7 |
| `DailyNutrition.targets` no se actualiza en cambios | Mapeo inicial | ❌ Pendiente | #8 |
| Invariante `4·p + 4·c + 9·f = target_calories` ± rounding | Mapeo inicial | ❌ Pendiente | #9 |

---

## Cómo se actualiza este archivo

- Cada vez que una card de Trello cierre algún ítem del plan, marcar el estado y agregar a "Trabajo del sprint actual".
- Si surge una nueva área de refactor durante el sprint (no estaba en el audit original), agregar a la sección "Items NO incluidos en el plan original".
- Para audit nuevos en el futuro, **NO crear `audit_reports_legacy/` de nuevo** — extender este archivo o crear `REFACTOR_PLAN_v2.md` referenciado desde acá.
