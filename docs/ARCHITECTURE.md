# NovaFitness — Backend Architecture

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy 2.x |
| Database | SQLite (dev) / PostgreSQL-ready |
| Validation | Pydantic v2 |
| Auth | JWT (HS256) + PBKDF2-SHA256 passwords |
| AI | Google Gemini 2.5 Flash |
| Nutrition APIs | USDA FDC, FatSecret, OpenFoodFacts |
| HTTP client | httpx (sync) |
| Tests | pytest |

---

## Directory layout

```
app/
├── main.py                  # Application factory, middleware, exception handlers, routes
├── config.py                # Settings (env vars via pydantic-settings)
├── constants.py             # Enums, app-wide constants
├── dependencies.py          # FastAPI DI: get_db, get_current_user, get_current_trainer
│
├── core/
│   ├── security.py          # JWT create/verify, PBKDF2 hashing
│   └── custom_exceptions.py # Domain exceptions → HTTP status mappings
│
├── db/
│   ├── database.py          # Engine, session factory, auto-migration on startup
│   ├── models.py            # All SQLAlchemy ORM models
│   ├── init_db.py           # create_tables() helper
│   └── workout_seed.py      # MET activity catalog seeding
│
├── api/                     # HTTP layer (routers) — thin, delegates to services
│   ├── auth.py
│   ├── users.py
│   ├── events.py
│   ├── nutrition.py
│   ├── workout.py
│   ├── routine.py
│   ├── diet.py
│   ├── trainer.py
│   ├── invite.py
│   └── notifications.py
│
├── routers/
│   └── food.py
│
├── services/                # Business logic — all state changes live here
│   ├── user_service.py
│   ├── biometric_service.py
│   ├── nutrition_service.py
│   ├── workout_service.py
│   ├── routine_service.py
│   ├── diet_service.py
│   ├── trainer_service.py
│   ├── notification_service.py
│   ├── skinfold_service.py
│   ├── progress_evaluation_service.py
│   ├── progress_timeline_service.py
│   ├── food_service.py
│   ├── food_aggregator_service.py
│   ├── food_parser.py
│   ├── ai_parser_service.py
│   ├── fatsecret_service.py
│   ├── usda_service.py
│   ├── portion_resolver_service.py
│   └── validation_service.py
│
├── schemas/                 # Pydantic request/response models (API contract)
└── models/                  # Internal Pydantic models (FoodEntry, FoodPortionCache)
```

---

## Database models

```
User ──────────────────────────────────────────────────────────┐
│  id, email, hashed_password, role (student|trainer)          │
│  age, gender, weight_kg, height_cm, activity_level           │
│  bmr_bpm, daily_caloric_expenditure                          │
│  objective, aggressiveness_level                             │
│  target_calories, protein_target_g, carbs_target_g,          │
│  fat_target_g, custom_target_*                               │
└──────────────┬───────────────────────────────────────────────┘
               │ 1:1
    ┌──────────┼──────────┬──────────────────────┬─────────────────────┐
    ▼          ▼          ▼                      ▼                     ▼
UserRoutine  UserDiet  DailyNutrition      WorkoutSession        SkinfoldMeasurement
  status       status    date, carbs/         blocks[]              body_fat_%
  routine_data diet_data  protein/fat         kcal_est              lean_mass_kg
  html_content html_content consumed/target
  current_     current_
  session_idx  meal_idx
               daily_consumed
               daily_overrides

WorkoutSession ──── WorkoutSessionBlock ──── ExerciseActivity
                      activity_id             met_low/med/high
                      duration_min            category
                      kcal_min/max/est        label_es

User ── TrainerStudent ── User (trainer)
         status

TrainerInvite (code, expires_at, used_by_user_id)

Notification (recipient_id, sender_id, type, is_read)

ExerciseDailyEnergyLog (user_id, log_date, exercise_kcal_*, net_kcal_est)

WorkoutCorrectionFactor (user_id, scope, factor)  ← per-user MET calibration

FoodPortionCache (normalized_name, unit_normalized, grams_per_unit, source)
```

---

## API endpoints reference

