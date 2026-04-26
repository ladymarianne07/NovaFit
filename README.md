# NovaFitness

Aplicación de fitness personalizada con IA. Tracking extremo de calorías, macros, dieta y entrenamiento. Permite a usuarios registrar comidas/entrenamientos/rutinas y a entrenadores gestionar alumnos con un sistema de invitaciones.

📚 **Documentación completa: [`docs/README.md`](docs/README.md)**

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python · FastAPI · SQLAlchemy · PostgreSQL (Supabase) |
| IA | Google Gemini (parsing de alimentos, generación y edición de rutinas/dietas) |
| Nutrición externa | FatSecret API + USDA |
| Frontend | React 18 · TypeScript · Vite · CSS custom properties |
| Auth | JWT con hash PBKDF2-SHA256 (validez 1 año, decisión PWA-first) |
| Testing | pytest (backend) · Jest + Testing Library (frontend) |

---

## Correr localmente

```bash
# Backend
python -m venv .venv
# Windows: .venv\Scripts\activate · macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

- Frontend dev: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs

`.env` requerido: `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `FATSECRET_CLIENT_ID`, `FATSECRET_CLIENT_SECRET`, `USDA_API_KEY`. Setup detallado en [`docs/operacion/DEPLOYMENT.md`](docs/operacion/DEPLOYMENT.md).

---

## Tests

```bash
python -m pytest app/tests/ -q
cd frontend && npx jest --passWithNoTests
```

Política: no correr la suite completa salvo cambios core (override 2026-04-26). Ver [`docs/DAILY_CODE.md`](docs/DAILY_CODE.md).

---

## Módulos

- **Auth + biométricos** — registro con peso/altura/edad/sexo/actividad, JWT, roles `user`/`trainer`, invitación de alumnos
- **Nutrición** (`Comidas`) — ingreso por lenguaje natural (Gemini), búsqueda FatSecret + USDA, tracking de macros por comida
- **Entrenamiento** (`Mis Entrenos`) — log por IA, integración con rutina activa, balance calórico
- **Rutinas** (`Mi Rutina`) — generación por IA (intake form) + subida por archivo, edición por instrucción NL, visualizador HTML
- **Progreso** — evaluación periódica IA, timeline corporal, pliegues cutáneos
- **Trainer Dashboard** — vista de alumnos asignados con perfil + biométricos
- **Notificaciones** — bell con polling 30s

Detalle de cada módulo en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Ramas

- **`main`** — estable, deployable a producción
- **`refactor-2026-04-26-WIP`** — desarrollo activo (todos los commits del sprint van acá; PR a main cuando un grupo está listo)

Flujo de trabajo: [`docs/DAILY_CODE.md`](docs/DAILY_CODE.md).

---

## Estructura

```
NovaFitness/
├── app/                       # Backend FastAPI
│   ├── api/                   # HTTP routers (excepto food)
│   ├── core/                  # exception handlers, helpers, security
│   ├── db/                    # SQLAlchemy models + database
│   ├── routers/               # food (router fuera del patrón /v1/)
│   ├── schemas/               # Pydantic
│   ├── services/              # Business logic
│   ├── templates/             # AI prompts (extraídos de services)
│   ├── tests/                 # pytest
│   └── main.py
├── frontend/                  # React + TypeScript
└── docs/                      # 📚 documentación (ver docs/README.md)
```

---

## Seguridad

- PBKDF2-SHA256 para hash de password
- JWT con validez 1 año (decisión PWA, ver [`docs/DECISIONS.md`](docs/DECISIONS.md))
- CORS configurado para PWA
- Aislamiento por usuario en queries (siempre filtra por `current_user.id`)
- Auto-migración de schema en startup (`docs/BACKEND_GUIDELINES.md`)

---

## Diferenciador

**Fiabilidad numérica extrema** en macros, calorías y entrenamiento. Invariantes auditables (`4·p + 4·c + 9·f = target_calories ± 1`), conciliación entre fuentes (USDA / FatSecret / AI), trazabilidad por usuario. Ver [`docs/NUMERIC_RELIABILITY.md`](docs/NUMERIC_RELIABILITY.md).
