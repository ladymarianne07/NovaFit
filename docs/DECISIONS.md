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

## #5 — `DailyNutrition` como single source of truth de macros consumidos; `UserDiet.completed_meals` como flags

**Decision:** Los macros consumidos por día se persisten **solamente** en la tabla `DailyNutrition`. El plan-tracking ("¿qué comidas del plan completé hoy?") usa flags en `UserDiet.completed_meals` (sin números). Reemplaza el ex-campo `daily_consumed` que tenía macros duplicados.

**Status:** ⚠ Pendiente de implementación. **Card #7 implementa.**

**Date:** Confirmada 2026-04-26.

**Why:**
- La duplicación entre `DailyNutrition` (tabla) y `UserDiet.daily_consumed` (JSON) producía drift: `delete_meal` y free-text logging solo escribían en `DailyNutrition`. Después de cualquier delete o log libre, los dos números divergían.
- La feature útil de `daily_consumed` ("¿qué del plan completé?") se mantiene con flags por meal_index. Los macros se reconstruyen en runtime desde el plan + overrides + flags si el frontend los necesita.
- Single source of truth elimina la posibilidad de drift por construcción.

**Estructura nueva:**
```json
"completed_meals": {
  "2026-04-26": [0, 2, 4]    // índices del array meals del plan
}
```

**Trade-offs:**
- ❌ Frontend tiene que computar "macros del plan completado" en runtime si quiere mostrar "completaste X kcal del plan hoy". Es trivial: `sum(plan.meals[i] for i in completed_meals[today])` con override-handling.
- ❌ Pérdida histórica del `daily_consumed` viejo (la usuaria confirmó que no necesita migración — DB se reseteará para testing).
- ✅ Drift imposible. Una sola escritura por meal-completion.
- ✅ Más limpio para entender ("¿cuánto comí hoy?" → DailyNutrition; "¿qué del plan?" → flags).

**Re-revisita si...** descubrimos un caso de uso que requiere el desglose de macros por meal completado en el storage (en lugar de runtime). Hoy ese caso no existe.

---

## #6 — `Settings` con `extra="ignore"` (cambia desde el default original `forbid`)

**Decision:** `app/config.py:Settings` usa `model_config = SettingsConfigDict(extra="ignore")` para tolerar env vars no declaradas.

**Status:** ⚠ Pendiente de implementación. **Card #35 implementa.**

**Date:** Confirmada 2026-04-26 (anterior comportamiento `forbid` superseded).

**Why:**
- El default `forbid` de pydantic-settings hace fallar el startup si el `.env` o el shell tienen alguna env var no declarada. En Card #3 esto rompió pytest entero porque alguien (probablemente otra sesión de Claude) pegó `TRELLO_API_KEY=...` en `.env` por error.
- El backend no debería caerse por contaminación del entorno de otro proyecto vecino.
- En deploy, plataformas como Render setean vars adicionales (`PORT`, `RENDER_*`) que no son del backend.

**Trade-offs:**
- ❌ Pierdes detección automática de typos en variables declaradas. Mitigación: agregar un test que verifique que el `.env` real tiene las variables que `Settings` espera.
- ✅ Robusto contra contaminación.
- ✅ Compatible con plataformas de deploy que setean vars extra.

**Re-revisita si...** descubrimos casos donde la tolerancia a vars extra esconde un bug real (ej: typo en variable crítica). En ese caso, considerar `extra="allow"` para permitir lectura via `model_extra`, o reforzar el test de `.env`.

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

## #8 — Trackear fibra como cuarto macro

**Decision:** El modelo nutricional incluye **fibra dietética como 4to macro** junto a proteína, carbs, grasa. Schemas, modelos, USDA/FatSecret integration y user targets se extienden para incluirla.

**Status:** ⚠ Pendiente de implementación. **Card #38 implementa.**

**Date:** 2026-04-26.

**Why:**
- USDA y FatSecret miden las calorías de un alimento descontando la fibra (Atwater modificado: ~2 kcal/g para fibra, no 4). El cálculo `4·prot + 4·carbs + 9·fat` que usamos hoy infla las calorías ~10% en alimentos con fibra moderada/alta.
- Sin fibra explícita, el invariante I-2 (suma de macros = calorías) **no se puede satisfacer** sin sacrificar la fidelidad biológica. Recalcular desde macros mintiéndole al usuario sobre la fibra es peor que aceptar inconsistencia visible.
- Track de fibra es estándar en apps fitness modernas (MyFitnessPal, Cronometer, MacroFactor). Permite features adicionales: objetivos de fibra, dietas keto con net carbs, alertas de bajo intake.

