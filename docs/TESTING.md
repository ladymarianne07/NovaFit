# TESTING.md — Convenciones de testing

> Patrones reales que usa el proyecto. Si tu test no encaja con estos patrones, probablemente estés inventando — pausar y revisar.

---

## Stack

- **pytest** — runner único
- **fastapi.testclient.TestClient** — cliente HTTP en proceso
- **SQLAlchemy** con SQLite en memoria/disco para tests (DB de test recreada por test)
- **monkeypatch** (pytest fixture) — para mockear dependencias externas

---

## Política de QA (override del 2026-04-26)

| Tipo de cambio | QA |
|---|---|
| Edits de docs, comentarios, formatting | ❌ Skip |
| Borrar archivos sueltos / `.gitignore` / chore | ❌ Skip |
| UI cosmética sin lógica | ❌ Skip (mientras no haya frontend nuevo) |
| Auth, schemas, models, validaciones | ✅ Tests unitarios + curl/REST al endpoint |
| Cálculos numéricos (kcal, macros, BMR, TDEE, totales) | ✅ Tests con invariantes (ver [`NUMERIC_RELIABILITY.md`](NUMERIC_RELIABILITY.md)) |
| Cambios en flujos de IA (Gemini) | ✅ Tests con mocks; verificar shape del JSON resultante |
| Cambios en UI con flujo crítico | ✅ MCP de Playwright |
| Cambios cross-layer | ✅ Tests por capa + Playwright si toca UI |

**No correr la suite completa** salvo cambio core. Detalle en [`DAILY_CODE.md`](DAILY_CODE.md) y [`CLAUDE_INSTRUCTIONS.md`](CLAUDE_INSTRUCTIONS.md).

**Tests pre-existentes EXENTOS** (no fixear salvo pedido explícito):
- `frontend/src/tests/Login.regression.test.tsx` — busca `.animate-spin` clase CSS que ya no existe
- `app/tests/test_nutrition_daily_reset.py::test_daily_nutrition_resets_next_day_but_previous_day_persists`
- `app/tests/test_nutrition_meals.py::test_delete_meal_rolls_back_totals_when_event_totals_are_missing`

Los últimos 2 son flakes intermitentes detectados el 2026-04-26 que se cubrirán con e2e Playwright cuando arranque ese trabajo.

---

## Estructura

```
app/tests/
├── conftest.py                              ← fixtures compartidos
├── test_auth.py                             ← registro, login
├── test_users.py                            ← endpoints de /users/*
├── test_events.py                           ← timeline append-only
├── test_food_endpoint.py                    ← /food/* endpoints
├── test_food_parser_meals.py                ← FoodService — parsing de texto libre
├── test_food_aggregator_service.py          ← FoodAggregatorService — multi-source ranking
├── test_ai_parser_service.py                ← AIParserService (Gemini food parser)
├── test_routine_generate.py                 ← RoutineService.generate_from_text + log_session
├── test_routine_avg_kcal.py                 ← (Card #10) avg_kcal_per_training_session
├── test_nutrition_meals.py                  ← NutritionService.log_meal / delete_meal
├── test_nutrition_daily_reset.py            ← DailyNutrition rollover diario
├── test_objective_calculations.py           ← BiometricService.calculate_objective_targets
├── test_user_recalculation_triggers.py      ← BMR/TDEE recálculo en updates
├── test_skinfolds.py                        ← SkinfoldService
├── test_progress_evaluation_endpoint.py     ← /users/me/progress-evaluation
├── test_progress_evaluation_service.py      ← progress_evaluation_service
├── test_progress_timeline_endpoint.py       ← /users/me/progress/timeline
├── test_portion_resolver_service.py         ← PortionResolverService
├── test_usda_similarity.py                  ← USDA ranking semántico
└── test_trainer_e2e.py                      ← flujo completo trainer-student
```

**Naming**:
- Tests de endpoints HTTP → `test_<modulo>_endpoint.py` o `test_<flujo>.py`
- Tests de service unitarios → `test_<service_name>.py`
- Tests E2E → `test_<flujo>_e2e.py`

Una test function = un escenario nombrado en estilo `test_<sujeto>_<comportamiento_esperado>`. Ej: `test_get_all_users_route_removed`, `test_compute_avg_kcal_single_session_60min_70kg`.

---

## Fixtures disponibles

Todas vienen de [`app/tests/conftest.py`](../app/tests/conftest.py).

### `client` — TestClient sin autenticar

```python
def test_unauth_endpoint_returns_401(client):
    response = client.get("/v1/diet/active")
    assert response.status_code == 401
```

Crea/destroya las tablas en cada test (test DB es SQLite en `./test.db`). Seed `exercise_activities` automático.

### `authed_client` — TestClient ya con Bearer token

```python
def test_authed_endpoint(authed_client):
    response = authed_client.get("/v1/diet/active")
    assert response.status_code == 200  # o 404 si no hay diet
```

Internamente: registra usuario con `test_user_data`, hace login, fija `Authorization: Bearer <token>` como header default.

### `test_user_data` — payload válido para registro

```python
{
    "email": "test@example.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User",
    "gender": "male",
    "weight": 70.0,
    "height": 175.0,
    "age": 25,
    "activity_level": 1.5,
}
```

Para variantes (otro peso, otro objective), usar `**test_user_data, "weight": 60.0` en lugar de copiar el dict entero.

### `db_session` — sesión SQLAlchemy directa para tests de service

```python
def test_helper_directly(db_session):
    avg = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data={...}, weight_kg=70
    )
    assert avg == ...
```

