# NovaFitness — Pointer

> Claude Code auto-carga este archivo al iniciar sesión. Es deliberadamente corto.
> El contenido vivo de instrucciones está bajo `docs/`.

## Antes de tocar código, leer en este orden

1. [`docs/DAILY_CODE.md`](docs/DAILY_CODE.md) — flujo diario (rama, loop Trello, política de QA)
2. [`docs/CLAUDE_INSTRUCTIONS.md`](docs/CLAUDE_INSTRUCTIONS.md) — qué cargar y reglas operativas

## Mapa rápido

| Necesito… | Voy a… |
|---|---|
| Entender la arquitectura | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) + [`docs/ARCHITECTURE_DIAGRAM.md`](docs/ARCHITECTURE_DIAGRAM.md) |
| Convenciones del backend | [`docs/BACKEND_GUIDELINES.md`](docs/BACKEND_GUIDELINES.md) |
| Patrones de testing | [`docs/TESTING.md`](docs/TESTING.md) |
| Manejo de errores | [`docs/ERROR_HANDLING.md`](docs/ERROR_HANDLING.md) |
| Glosario de dominio | [`docs/DOMAIN_GLOSSARY.md`](docs/DOMAIN_GLOSSARY.md) |
| Invariantes numéricas (la propuesta de valor) | [`docs/NUMERIC_RELIABILITY.md`](docs/NUMERIC_RELIABILITY.md) |
| ADRs (decisiones no obvias) | [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| Estado del refactor heredado | [`docs/REFACTOR_PLAN.md`](docs/REFACTOR_PLAN.md) |
| Setup local / deploy | [`docs/operacion/DEPLOYMENT.md`](docs/operacion/DEPLOYMENT.md) |

Frontend: convenciones siguen en [`FRONTEND_GUIDELINES.md`](FRONTEND_GUIDELINES.md) (root, fuera del scope de `docs/` por ahora).

## Reglas de oro (extracto)

- Trabajo activo va a `refactor-2026-04-26-WIP`. `main` solo recibe merges vía PR.
- Tras cualquier cambio de código relevante, **diff contra los docs**: si divergen, pausar y preguntar a la usuaria cuál es ground truth.
- Ante ambigüedad, **NUNCA asumir**: pausar y preguntar.
- Política de tests: skip suite completa cuando no se toca core (override del 2026-04-26 — detalle en `DAILY_CODE.md`).
