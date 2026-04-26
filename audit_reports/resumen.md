# Resumen de Auditoría Backend — NovaFitness
**Fecha:** 2026-04-04 | **Alcance:** Solo lectura — ningún archivo del proyecto fue modificado

---

## Tabla Resumen por Agente

| Agente | Reporte | Issues encontrados | Severidad global |
|--------|---------|-------------------|-----------------|
| 1 — Duplicados | [duplicados.md](duplicados.md) | 10 categorías (~500 líneas dup.) | **Alta** |
| 2 — Código muerto | [codigo_muerto.md](codigo_muerto.md) | 2 elementos | Baja |
| 3 — Código incompleto | [codigo_incompleto.md](codigo_incompleto.md) | 2 issues menores | Baja |
| 4 — Templates embebidos | [templates.md](templates.md) | 7 templates (~780 líneas) | **Alta** |
| 5 — Nomenclatura | [naming.md](naming.md) | 15 inconsistencias | Media |
| 6 — Complejidad | [complejidad.md](complejidad.md) | 9 funciones candidatas | **Alta** |
| 7 — Errores y contratos | [errores_y_contratos.md](errores_y_contratos.md) | 16 inconsistencias | **Alta** |

---

## Orden de Prioridad Sugerido

### 🔴 Prioridad 1 — Impacto inmediato en confiabilidad de la API

**¿Por qué atacar primero?** Estos issues afectan directamente a clientes de la API hoy, causando comportamiento impredecible.

**1.1 Estandarizar contratos de error** (`errores_y_contratos.md`)
- El mismo error de validación devuelve 400 en diet y 422 en routine — confunde al frontend
- Crear `ErrorResponse` Pydantic model con `error_code` obligatorio
- Unificar los 3 formatos de respuesta de error actuales
- Archivos: `app/main.py`, `app/api/diet.py`, `app/api/routine.py`

**1.2 Mover validación de inputs a los schemas** (`errores_y_contratos.md`)
- La validación del campo `action` vive en los endpoints en lugar de en Pydantic schemas
- Riesgo: bypaseable si se llama al servicio directamente
- Archivos: `app/schemas/diet.py`, `app/schemas/routine.py`

---

### 🟠 Prioridad 2 — Deuda técnica de alto impacto en mantenibilidad

**¿Por qué atacar segundo?** Reducen dramaticamente el costo de futuros cambios.

**2.1 Extraer templates de prompts IA** (`templates.md`)
- 780 líneas de prompts embebidas en servicios dificultan actualizarlos sin riesgo de romper lógica
- Crear `app/templates/diet.py`, `app/templates/routine.py`, `app/templates/food_parser.py`
- Sin impacto en funcionalidad, solo organización

**2.2 Eliminar el workflow Gemini duplicado** (`duplicados.md`)
- El patrón generate/edit (upsert → Gemini → HTML → set status) está copiado en `diet_service.py` y `routine_service.py`
- ~200 líneas duplicadas que evolucionan por separado
- Crear `app/services/gemini_base_service.py` con clase abstracta

**2.3 Decorador de manejo de excepciones en endpoints** (`duplicados.md`)
- 50+ líneas de bloques try-except idénticos repetidos en 8 archivos de API
- Crear `@handle_service_exceptions()` en `app/core/exception_handlers.py`

---

### 🟡 Prioridad 3 — Calidad de código y legibilidad

**¿Por qué atacar tercero?** No impactan la API en producción, pero hacen el código más difícil de mantener.

**3.1 Dividir funciones de generación HTML** (`complejidad.md`)
- `_generate_html()` en routine: 279 líneas mezclando HTML, CSS, JS y lógica de negocio
- `_generate_diet_html()` en diet: 169 líneas con el mismo problema
- Crear funciones separadas para CSS, JS, header, body

**3.2 Refactorizar `setup_exception_handlers()`** (`complejidad.md`)
- 205 líneas de patrón idéntico repetido 15 veces
- Usar patrón factory → reducir a ~35 líneas

**3.3 Dividir funciones de logging** (`complejidad.md`)
- `log_meal()` (70 líneas), `log_session()` (81 líneas): mezclan validación, cálculo, IO y persistencia
- Separar en funciones con responsabilidad única

---

### 🟢 Prioridad 4 — Limpieza menor sin riesgo

**4.1 Corregir nomenclatura** (`naming.md`)
- Renombrar `_404`, `_422`, `_500` a nombres descriptivos
- Renombrar `get_meal_alternative()` a `generate_meal_alternative()`
- Estandarizar `kcal_*` → `calories_*` en modelos
- Resolver mezcla español/inglés en constantes