Útil cuando el test necesita pegarle al service sin pasar por HTTP.

### `monkeypatch` (pytest) — para mockear dependencias externas

Ver patrones específicos en sección "Mocks" abajo.

---

## Patrones de mocking

### Gemini (AI calls)

`monkeypatch` la función específica que hace el call HTTP. Ej:

```python
def test_routine_generation(authed_client, monkeypatch):
    def fake_gemini_call(prompt: str) -> dict:
        return {
            "title": "Test routine",
            "sessions": [...],
            # estructura mínima válida del schema de routine
        }
    monkeypatch.setattr(
        "app.services.routine_service.RoutineService._call_gemini_text",
        fake_gemini_call,
    )
    # ...
```

**Por qué este path específico**: Gemini calls viven en métodos `_call_gemini_*` de cada service. Mockear el service method en lugar del HTTP/SDK aísla el test de la lib externa.

### FatSecret

```python
from app.services.fatsecret_service import FatSecretFoodResult

def fake_fatsecret_search(_normalized_name: str):
    return FatSecretFoodResult(
        food_id="fs-123",
        description="Banana",
        calories_per_100g=89.0,
        carbs_per_100g=22.8,
        protein_per_100g=1.1,
        fat_per_100g=0.3,
        serving_size_grams=None,
    )

monkeypatch.setattr(
    "app.services.food_service.search_fatsecret_food_by_name",
    fake_fatsecret_search,
)
```

### USDA

Simétrico a FatSecret:

```python
from app.services.usda_service import USDAFoodResult

def fake_usda_search(_normalized_name: str):
    return USDAFoodResult(
        fdc_id="09040",
        description="Bananas, raw",
        calories_per_100g=88.0,
        ...
    )

monkeypatch.setattr(
    "app.services.food_service.search_food_by_name",
    fake_usda_search,
)
```

### Food parser (Gemini para parsing de texto a items)

```python
from app.schemas.food import ParsedFoodPayload

def fake_parse_food_input(_text: str):
    return [ParsedFoodPayload(name="banana", quantity=100, unit="grams")]

monkeypatch.setattr(
    "app.services.food_service.parse_food_input",
    fake_parse_food_input,
)
```

### Excepciones internas (forzar bug interno → 500)

```python
def boom(self, *_args, **_kwargs):
    raise RuntimeError("simulated internal failure")

monkeypatch.setattr(UserService, "update_user_objective", boom)

# Luego: con TestClient default (raise_server_exceptions=True),
# el RuntimeError propaga al test:
with pytest.raises(RuntimeError, match="simulated internal failure"):
    authed_client.put("/users/me/objective", json={...})
```

> En producción, el handler global `Exception` en `main.py` convierte cualquier `RuntimeError` no capturado a 500 con shape canónica. El test verifica que **NO hay un `try/except` que silencie la excepción** — propagación = no silenciamiento.

---

## Patrones de assertion

### Tests de endpoint HTTP

```python
response = authed_client.post("/v1/diet/generate", json={...})
assert response.status_code == 201
data = response.json()
assert data["status"] == "ready"
assert "diet_data" in data
```

### Tests de invariantes numéricas

```python
# Para el invariante 4·p + 4·c + 9·f ≈ target_calories:
total_kcal = 4 * data["protein_g"] + 4 * data["carbs_g"] + 9 * data["fat_g"]
assert abs(total_kcal - data["target_calories"]) <= 1
```

```python
# Para escalado lineal (peso × MET × hora):
avg_50 = compute(weight_kg=50)
avg_100 = compute(weight_kg=100)
assert avg_100 == pytest.approx(avg_50 * 2, rel=0.01)
```

### Tests de error HTTP

```python
response = client.get("/v1/diet/active")  # sin auth
assert response.status_code == 401

response = authed_client.put("/users/me/objective", json={"aggressiveness_level": 99})
assert response.status_code == 422  # Pydantic rechaza
```

---

## Cuándo crear un test nuevo

- Cualquier nuevo endpoint → test de happy path + de error de validación + de error de auth
- Nuevo método de service con lógica numérica → test que pin la fórmula con valores fijos
- Nuevo invariante → test que lo verifique para un set de inputs (no solo el caso obvio)
- Nuevo bug arreglado → test de regresión que falla sin el fix

**No crear tests por crear**: si el comportamiento ya está cubierto por un test existente cercano, ampliar el test existente con un caso más en lugar de duplicar setup.

---

## Cómo correr los tests

```bash
# Todo el backend (~90 segundos)
python -m pytest app/tests/ -q

# Un archivo específico
python -m pytest app/tests/test_routine_avg_kcal.py -v

# Un test específico
python -m pytest app/tests/test_users.py::test_get_all_users_route_removed -v

# Solo los que matchean un nombre (substring)
python -m pytest app/tests/ -k "avg_kcal" -v
```

> Política: para cards que no tocan core, **NO correr la suite completa** — solo los tests del dominio afectado. Ver `CLAUDE_INSTRUCTIONS.md`.

---

## Convenciones implícitas heredadas (no rompas)

- **No usar `--no-cov` ni configurar coverage threshold** — el proyecto no tiene política formal de cobertura, todavía.
- **No agregar tests que dependan de redes reales** (Gemini, USDA, FatSecret) — siempre mockear.
- **No usar `time.sleep` ni esperas reales** en tests — tiempo se mockea con monkeypatch o se usa fechas fijas.
- **Cleanup de DB lo hace el fixture `client`** — no agregar `db.commit()` final en tests.
- **Usar `pytest.approx` para floats** — nunca `==` directo en flotantes.