### Authentication `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Register user (student or trainer). Auto-calculates BMR/TDEE for students. |
| POST | `/auth/login` | — | Authenticate → JWT Bearer token |
| POST | `/auth/login-form` | — | OAuth2 password form (Swagger UI compatible) |
| POST | `/auth/logout` | Bearer | Client-side confirmation (stateless JWT) |

### Users `/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users/me` | Bearer | Full profile |
| PUT | `/users/me` | Bearer | Update profile + biometrics (auto-recalc BMR/TDEE) |
| PUT | `/users/me/biometrics` | Bearer | Biometrics only |
| POST | `/users/me/enable-self-use` | Bearer | Trainer activates personal use |
| PUT | `/users/me/objective` | Bearer | Set objective + aggressiveness → auto-calc macro targets |
| PUT | `/users/me/nutrition-targets` | Bearer | Custom macro overrides |
| GET | `/users/{id}/skinfold-history` | Bearer | Skinfold measurement history |
| POST | `/users/me/progress-evaluation` | Bearer | AI progress score + analysis |
| GET | `/users/me/progress-timeline` | Bearer | Progress over time |

### Nutrition `/nutrition`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/nutrition/macros` | Bearer | Daily consumed vs. target macros |
| POST | `/nutrition/meals` | Bearer | Log a meal (deprecated, use `/food/parse-and-log`) |
| GET | `/nutrition/meals` | Bearer | Daily meals grouped by type |

### Diet `/v1/diet`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/diet/generate` | Bearer | Generate AI diet (Gemini) → enriched with Fat Secret macros |
| POST | `/v1/diet/edit` | Bearer | Edit diet via natural language |
| GET | `/v1/diet/active` | Bearer | Get current diet plan |
| GET | `/v1/diet/current-meal` | Bearer | Next planned meal (auto-detects training vs rest day) |
| POST | `/v1/diet/log-meal` | Bearer | Mark meal complete/skip → advances tracker, updates DailyNutrition |
| POST | `/v1/diet/meals/alternative` | Bearer | Generate AI meal alternative (same macros ±ranges) |
| POST | `/v1/diet/meals/apply-alternative` | Bearer | Apply alternative (permanent or 24 h override) |
| POST | `/v1/diet/modify-meal` | Bearer | Add / remove food from a meal |

### Routines `/v1/routines`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/routines/upload` | Bearer | Upload PDF/image → parse with Gemini |
| POST | `/v1/routines/generate` | Bearer | Generate routine from intake form |
| POST | `/v1/routines/edit` | Bearer | Edit via natural language |
| GET | `/v1/routines/active` | Bearer | Get active routine |
| POST | `/v1/routines/log-session` | Bearer | Log session completion |
| POST | `/v1/routines/advance-session` | Bearer | Move to next session (wraps around) |

### Workout `/v1`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/sessions` | Bearer | Create workout session with blocks (MET-based calorie estimation) |
| GET | `/v1/days/{date}/energy` | Bearer | Daily energy totals (exercise + intake + net) |
| GET | `/v1/sessions` | Bearer | List sessions (paginated) |

### Food `/food`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/food/parse-and-calculate` | — | Free-text → Gemini parse → USDA calories |
| GET | `/food/search-multi` | — | Multi-source food search (USDA, FatSecret, OpenFoodFacts) |
| POST | `/food/parse-and-log` | Bearer | Parse text + log meal to DailyNutrition |

### Trainer `/trainer`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/trainer/invite` | Trainer | Get current invite code |
| POST | `/trainer/invite` | Trainer | Generate new invite code (7-day) |
| GET | `/trainer/students` | Trainer | List active students |
| GET | `/trainer/students/{id}` | Trainer | Full student profile |
| DELETE | `/trainer/students/{id}` | Trainer | Unlink student |
| PUT | `/trainer/students/{id}/biometrics` | Trainer | Update student biometrics |
| PUT | `/trainer/students/{id}/objective` | Trainer | Update student objective |
| PUT | `/trainer/students/{id}/nutrition-targets` | Trainer | Update student nutrition targets |
| GET | `/trainer/students/{id}/nutrition/macros` | Trainer | Student's macro progress |
| GET | `/trainer/students/{id}/skinfold-history` | Trainer | Student's skinfold history |