**4.2 Eliminar código muerto** (`codigo_muerto.md`)
- Remover import `cast` de `app/api/routine.py:6`
- Decidir destino de `drop_tables()` en `database.py`

**4.3 Extraer helpers de user service** (`duplicados.md`)
- `extract_user_bio()`, `extract_weight_kg()`, `get_user_id()` — pequeños pero repetidos en 6+ archivos

**4.4 Deuda técnica menor** (`codigo_incompleto.md`)
- Implementar Redis cache en `food_aggregator_service.py` antes de escalar
- Agregar `@abstractmethod` a `BaseConnector`

---

## Estimación de Impacto por Limpieza

| Limpieza | Esfuerzo est. | Reducción de código | Impacto en mantenibilidad | Riesgo de cascada |
|----------|--------------|---------------------|--------------------------|-------------------|
| Contrato de error unificado | 3–5 días | ~50 líneas net | ⭐⭐⭐⭐⭐ Muy alto | ⚠️ Medio — requiere actualizar tests y frontend |
| Extraer templates IA | 4–6 horas | ~0 net (reorg.) | ⭐⭐⭐⭐ Alto | 🟢 Bajo — solo reorganización |
| Workflow Gemini base class | 1–2 días | ~200 líneas menos | ⭐⭐⭐⭐ Alto | ⚠️ Medio — lógica compartida |
| Decorador excepciones | 4–6 horas | ~50 líneas menos | ⭐⭐⭐ Medio | 🟢 Bajo |
| Dividir HTML generation | 1–2 días | ~0 net (reorg.) | ⭐⭐⭐⭐ Alto | 🟢 Bajo si tests pasan |
| Refactorizar exception setup | 2–3 horas | ~170 líneas menos | ⭐⭐⭐ Medio | 🟢 Muy bajo |
| Nomenclatura | 2–4 horas | ~0 net | ⭐⭐ Bajo-medio | 🟢 Bajo si se actualizan callers |
| Código muerto | 30 min | 3–5 líneas | ⭐ Bajo | 🟢 Muy bajo |

---

## Advertencias de Cambios con Efecto en Cascada

### ⚠️ 1. Estandarización del contrato de error
**Impacto en cascada:** El frontend (`frontend/src/services/api.ts`) puede estar parseando `detail` como string en todos los casos. Si el backend comienza a retornar `{"detail": ..., "error_code": ..., "error_type": ...}`, el frontend necesita actualizarse en paralelo. Coordinar con frontend antes de deployar.

### ⚠️ 2. Clase base de workflow Gemini
**Impacto en cascada:** Cualquier modificación del comportamiento de generación (timeouts, retry logic, status management) afectará tanto dietas como rutinas simultáneamente. Riesgo deseable a largo plazo, pero requiere tests comprehensivos antes del merge.

### ⚠️ 3. Renombres en `app/db/models.py`
**Impacto en cascada:** Los campos `kcal_*`, `met_*`, `bmr_bpm` son columnas de base de datos. Renombrarlos **requiere una migración de Alembic**. Si se hace sin migración, rompe en producción inmediatamente. No mezclar renombre de columna con renombre de atributo Python.

### ⚠️ 4. Mover validación a schemas Pydantic
**Impacto en cascada:** Si la validación se mueve a los schemas, los errores que hoy son `HTTPException` serán `RequestValidationError` manejados por FastAPI. El handler de `RequestValidationError` en `main.py` debe producir el mismo formato de respuesta esperado por el cliente.

### ⚠️ 5. Refactorizar `log_meal()` y `log_session()`
**Impacto en cascada:** Estas funciones tocan múltiples tablas de DB y tienen lógica de estado compleja. La refactorización es correcta pero requiere tests de integración completos antes de deployar.

---

## Estado General del Proyecto

| Dimensión | Estado | Comentario |
|-----------|--------|------------|
| Funcionalidad core | ✅ Completa | No hay funcionalidades incompletas críticas |
| Código muerto | ✅ Mínimo | Solo 2 elementos menores |
| Duplicación | ⚠️ Moderada | 10 categorías, ~500 líneas de código repetido |
| Templates/Prompts | ⚠️ Embebidos | 780 líneas embebidas en servicios |
| Complejidad | ⚠️ Alta localizada | 2 funciones HTML críticas de 169 y 279 líneas |
| Contratos de API | ❌ Inconsistente | 3 formatos de error, status codes contradictorios |
| Nomenclatura | ⚠️ Parcialmente inconsistente | 15 issues en 5 archivos |

**Conclusión:** El proyecto es production-ready en funcionalidad, pero requiere trabajo de ingeniería para escalar con mantenibilidad. El issue más urgente es estandarizar los contratos de error antes de que el frontend lo asuma como comportamiento definitivo.