**Implementación (Card #38):**
- `USDAFoodResult`, `FatSecretFoodResult`, `FoodNormalized`, `ParsedFoodPayload` → agregar `fiber_per_100g` (default 0 si fuente no provee)
- `FoodEntry` → columna `fiber_g`
- `DailyNutrition` → columna `fiber_consumed`
- `User` → columna `fiber_target_g`
- `BiometricService` → calcular fiber target (default: 14 g por cada 1000 kcal según USDA recommendations)
- Diet generation prompt → incluir fibra como objetivo

**Trade-offs:**
- ❌ Cambios en schemas + DB + UI (esfuerzo concentrado, ~2-3 días).
- ❌ Si una fuente externa no provee fibra (raro), default 0 puede ser inexacto.
- ✅ Calorías biológicamente correctas (USDA directo) + invariante I-2 satisfecho.
- ✅ Habilita features futuras de fibra/keto/digestión.
- ✅ La app pasa de "trackeo de macros" a "trackeo serio de macros + fibra" — refuerzo del diferenciador.

**Invariante I-2 con fibra:**
```
4 · prot + 4 · (carbs - fiber) + 2 · fiber + 9 · fat  ≈  calories  ± 1 kcal
```

**Re-revisita si...** descubrimos un trade-off no anticipado. Card #38 incluye smoke tests para verificar que I-2 se cumple en tres alimentos índice (banana, lentejas, manzana) post-implementación.

---

## #9 — Redondeo entero universal en outputs visibles

**Decision:** Todo número numérico **visible al usuario** (calorías, macros en gramos) se redondea a **entero**, sin decimales. Cantidades intermedias no visibles (MET window, correction_factor) mantienen decimales.

**Status:** ⚠ Pendiente de implementación parcial. **Card #39 implementa.**

**Date:** 2026-04-26.

**Why:**
- Decimales en outputs visibles agregan ruido sin valor: "1850.5 kcal" vs "1851 kcal" no cambia la decisión del usuario, pero confunde.
- Consistencia: hoy hay redondeos arbitrarios entre módulos (1 decimal en BMR, 2 en macros consumidos, entero en target_calories). Unificar simplifica.
- El invariante I-1 (rebalanceo de carbs) ya funciona mejor con enteros porque los redondeos son determinísticos por bloque.

**Trade-offs:**
- ❌ Cambios en múltiples services + tests (auditoría de `round(x, N)` en el codebase).
- ❌ Cambios pequeños de UI (algunos componentes mostrarán "350" en lugar de "350.5").
- ✅ Output uniforme.
- ✅ Tests más simples (no `pytest.approx` para validar visibles).

**Excepción**: cantidades intermedias del cálculo físico mantienen decimales:
- MET window (`met_used_min`, `met_used_max`): 3 decimales
- `correction_factor`: 3 decimales

**Re-revisita si...** recibimos feedback de usuarios pidiendo precisión decimal en algún campo específico (ej: "yo controlo mi proteína al 0.5 g"). Hoy no es el caso.

---

## #10 — Auto-recompute al cambiar peso/biometricos

**Decision:** Cuando `update_user_biometrics` cambia el peso del usuario en **más de 2 kg**, se dispara recálculo automático de campos derivados que usen peso:

- `User.bmr_bpm`, `User.daily_caloric_expenditure`, `User.target_calories` y los `*_target_g` (esto **ya existe** vía `BiometricService.update_user_biometrics_with_recalculation`).
- **NUEVO:** `UserRoutine.routine_data["avg_kcal_per_training_session"]` para la rutina activa del usuario, si la hay.

**Status:** ⚠ Pendiente de implementación parcial. **Card #40 implementa la parte de routine.**

**Date:** 2026-04-26.

**Why:**
- El usuario tiene la expectativa razonable de que "si actualizo mi peso, todos mis números se actualizan". El patrón ya existe para targets nutricionales — extenderlo a la rutina cierra el círculo.
- Sin esto, el `avg_kcal` queda obsoleto silenciosamente: para María (peso 65 → 60 kg), su dieta de día de entreno seguiría dándole +358 kcal extras cuando su realidad serían +330 kcal. Pequeño pero suma con el tiempo.

**Threshold de 2 kg:**
- Cambios <2 kg suelen ser fluctuación normal (agua, fibra, etc.) — no merecen recalc constante.
- 2 kg representa ~5% de cambio en kcal estimadas (linear en peso) — perceptible.

**Lo que NO se auto-recalcula:**
- **Diet plan (`UserDiet.diet_data`)** — el plan de comidas en sí (lo que Gemini generó) NO se regenera automáticamente. Sería un Gemini call costoso que el usuario podría no querer (le cambiaría todas las comidas). Los **targets** sí se actualizan (vía la cadena existente), pero las **comidas específicas** del plan no.
- Para regenerar el plan de comidas, el usuario tiene que invocar explícitamente `POST /v1/diet/generate` (ya existe).

**Trade-offs:**
- ❌ Más código path para testear. Si el recálculo de routine.avg_kcal falla silenciosamente, el problema reaparece.
- ❌ Pequeña latencia adicional en `update_user_biometrics` (un cálculo más).
- ✅ "Just works" desde el punto de vista del usuario.
- ✅ Threshold evita ruido por fluctuaciones.

**Re-revisita si...** descubrimos que 2 kg es muy bajo (mucho recalc) o muy alto (la dieta queda obsoleta). Ajustar threshold via `WorkoutConstants.WEIGHT_CHANGE_RECOMPUTE_THRESHOLD_KG`.

---

## Cómo agregar un ADR

1. Identificar que la decisión es **no obvia** (alguien razonable podría haber decidido distinto).
2. Escribir un ADR siguiendo el formato de arriba: Decision, Status, Date, Why, Trade-offs, Re-revisita si...
3. Numerar consecutivamente (`#NN`).
4. Si la decisión cambia con el tiempo, **agregar un nuevo ADR** que la supere y marcar el anterior como `Superseded by #MM`.
5. Si la decisión está pendiente de implementación, marcar Status como ⚠ con la card correspondiente.
