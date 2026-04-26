# NovaFitness — Documentación

Esta carpeta es el **cerebro del proyecto backend**. Toda decisión, convención y patrón vive acá.

> Si estás entrando por primera vez (humano o Claude), arrancá por **[`DAILY_CODE.md`](DAILY_CODE.md)**.

---

## Mapa por audiencia

### Si vas a tocar código (Claude o dev humano)

1. **[`DAILY_CODE.md`](DAILY_CODE.md)** — flujo diario: qué rama, loop con Trello, política de QA, cómo crear nuevas tareas
2. **[`CLAUDE_INSTRUCTIONS.md`](CLAUDE_INSTRUCTIONS.md)** — reglas operativas: tests, sync doc-código, no-asumir, cierre de cards
3. **[`ARCHITECTURE.md`](ARCHITECTURE.md)** + **[`ARCHITECTURE_DIAGRAM.md`](ARCHITECTURE_DIAGRAM.md)** — arquitectura macro (capas, modelos, request lifecycle, AI flow)
4. **[`BACKEND_GUIDELINES.md`](BACKEND_GUIDELINES.md)** — convenciones backend (clean code, layers, naming, error handling, performance, security, SQLAlchemy sync, dual routing)

### Si vas a tocar un dominio específico

- **[`DOMAIN_GLOSSARY.md`](DOMAIN_GLOSSARY.md)** — glosario de términos del backend (`daily_consumed` vs `DailyNutrition`, `intake_data`, `aggressiveness_level`, MET intensity, `WorkoutCorrectionFactor`, etc.)
- **[`NUMERIC_RELIABILITY.md`](NUMERIC_RELIABILITY.md)** — invariantes numéricas (la propuesta de valor del producto): redondeo, reconciliación, fuentes de verdad
- **[`ERROR_HANDLING.md`](ERROR_HANDLING.md)** — contrato de errores: jerarquía, cuándo lanzar qué, shape canónica, cómo agregar nuevos

### Si vas a entender por qué algo es así (decisiones)

- **[`DECISIONS.md`](DECISIONS.md)** — ADRs: por qué no Alembic, por qué `FoodEntry` sin `user_id`, por qué JWT 1 año, por qué dos accumulators de macros, etc.
- **[`REFACTOR_PLAN.md`](REFACTOR_PLAN.md)** — síntesis del audit del 2026-04-04 con estado actual ✅/🟡/❌ y conexión con cards de Trello

### Si vas a escribir tests

- **[`TESTING.md`](TESTING.md)** — convenciones reales del proyecto: estructura de tests, fixtures (`client`, `authed_client`, `db_session`, `test_user_data`), cómo se mockea Gemini/FatSecret/USDA, override de "no correr suite completa"

### Si vas a hacer setup local o deploy

- **[`operacion/DEPLOYMENT.md`](operacion/DEPLOYMENT.md)** — instalación local (Windows), variables de entorno, deploy a Render / Vercel, troubleshooting

---

## Convenciones de la docs

- **Idioma:** español de Argentina para el contenido conceptual; inglés para citas de código y nombres técnicos.
- **Citas de código:** formato `archivo:línea` (ej: `app/api/diet.py:215`). Usar links de markdown cuando sea posible: `[archivo.py:42](archivo.py#L42)`.
- **Cuando un doc se contradice con el código:** ver regla en [`CLAUDE_INSTRUCTIONS.md`](CLAUDE_INSTRUCTIONS.md) sección 3.1 — pausar, presentar diff, dejar que la usuaria decida.
- **TBDs explícitos:** marcar con `> ⚠ TBD: <pregunta>` para que aparezcan resaltados al revisar.
- **No reintroducir** carpetas tipo `audit_reports_legacy/` — extender `REFACTOR_PLAN.md` con nuevas auditorías.

---

## Qué NO está acá (y dónde está)

- **Frontend conventions** — siguen en `FRONTEND_GUIDELINES.md` en el root. Cuando arranque el rediseño con Claude Design, se decide si se mueve a `docs/` o se queda separado.
- **Memoria de sesión / preferencias de usuaria** — `~/.claude/projects/d--NovaFitness/memory/` (fuera del repo, persiste entre sesiones).
- **Operativa de la usuaria como entrenadora** (prompts manuales que usaba con clientes vía claude.ai) — eliminados el 2026-04-26, ya no se usan.

---

## Cómo evolucionar la docs

- Crear cards de Trello para cualquier doc que quieras agregar/modificar — etiqueta `docs`.
- Si un cambio de código afecta a un doc, actualizalo en el mismo PR (ver regla 3.1 de `CLAUDE_INSTRUCTIONS.md`).
- Antes de eliminar un doc, confirmar con la usuaria.
