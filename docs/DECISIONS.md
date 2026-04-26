# DECISIONS.md — Architecture Decision Records

> Cada decisión arquitectónica no obvia tiene un breve ADR acá. Si no entendés por qué algo es así, leer este archivo antes de "mejorar".
> Formato: **#NN — Título** · *Decision · Status · Date · Why · Trade-offs · Re-revisita si...*

---

## #1 — Auto-migration con `ALTER TABLE` en startup, no Alembic

**Decision:** Las migraciones de schema se hacen automáticamente en el startup de FastAPI vía `app/db/database.py`, comparando las columnas declaradas en SQLAlchemy contra el schema actual y agregando las que falten con `ALTER TABLE`.

**Status:** ✅ Vigente.

**Date:** 2026-02 (decisión de la creación del proyecto).

**Why:**
- Solo dev, sin equipo. Alembic es overhead innecesario.
- Deploy en Render single-process. No hay race conditions multi-worker (si las hubiera, esto habría que repensarlo).
- Cambios de schema son frecuentes y se quiere evitar el ciclo "edit model → generar migración → revisar → aplicar".
- Las columnas requeridas se declaran explícitamente en `REQUIRED_USER_COLUMNS`, `REQUIRED_ROUTINE_COLUMNS`, `REQUIRED_DIET_COLUMNS` en `database.py`. Esto sirve como contrato.

**Trade-offs:**
- ❌ No hay versionado del schema. Si rompemos algo en una migración, no hay rollback automático.
- ❌ Renombre de columnas no es soportado (solo agregar). Cualquier rename requiere intervención manual.
- ❌ Drop de columnas requiere intervención manual.
- ❌ Si dos workers arrancan simultáneamente con un schema desactualizado, ambos ejecutan `ALTER TABLE` → race condition. Hoy Render usa single-worker, mitigado.
- ✅ Velocidad de iteración alta.
- ✅ Un solo lugar (`database.py`) para entender qué columnas espera el sistema.

**Re-revisita si...** se suma equipo y/o multi-worker. La decisión de migrar a Alembic sería suficientemente importante para una card de Trello dedicada.

---

## #2 — JWT con expiración de 1 año

**Decision:** Los access tokens emitidos en login expiran en `525600` minutos (1 año). No hay refresh tokens.

**Status:** ✅ Vigente.

**Date:** ~2026-02.

**Why:**
- App es PWA. Forzar login frecuente rompe la experiencia de "abro la app y ya estoy adentro".
- Audiencia objetivo (entrenadores y atletas) usa la app a diario. Una sesión de meses es UX correcto para eso.
- No hay datos high-value que justifiquen seguridad estilo banco.

**Trade-offs:**
- ❌ Token comprometido = acceso por mucho tiempo. Mitigación: el token vive en localStorage del frontend (lo común en PWAs); rotar el `SECRET_KEY` invalida todos los tokens al instante.
- ❌ Si bloqueamos un usuario, su token sigue válido hasta que expire o cambiemos `SECRET_KEY`. No hay revocación granular.
- ✅ UX simple y predecible para PWA.

**Re-revisita si...** llegamos a launch público. El riesgo de credenciales filtradas crece y conviene refresh tokens + access tokens cortos. Cards posibles: "agregar refresh token flow" + "blacklist de JWTs revocados (Redis)".

---

## #3 — `FoodEntry` no tiene `user_id` (cache global, no histórico)

**Decision:** La tabla `food_entries` no tiene foreign key a `users`. Es un caché global de items parseados (texto + USDA/FatSecret resolved), compartido entre todos los usuarios.

**Status:** ✅ Vigente.

**Date:** ~2026-02.

**Why:**
- El propósito es **cachear el parsing+resolución** de "100g de banana" → `{usda_id, calories_per_100g, ...}`. El cálculo es independiente del usuario.
- Compartir el caché entre usuarios maximiza el hit rate.
- El histórico per-user de comidas vive en `DailyNutrition` y `Event(event_type=meal)`, NO en `FoodEntry`.