### Other

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/invite/accept` | Bearer | Accept trainer invite code |
| GET | `/events/` | Bearer | Activity timeline |
| POST | `/events/` | Bearer | Log event (append-only) |
| GET | `/notifications` | Bearer | Latest 50 notifications |
| PUT | `/notifications/{id}/read` | Bearer | Mark as read |

---

## Request lifecycle

```
HTTP Request
     │
     ▼
FastAPI route handler (app/api/*.py)
     │  validates request body via Pydantic schema
     │  injects: db Session, current_user (from JWT)
     │
     ▼
Service layer (app/services/*.py)
     │  all business logic lives here
     │  reads / writes via SQLAlchemy ORM
     │  calls external APIs (Gemini, USDA, FatSecret)
     │
     ▼
SQLAlchemy ORM → SQLite / PostgreSQL
     │
     ▼
Pydantic response model → JSON response
```

---

## Authentication flow

```
POST /auth/register
  └─ ValidationService.validate_user_data()
  └─ BiometricService.calculate_user_metrics()    ← BMR + TDEE
  └─ UserService.create_user()                    ← PBKDF2-SHA256 hash
  └─ Returns UserResponse (no token)

POST /auth/login
  └─ UserService.authenticate_user()             ← verify PBKDF2 hash
  └─ create_access_token(sub=user_id, exp=1yr)
  └─ Returns { access_token, token_type: "bearer" }

GET /protected-route
  └─ get_current_active_user()  ← dependency
       └─ OAuth2PasswordBearer reads Authorization header
       └─ jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
       └─ db.get(User, user_id_from_sub)
       └─ raises 401 if token invalid / user not found
```

---

## AI integration (Gemini)

All three AI flows use `httpx` synchronously against the Gemini REST API:

```
_call_gemini()          → 65536 output tokens  (diet / routine full generation)
_call_gemini_light()    → 4096  output tokens  (single meal alternative)
```

### Diet generation flow

```
POST /v1/diet/generate
  └─ _build_diet_generation_prompt(intake, free_text, user_bio, routine_data)
  └─ _call_gemini(prompt)
       └─ Gemini → raw JSON text
       └─ _extract_json()        ← strips markdown, trailing commas, escape fixes
       └─ json.loads() → dict
  └─ raw_data["training_days"] = intake.training_days
  └─ _enrich_diet_with_fatsecret(raw_data)    ← NEW: replace AI macros with real data
       └─ ThreadPoolExecutor(max_workers=8)
       └─ For each unique food name → FatSecret search_food_by_name()
       └─ _extract_grams_from_portion(portion)  ← e.g. "1 unidad (120g)" → 120.0
       └─ food.calories = (kcal_per_100g / 100) * grams
       └─ _recalculate_meal_totals()
  └─ _generate_diet_html(raw_data)
  └─ UserDiet.diet_data = raw_data
  └─ UserDiet.html_content = html
```

### Routine file parsing flow

```
POST /v1/routines/upload
  └─ file size / MIME type validation
  └─ base64 encode file bytes
  └─ Gemini multimodal request (file + system prompt)
  └─ _extract_json() → routine_data dict
  └─ _generate_routine_html(routine_data)
  └─ UserRoutine.routine_data = routine_data
```

---

## Nutrition tracking — two parallel systems

The system has two independent macro accumulators that must stay in sync:

| Store | Table / Field | Source of truth for |
|---|---|---|
| `DailyNutrition` | `daily_nutrition` table | Dashboard macro ring charts |
| `daily_consumed` | `user_diets.daily_consumed` JSON | Diet plan tracker internal state |

Both are written together when a planned meal is marked **complete**:

```python
# diet_service.py — log_meal(action='complete')
daily_consumed[today_str] += meal_macros        # ← diet plan tracker
NutritionService.get_or_create_daily_nutrition()
daily_nutrition.protein_consumed += meal_macros  # ← dashboard
```

`daily_consumed` resets automatically at midnight because `get_current_meal()` checks
`current_meal_date != today` and resets `current_meal_index = 0` on a new day.

---

## Calorie calculation (workouts)

```
kcal_est = weight_kg × MET × (duration_min / 60) × correction_factor

MET lookup:
  activity_key (e.g. "cardio_running") → ExerciseActivity row
  intensity ("low"|"medium"|"high")    → met_low / met_medium / met_high

correction_factor (WorkoutCorrectionFactor):
  scope "global"       → applies to all activities
  scope "category"     → applies to a category (e.g. "cardio")
  scope "activity_key" → applies to a specific exercise
  default = 1.0
```

---

## Macro target calculation (users)

```
User sets objective + aggressiveness_level (1–3)
  └─ BiometricService.calculate_and_store_objective_targets(user)

fat_loss:
  deficit = {1: 300, 2: 500, 3: 750} kcal
  target_calories = TDEE - deficit
  protein = weight_kg × 2.2 g/kg
  fat = 25–30% of target_calories
  carbs = remainder

muscle_gain:
  surplus = {1: 150, 2: 250, 3: 500} kcal
  protein = weight_kg × 1.8 g/kg
  carbs = 45–50% of target_calories
  fat = 25–35%

body_recomp:
  target_calories = TDEE - 150
  protein = weight_kg × 2.0 g/kg

maintenance:
  target_calories = TDEE
  protein = weight_kg × 1.6 g/kg

performance:
  surplus = 200 kcal
  carbs = 50–55%
```

---

## Auto-migration on startup

No Alembic. On `create_tables()` the app:

1. Runs `Base.metadata.create_all()` — creates any missing tables
2. Runs `ensure_schema_compatibility()` — detects missing columns via `sqlalchemy.inspect()` and executes `ALTER TABLE … ADD COLUMN`
3. Runs `seed_exercise_activities()` — inserts MET catalog if empty

Tracked columns (added automatically when missing):

```python
REQUIRED_USER_COLUMNS     = { "objective", "aggressiveness_level", "target_calories", ... }
REQUIRED_ROUTINE_COLUMNS  = { "source_type", "health_analysis", "intake_data", ... }
REQUIRED_DIET_COLUMNS     = { "daily_consumed", "daily_overrides", ... }
```

---

## Trainer–student flow

```
Trainer                              Student
  │                                     │
  POST /trainer/invite                  │
  ← { code: "XXXX", expires_at }        │
  │                                     │
  share code out-of-band ─────────────► │
                                        POST /invite/accept  { code }
                                        └─ TrainerStudent created (status=active)
                                        └─ Notification → trainer
  │
  GET /trainer/students
  ← [{ student_id, name, macros, routine_status, ... }]
  │
  PUT /trainer/students/{id}/biometrics
  └─ Updates student biometrics
  └─ Recalculates student BMR/TDEE
  └─ Notification → trainer (confirmation)
```

---

## Error handling

Global exception handlers in `main.py` map domain exceptions to HTTP codes:

| Exception | HTTP |
|---|---|
| `UserAlreadyExistsError` | 409 |
| `InvalidCredentialsError` | 401 |
| `BiometricValidationError` | 422 |
| `IncompleteBiometricDataError` | 400 |
| `TrainerOnlyError` | 403 |
| `InviteNotFoundError` | 404 |
| `InviteExpiredError` | 410 |
| `RoutineFileTooLargeError` | 413 |
| `RoutineInvalidFileTypeError` | 415 |
| `RoutineParsingError` / `DietParsingError` | 422 |
| `RoutineNotFoundError` / `DietNotFoundError` | 404 |
| Unhandled `Exception` | 500 |

---

## Environment variables

```ini
# App
APP_NAME=NovaFitness API
VERSION=1.0.0
DEBUG=False
APP_TIMEZONE=America/Argentina/Buenos_Aires

# Database
DATABASE_URL=sqlite:///./novafitness.db
# PostgreSQL: postgresql://user:password@host/novafitness

# JWT
SECRET_KEY=<secrets.token_urlsafe(32)>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=525600   # 1 year

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","https://your-frontend.com"]

# External APIs
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
USDA_API_KEY=...
FATSECRET_CLIENT_ID=...
FATSECRET_CLIENT_SECRET=...
```

---

## Swagger / interactive docs

The API exposes two built-in UIs (no extra setup needed):

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — interactive, try requests directly |
| `http://localhost:8000/redoc` | ReDoc — clean read-only reference |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3.x schema |

To authenticate in Swagger UI:
1. Call `POST /auth/login` → copy `access_token`
2. Click **Authorize** (top right) → paste token as `Bearer <token>`
3. All subsequent requests will include the header automatically
