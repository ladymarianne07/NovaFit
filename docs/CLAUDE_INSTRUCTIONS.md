# CLAUDE_INSTRUCTIONS.md — Reglas operativas para Claude Code

> Cargar al iniciar sesión, junto con [`DAILY_CODE.md`](DAILY_CODE.md). Si entras a NovaFitness por primera vez en una sesión, leé estos dos antes de tocar nada.

---

## 1. Antes de cada sesión

1. Verificar la rama: `git branch --show-current` debe devolver `refactor-2026-04-26-WIP`. Si no, `git switch refactor-2026-04-26-WIP`. (Justificación en [`DAILY_CODE.md`](DAILY_CODE.md) → "Estrategia de ramas".)
2. Pull si te aviso, o si vas a abrir trabajo nuevo: `git pull origin refactor-2026-04-26-WIP`.
3. Verificar Trello (https://trello.com/b/U72EdES8/novafitness): cards en "Sprint actual" + "In progress".
4. Si no hay cards activas y la usuaria no te dio una directa, preguntar.

---

## 2. Política de tests (override del 2026-04-26)

| Tipo de cambio | QA |
|---|---|
| Edits de docs, comentarios, formatting | ❌ Skip |
| Borrar archivos sueltos / `.gitignore` / chore | ❌ Skip |
| UI cosmética sin lógica (mientras no haya frontend nuevo) | ❌ Skip |
| Auth, schemas, models, validaciones | ✅ Tests unitarios + curl/REST al endpoint |
| Cálculos numéricos (kcal, macros, BMR, TDEE, totales) | ✅ Tests con invariantes (ver [`NUMERIC_RELIABILITY.md`](NUMERIC_RELIABILITY.md)) |
| Cambios en flujos de IA (Gemini) | ✅ Tests con mocks; verificar shape del JSON resultante |
| Cambios en UI con flujo crítico | ✅ MCP de Playwright — usar como usuario normal |
| Cambios cross-layer | ✅ Tests por capa + Playwright si toca UI |

**No correr la suite completa** salvo cambio core. Esto **overridea** la política original que decía "correr la suite completa después de cada cambio".

**Tests pre-existentes EXENTOS** (no fixear salvo pedido explícito):
- `frontend/src/tests/Login.regression.test.tsx` — busca clase `.animate-spin` que ya no existe. Confirmado pre-existente vía git history.

---

## 3. Reglas de oro

### 3.1 Diff doc vs código tras cada cambio
Tras cualquier modificación de código de dominio (services, schemas, models, endpoints, contratos de error, lógica numérica), antes de cerrar la card hacer un **diff mental contra los docs relevantes**:

1. ¿Qué docs cubren la zona? (`ARCHITECTURE.md`, `BACKEND_GUIDELINES.md`, `DOMAIN_GLOSSARY.md`, `NUMERIC_RELIABILITY.md`, `ERROR_HANDLING.md`, etc.)
2. ¿El código nuevo coincide con lo que el doc dice?
3. **Si NO coincide**: pausar, presentar el diff a la usuaria, dejar que decida si el doc se actualiza o el código se ajusta.

NUNCA elegir silenciosamente. La doc no es info "que se actualiza si me acuerdo" — es **la spec**.

### 3.2 Pausar y preguntar
Ante cualquier ambigüedad o decisión no obvia (scope, arquitectura, trade-offs, datos del dominio, cambios destructivos), pausar y preguntar a la usuaria. NUNCA asumir.

Cuando aparecen 2+ preguntas, agruparlas y presentarlas con opciones concretas A/B/C cuando aplique.

### 3.3 No desviar de estructura existente
Antes de proponer "una mejor forma" para algo, verificar primero contra:

- [`REFACTOR_PLAN.md`](REFACTOR_PLAN.md)
- [`BACKEND_GUIDELINES.md`](BACKEND_GUIDELINES.md)
- [`ARCHITECTURE.md`](ARCHITECTURE.md) y [`DECISIONS.md`](DECISIONS.md)
- Las cards ya existentes en Trello

Si tu propuesta tiene un trade-off mejor, igual presentarlo a la usuaria antes de cambiar el rumbo.

### 3.4 No commitear a `main`
Todos los commits del sprint van a `refactor-2026-04-26-WIP`. `main` solo recibe merges vía PR cuando un grupo de cards está listo y testeado.

---

## 4. Cierre de card

Para considerar una card de Trello "Done":

1. Código modificado, testeado donde aplica.
2. Diff doc vs código verificado (regla 3.1).
3. Commit limpio en WIP con mensaje descriptivo.
4. Comentario en la card de Trello con: archivos tocados, criterios cubiertos, QA realizado, commit hash, hallazgos laterales.
5. Mover card a "Done" vía MCP de Trello (no Review/Test, salvo que requiera validación manual de la usuaria).

Si surge tarea nueva durante el trabajo, NO mezclar con la card actual: crear card nueva en Backlog vía MCP.

---

## 5. Setup técnico

- **Working dir:** `d:\NovaFitness`
- **Shell:** Git Bash (Unix syntax). PowerShell también disponible si hace falta.
- **Branch activo:** `refactor-2026-04-26-WIP`
- **Trello board:** [`https://trello.com/b/U72EdES8/novafitness`](https://trello.com/b/U72EdES8/novafitness) — usar MCP de Trello para todas las operaciones
- **Memoria persistente:** `~/.claude/projects/d--NovaFitness/memory/` — guardar feedback nuevo de la usuaria ahí

---

## 6. Si algo no cuadra

Si las instrucciones de este archivo o de los otros docs contradicen lo que ves en el código o lo que la usuaria te dice **en la sesión actual**:

1. La usuaria en la sesión actual gana.
2. Después aplicar regla 3.1 (diff doc vs código): pausar, preguntar, decidir si el doc tiene que actualizarse.
