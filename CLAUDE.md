# NovaFitness — Claude Instructions

## Before writing any code

1. Read `BACKEND_GUIDELINES.md` before making any backend changes (FastAPI, services, schemas, models).
2. Read `FRONTEND_GUIDELINES.md` before making any frontend changes (React, TypeScript, CSS).

## Backend testing requirements

Every new backend feature must include tests before the task is considered done:

- **Unit tests** — test each service method in isolation (see `BACKEND_GUIDELINES.md` → Testing Guidelines)
- **Integration tests** — test the full request/response cycle through the API endpoints
- Tests go in `app/tests/` following the existing naming pattern (e.g. `test_trainer_e2e.py`)
- Aim to cover: happy path, validation errors, authorization checks, and edge cases

## Frontend testing requirements

Every new frontend feature must include tests before the task is considered done:

- **Integration tests** — test the component renders correctly and behaves as expected (see `FRONTEND_GUIDELINES.md` → Component Testing Guidelines)
- Tests go in `frontend/src/tests/` following the existing naming pattern (e.g. `ComponentName.integration.test.tsx`)
- Aim to cover: correct rendering, user interactions, loading/error states, and role-based visibility where applicable
- Mock API calls and context providers as needed (follow the pattern in existing test files)

## After completing any feature or fix

Run the full regression suite and fix any failures before considering the task done:

```bash
# Backend
cd "c:\Users\Maru\OneDrive\Escritorio\NovaFitness" && python -m pytest app/tests/ -q

# Frontend
cd "c:\Users\Maru\OneDrive\Escritorio\NovaFitness\frontend" && npx jest --passWithNoTests
```

If a test fails due to your changes, fix it before finishing. Pre-existing failures (documented below) are exempt.

### Known pre-existing test failures (do NOT fix unless explicitly asked)

- `frontend/src/tests/Login.regression.test.tsx` — looks for `.animate-spin` CSS class that no longer exists in the codebase. Confirmed pre-existing via git history.
