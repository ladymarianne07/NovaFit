# DAILY_CODE.md — Flujo diario de trabajo

> Este archivo es la **fuente de verdad del flujo de trabajo**. Antes de tocar código, leelo. Se actualiza cuando cambia el flujo, no cada sprint.

---

## Estrategia de ramas

- **`main`** = código estable que se deploya a producción. Solo recibe merges desde `refactor-2026-04-26-WIP` vía PR cuando un grupo de cards está listo y testeado.
- **`refactor-2026-04-26-WIP`** = rama de desarrollo activo. **Todos los commits del sprint van acá.** Tiene la base de `main` + el refactor parcial heredado del 2026-04-04 que se va a ir fixeando card por card.
- Antes de empezar a trabajar, asegurarse de estar parada en WIP: `git branch --show-current` debe devolver `refactor-2026-04-26-WIP`. Si no, `git switch refactor-2026-04-26-WIP`.

---

## Loop de trabajo

1. **Leer el tablero Trello** → https://trello.com/b/U72EdES8/novafitness
2. **Tomar la primera card de "Sprint actual"** que no esté en "In progress"
3. **Mover la card a "In progress"** (vía MCP de Trello)
4. **Trabajar la card** siguiendo:
   - Los **criterios de aceptación** que tiene cada card
   - Las **decisiones arquitectónicas existentes** (NO desviar de la estructura ya codificada — ver referencias abajo)
   - El plan documentado en la card (sección "Solución" o "Decisión")
5. **QA** según política (ver tabla abajo)
6. **Commitear** los cambios con mensaje descriptivo (referenciar el card si ayuda)
7. **Comentar en la card** lo hecho: commit hash, archivos tocados, observaciones
8. **Mover la card a "Done"** (o a "Review/Test" si necesita validación de la usuaria)
9. **Repetir desde el paso 2** mientras haya cards en "Sprint actual"

---

## Política de QA

Cuándo hacer pruebas y cómo:

| Tipo de cambio | QA requerido |
|---|---|
| Edits de docs, comentarios, formatting | ❌ Skip |
| Borrar archivos sueltos / `.gitignore` / chore | ❌ Skip |
| Cambios cosméticos UI sin lógica | ❌ Skip (hasta que arranque el frontend nuevo) |
| Auth, schemas, models, validaciones | ✅ Tests unitarios + curl/REST al endpoint |
| Cálculos numéricos (kcal, macros, BMR, TDEE, totales) | ✅ Tests unitarios con invariantes (ej: `4·p + 4·c + 9·f == target ± 1`) |
| Cambios en flujos de IA (Gemini) | ✅ Tests con mocks; verificar shape del JSON resultante |
| Cambios en UI con flujo crítico (login, log de comida, generar dieta/rutina) | ✅ MCP de Playwright — probar como usuario normal |
| Cambios cross-layer (back + front) | ✅ Tests por capa + Playwright si toca UI |

**No correr la suite completa** salvo cuando se toca core. Override sobre la regla original de `CLAUDE.md`, confirmado por la usuaria el 2026-04-26.

**Playwright se usa para UI core** (no para pulido visual). Ejemplo: si se cambia la lógica de log de comida, abrir el flujo en navegador, loguear una comida, verificar que macros suman correctamente, ver consola sin errores.

---

## Crear nuevas tareas

Si surge una tarea nueva durante una sesión (la usuaria pide algo nuevo, o aparece un bug colateral), **NO mezclar con la card actual**. Crear card nueva en Trello (lista `Backlog`) con:

- **Título** con prefijo emoji por tipo:
  - 🔧 bug — Bug funcional
  - 🔢 bug numérico — Bug que afecta fiabilidad de números (P0 por la propuesta de valor)
  - 🚀 infra — Deploy, CI, build
  - 🔒 security — Auth, permisos, sanitización
  - 📜 refactor — Refactor de estructura sin cambio funcional
  - 📜 docs — Documentación
  - 🧪 tests — Suite de tests / E2E
  - 🤖 feat — Nueva feature (especialmente IA)
  - 🎨 frontend — Cambio frontend (cuando arranque)
  - 🧹 chore — Higiene del repo
- **Descripción** markdown con:
  - **Contexto / problema** — qué está pasando hoy
  - **Solución sugerida** — opciones consideradas + decisión recomendada
  - **Criterios de aceptación** — checklist verificable
  - **Estimación** — horas o días
- **Labels** apropiados (prioridad + capa + categoría especial)

Usar el MCP de Trello (`add_card_to_list`) para crearla directamente.

---

## No desviar de la estructura existente

Antes de proponer "una mejor forma" para algo, **verificar primero** si choca con:

- `audit_reports/resumen.md` (rama `refactor-2026-04-26-WIP`) — define el plan de refactor con prioridades P1–P4
- `BACKEND_GUIDELINES.md` — convenciones del backend
- `FRONTEND_GUIDELINES.md` — convenciones del frontend
- `ARCHITECTURE.md`, `ARCHITECTURE_DIAGRAM.md` (rama WIP) — arquitectura macro
- Las cards ya creadas en Trello (otras pueden depender de la estructura actual)

Si el plan documentado tiene un trade-off mejor, **primero consultar a la usuaria** antes de cambiar el rumbo.

---

## Trello

- **Tablero:** https://trello.com/b/U72EdES8/novafitness
- **Listas:** Backlog → Sprint actual → In progress → Review/Test → Done
- **Labels:**
  - **Prioridad:** `P0` (rojo), `P1` (naranja), `P2` (amarillo)
  - **Capa:** `backend` (azul), `frontend` (violeta), `infra` (celeste), `tests` (verde), `docs` (rosa)
  - **Especiales:** `security` (negro), `numeric-reliability` (lima), `foundations-redesign` (sin color — cards que preparan el camino para el frontend nuevo de Claude Design)

---

## Referencias

- `CLAUDE.md` — instrucciones del proyecto para Claude Code (en rama WIP)
- `ARCHITECTURE.md` — arquitectura macro (en rama WIP)
- `audit_reports/resumen.md` — plan de refactor con checklist P1–P4 (en rama WIP)
- `BACKEND_GUIDELINES.md` / `FRONTEND_GUIDELINES.md` — convenciones por capa
- Memoria persistente en `~/.claude/projects/d--NovaFitness/memory/`