**Trade-offs:**
- ❌ Si un usuario edita un `FoodEntry` (no se permite hoy), afectaría a todos los usuarios. Por eso la tabla es read-only post-insert.
- ❌ No se puede preguntar "¿qué comidas parseó este usuario?" sin pasar por `Event` o `DailyNutrition`.
- ✅ Bajo storage cost (solo se persisten items únicos parseados, no per-user duplicados).

**Re-revisita si...** queremos histórico de "los últimos parseos del usuario X" como feature de UX. En ese caso conviene una tabla intermedia `user_food_lookups` con FK a `food_entries.id` y `user_id`.

---

## #4 — Dual registration de routers `/v1/`

**Decision:** Los routers que usan prefijo `/v1/` se registran **dos veces** en `main.py`: una sin prefijo extra (para la convención del backend) y otra con `prefix="/api"` (para producción detrás de proxies que no strip-ean `/api`).

**Status:** ⚠ Documentada como vigente. **Card #6 alinea el código actual** que perdió esta práctica en el refactor del 2026-04-26.

**Date:** Decisión heredada. Documentada formalmente el 2026-04-26.

**Why:**
- Vite (dev server) tiene un proxy `/api → http://localhost:8000` que strip-ea `/api`. En dev el backend ve `/v1/...`.
- En production, el frontend pega `/api/v1/...` directo al backend. Si el proxy de Render/Cloudflare no strip-ea, el backend tiene que responder a `/api/v1/...`.
- Doble registro es la mitigación más simple: el endpoint funciona en ambos paths.

**Trade-offs:**
- ❌ Costo cognitivo: dev nuevo se sorprende de ver el mismo endpoint dos veces en `main.py`.
- ❌ OpenAPI muestra cada endpoint dos veces (con y sin `/api`). Lo aceptamos.
- ✅ Cero cambios en el frontend o en config del proxy si se cambia de proveedor de hosting.

**Detalle de implementación:** ver `BACKEND_GUIDELINES.md` → "Register Router".

**Re-revisita si...** el frontend nuevo (Claude Design) decide pegar **siempre** sin prefijo `/api`, o si pasamos a un proxy que strip-ea `/api` consistentemente. En ese caso, eliminar la segunda registración. Hasta tanto, esta es la regla.

---

## #5 — Doble accumulator de macros consumidos (`DailyNutrition` + `UserDiet.daily_consumed`)

**Decision:** Hoy las calorías y macros consumidas por día se acumulan en **dos lugares simultáneamente**: la tabla `DailyNutrition` y el JSON `UserDiet.daily_consumed`.

**Status:** ⚠ **Conocida como problemática.** Card #7 del Backlog define la single source of truth.

**Date:** Heredada. Decisión a tomar formalmente en Card #7.

**Why (intent original, parcialmente extrapolado):**
- `DailyNutrition` (tabla SQL) — query rápido para el dashboard ("¿cuántos kcal llevo hoy?").
- `UserDiet.daily_consumed` (JSON) — flexibilidad para cargar el JSON entero del diet activo y mostrar progreso por comida del plan.

**Trade-offs:**
- ❌ Drift entre las dos fuentes. Confirmado: `delete_meal` y free-text logging solo tocan `DailyNutrition`.
- ❌ Doble escritura → más oportunidades de bug.
- ✅ Lectura del dashboard puede ser de un solo query SQL en vez de JSON parsing.

**Sugerencia para Card #7:** `DailyNutrition` queda como single source of truth para macros. `UserDiet.daily_consumed` se reduce a un flag por meal_index — `{date: {meal_index: True}}` — sin números, solo estado de completion. Pendiente confirmar.

**Re-revisita si...** Card #7 se cierra (lo cual debería pasar pronto).

---

## #6 — `Settings` con `extra=forbid` (heredado por default de pydantic-settings)

**Decision:** `app/config.py:Settings` no setea `extra` explícitamente; pydantic-settings default es `forbid`. Resultado: cualquier env var fuera de las declaradas hace fallar el startup.

