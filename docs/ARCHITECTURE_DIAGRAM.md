# NovaFitness — Backend Connection Diagram

All diagrams use [Mermaid](https://mermaid.js.org/) syntax.
Render with: GitHub, VS Code extension "Markdown Preview Mermaid Support", or mermaid.live.

---

## 1. High-level component map

```mermaid
graph TB
    subgraph Client["Client (React PWA)"]
        FE[Frontend]
    end

    subgraph Backend["FastAPI Backend"]
        direction TB

        subgraph API["API Layer (app/api/ + app/routers/)"]
            A_auth[auth]
            A_users[users]
            A_nutrition[nutrition]
            A_diet[diet]
            A_routine[routine]
            A_workout[workout]
            A_food[food]
            A_trainer[trainer]
            A_events[events]
            A_invite[invite]
            A_notif[notifications]
        end

        subgraph Services["Service Layer (app/services/)"]
            S_user[UserService]
            S_bio[BiometricService]
            S_nutrition[NutritionService]
            S_diet[DietService]
            S_routine[RoutineService]
            S_workout[WorkoutService]
            S_food[FoodService]
            S_aggregator[FoodAggregatorService]
            S_trainer[TrainerService]
            S_notif[NotificationService]
            S_skinfold[SkinfoldService]
            S_progress[ProgressServices]
            S_portion[PortionResolverService]
        end

        subgraph DB["Database (SQLAlchemy + SQLite/PostgreSQL)"]
            M_user[(User)]
            M_diet[(UserDiet)]
            M_routine[(UserRoutine)]
            M_nutrition[(DailyNutrition)]
            M_workout[(WorkoutSession)]
            M_events[(Event)]
            M_trainer[(TrainerStudent / Invite)]
            M_notif[(Notification)]
            M_skinfold[(SkinfoldMeasurement)]
            M_cache[(FoodPortionCache)]
            M_activity[(ExerciseActivity)]
        end
    end

    subgraph External["External APIs"]
        E_gemini[Google Gemini 2.5 Flash]
        E_usda[USDA FoodData Central]
        E_fatsecret[FatSecret API]
        E_off[OpenFoodFacts]
    end

    FE -->|HTTP + JWT| API
    API --> Services
    Services --> DB
    S_diet --> E_gemini
    S_routine --> E_gemini
    S_food --> E_gemini
    S_diet -->|enrich macros| E_fatsecret
    S_food --> E_usda
    S_aggregator --> E_usda
    S_aggregator --> E_fatsecret
    S_aggregator --> E_off
    S_portion --> E_usda
    S_portion --> E_fatsecret
    S_portion --> E_off
```

---

## 2. Request lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as FastAPI Middleware
    participant R as Router (api/)
    participant D as Dependency (get_current_user)
    participant S as Service Layer
    participant DB as SQLAlchemy / DB
    participant EXT as External API

    C->>MW: HTTP Request + Authorization: Bearer <token>
    MW->>MW: CORS check
    MW->>R: Forward request
    R->>D: Inject dependencies
    D->>DB: SELECT User WHERE id=<sub from JWT>
    DB-->>D: User object
    D-->>R: current_user
    R->>R: Validate request body (Pydantic)
    R->>S: call service method(db, user_id, ...)
    S->>DB: ORM queries (SELECT / INSERT / UPDATE)
    S-->>EXT: httpx call (if needed: Gemini / USDA / FatSecret)
    EXT-->>S: JSON response
    S-->>R: Result object / dict
    R-->>C: JSON response (Pydantic serialized)
```

---

## 3. Diet plan generation flow

```mermaid
flowchart TD
    A[POST /v1/diet/generate] --> B[Build prompt\n_build_diet_generation_prompt]
    B --> C[_call_gemini\n65536 output tokens]
    C --> D[_extract_json\nstrip markdown, fix escapes]
    D --> E[json.loads → raw_data dict]
    E --> F[Inject training_days\ninto raw_data]
    F --> G[_enrich_diet_with_fatsecret]

    subgraph Enrich["Fat Secret enrichment (parallel)"]
        G --> H[Collect all food items\nfrom training_day + rest_day]
        H --> I[Extract unique food names]
        I --> J[ThreadPoolExecutor max_workers=8]
        J --> K1[search_food_by_name food_1]
        J --> K2[search_food_by_name food_2]
        J --> K3[search_food_by_name food_N]
        K1 & K2 & K3 --> L[Apply per-100g macros\n× grams / 100]
        L --> M[_recalculate_meal_totals\n_recalculate day totals]
    end

    M --> N[_generate_diet_html]
    N --> O[UserDiet.diet_data = raw_data\nUserDiet.html_content = html\nUserDiet.status = ready]
    O --> P[Return UserDietResponse]
```

---

## 4. Meal tracker daily flow

```mermaid
stateDiagram-v2
    [*] --> NewDay: midnight / first access

    NewDay: Reset\ncurrent_meal_index = 0\ncurrent_meal_date = today

    NewDay --> CheckDayType

    CheckDayType: Detect day type\n_get_spanish_weekday(today)\nvs training_days list
    CheckDayType --> TrainingDay: today ∈ training_days
    CheckDayType --> RestDay: today ∉ training_days

    TrainingDay --> ShowMeal: meals = training_day.meals[index]
    RestDay --> ShowMeal: meals = rest_day.meals[index]

    ShowMeal --> CheckOverride: daily_overrides[today][index]?
    CheckOverride --> UseOverride: yes → is_overridden=true
    CheckOverride --> UsePlanned: no

    UseOverride --> Display
    UsePlanned --> Display

    Display: GET /v1/diet/current-meal\nreturns meal + macros

    Display --> LogComplete: POST /log-meal action=complete
    Display --> LogSkip: POST /log-meal action=skip

    LogComplete --> UpdateMacros: daily_consumed += macros\nDailyNutrition += macros
    LogSkip --> Advance
    UpdateMacros --> Advance

    Advance: current_meal_index += 1

    Advance --> LastMeal: index >= total_meals - 1
    Advance --> ShowMeal: more meals remaining

    LastMeal: All meals done for today
    LastMeal --> [*]
```

---

## 5. Nutrition tracking — two systems

```mermaid
graph LR
    subgraph FreeText["Free-text meal logging"]
        FT[POST /food/parse-and-log\nnatural language input]
        FT --> Gemini[Gemini\nparse food items]
        Gemini --> USDA[USDA\ncalories per 100g]
        USDA --> DN1[DailyNutrition\n+= macros]
    end

    subgraph DietTracker["Diet plan meal completion"]
        DT[POST /v1/diet/log-meal\naction=complete]
        DT --> DC[daily_consumed\n+= meal macros]
        DT --> DN2[DailyNutrition\n+= meal macros]
    end

    DN1 --> Dashboard[Dashboard\nmacro ring chart]
    DN2 --> Dashboard
    DC --> DietUI[Diet module\ntracker state]
```

---

## 6. Authentication and authorization

```mermaid
flowchart TD
    A[Client sends request] --> B{Has Authorization header?}
    B -->|No| C{Is endpoint public?}
    C -->|Yes| D[Process request\nno user context]
    C -->|No| E[401 Unauthorized]

    B -->|Yes Bearer token| F[jwt.decode\nSECRET_KEY HS256]
    F -->|Invalid / expired| G[401 Unauthorized]
    F -->|Valid| H[Extract user_id from sub]
    H --> I[db.get User id=user_id]
    I -->|Not found| J[401 Unauthorized]
    I -->|Found| K{Is user active?}
    K -->|No| L[403 Forbidden]
    K -->|Yes| M{Is endpoint trainer-only?}
    M -->|Yes| N{user.role == trainer?}
    N -->|No| O[403 TrainerOnlyError]
    N -->|Yes| P[Inject current_user\nprocess request]
    M -->|No| P
```

---

## 7. Trainer–student relationship

```mermaid
sequenceDiagram
    participant T as Trainer
    participant API as FastAPI
    participant DB as Database
    participant S as Student

    T->>API: POST /trainer/invite
    API->>DB: INSERT TrainerInvite (code, expires_at=+7d)
    API-->>T: { code, expires_at }

    T-->>S: Share code (out-of-band: WhatsApp, email, etc.)

    S->>API: POST /invite/accept { code }
    API->>DB: SELECT TrainerInvite WHERE code=?
    DB-->>API: Invite record
    API->>API: Validate: not used, not expired
    API->>DB: INSERT TrainerStudent (trainer_id, student_id, status=active)
    API->>DB: UPDATE TrainerInvite used_by=student_id
    API->>DB: INSERT Notification (type=invite_accepted → trainer)
    API-->>S: 200 OK

    T->>API: GET /trainer/students
    API->>DB: SELECT User JOIN TrainerStudent WHERE trainer_id=?
    API-->>T: [StudentSummary, ...]

    T->>API: PUT /trainer/students/{id}/biometrics
    API->>DB: UPDATE User biometrics
    API->>API: Recalculate BMR + TDEE
    API->>DB: INSERT Notification (type=biometric_update → trainer)
    API-->>T: Updated student profile
```

---

## 8. Workout calorie estimation

```mermaid
flowchart LR
    A[POST /v1/sessions\nblocks array] --> B

    subgraph PerBlock["Per block"]
        B[activity_key + intensity\n+ duration_min + weight_kg]
        B --> C[SELECT ExerciseActivity\nWHERE activity_key=?]
        C --> D{intensity}
        D -->|low| E[met_low]
        D -->|medium| F[met_med]
        D -->|high| G[met_high]
        E & F & G --> H[kcal = weight × MET × duration_h]
        H --> I[× correction_factor\nWorkoutCorrectionFactor]
    end

    I --> J[WorkoutSessionBlock\nkcal_min / max / est]
    J --> K[SUM all blocks]
    K --> L[WorkoutSession\ntotal_kcal_est]
    L --> M[ExerciseDailyEnergyLog\nupsert for log_date]
```

---

## 9. Food macro resolution pipeline

```mermaid
flowchart TD
    A[User input text\ne.g. '2 huevos revueltos con tostada'] --> B[Gemini AI Parser\nfood_parser.py]
    B --> C[Structured items\nname + quantity + unit]
    C --> D{For each item}

    D --> E[Search USDA FDC\nby food name]
    E -->|found| F[Per-100g macros from USDA]
    E -->|not found| G[Search FatSecret\nby food name]
    G -->|found| H[Per-100g macros from FatSecret]
    G -->|not found| I[Search OpenFoodFacts]
    I -->|found| J[Per-100g macros from OpenFoodFacts]
    I -->|not found| K[Category fallback\ne.g. grain=350 kcal/100g]

    F & H & J & K --> L[PortionResolverService\nconvert unit → grams]
    L --> M[calories = macros_per_100g × grams / 100]
    M --> N[FoodParseCalculateResponse\nper item + totals]
```