**Status:** ⚠ **A cambiar.** Card #35 del Backlog.

**Date:** Heredada (default de la librería).

**Why (intent inferido):**
- Detectar typos en `.env` temprano. Si pongo `DATABSE_URL` en lugar de `DATABASE_URL`, el `forbid` lo agarra.

**Trade-offs:**
- ❌ Cualquier env var de OTRO proyecto en el shell rompe pytest (descubierto en Card #3 cuando un `TRELLO_API_KEY=...` espurio en `.env` hizo crashear toda la suite).
- ❌ Si en deploy se setean vars adicionales (ej: por la plataforma), el backend no arranca.

**Decisión sugerida en Card #35:** cambiar a `extra="ignore"` (estándar de apps que pueden recibir env vars de productos vecinos). Si queremos seguir cazando typos en VARIABLES DECLARADAS, podemos validar con un test que verifique el contenido del `.env`.

---

## #7 — Hash de password con PBKDF2-SHA256, no bcrypt

**Decision:** `app/core/security.py` usa PBKDF2-SHA256 (vía passlib) para hash de passwords.

**Status:** ✅ Vigente.

**Date:** ~2026-02. Confirmada al detectar contradicciones en docs viejos (que decían "bcrypt") en 2026-04-26.

**Why:**
- PBKDF2 es FIPS-compliant y está en stdlib de Python (no requiere lib externa).
- Para el threat model actual (PWA de fitness, no banco), PBKDF2 con buen iteration count es suficiente.
- bcrypt en passlib tiene quirks de compatibilidad con `bcrypt 4.x` (warnings molestos al validar passwords > 72 bytes — uno de los motivos por el que existe `truncate_password_if_needed`).

**Trade-offs:**
- ❌ bcrypt es más resistente a hardware especializado para crackeo. PBKDF2 es algo más débil contra GPUs.
- ✅ Sin lib externa, menos issues de versionado.

**Re-revisita si...** crece el threat model (login agresivo, target de phishing). Cambiar a bcrypt o argon2 en ese caso (pip install + passlib upgrade).

---

## TBDs (decisiones por confirmar)

> ⚠ Cada uno de estos requiere tu decisión cuando puedas leer la doc completa. Cuando confirmes uno, lo movemos arriba como ADR formal.

### TBD-A — ¿Migrar `Settings` a `extra="ignore"` (Card #35)?

Sugerencia: sí. Reduce fricción de dev y deploy sin perder nada significativo (typo detection se cubre con un test).

### TBD-B — ¿`UserDiet.daily_consumed` se reduce a flags de completion (Card #7)?

Sugerencia: sí. Single source of truth = `DailyNutrition`. Confirmar antes de implementar.

### TBD-C — ¿Reglas de redondeo formalizar?

Ver `NUMERIC_RELIABILITY.md` TBD-1 a TBD-3.

### TBD-D — ¿Política de macro priority FatSecret > USDA > OFF (Card frente a NUMERIC_RELIABILITY TBD-5)?

Confirmar.

### TBD-E — ¿auto-recompute `avg_kcal_per_training_session` cuando cambia el peso del usuario?

Hoy no se hace. Si el usuario sube/baja >2 kg, el avg de la rutina activa queda obsoleto. Card pendiente para decidir si auto-recompute en `update_user_biometrics` o esperar al próximo edit de rutina.

---

## Cómo agregar un ADR

1. Identificar que la decisión es **no obvia** (alguien razonable podría haber decidido distinto).
2. Escribir un ADR siguiendo el formato de arriba: Decision, Status, Date, Why, Trade-offs, Re-revisita si...
3. Numerar consecutivamente (`#NN`).
4. Si la decisión cambia con el tiempo, **agregar un nuevo ADR** que la supere y marcar el anterior como `Superseded by #MM`.
5. Si la decisión está pendiente, agregarla en la sección "TBDs" hasta que se confirme.
