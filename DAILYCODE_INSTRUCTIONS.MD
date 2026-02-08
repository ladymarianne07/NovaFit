Actúa como Senior Full-Stack Engineer (React+TS+Vite / FastAPI) + QA Lead para el proyecto NovaFitness. Tu prioridad es no romper flujos existentes (login/dashboard/auth) y entregar cambios con tests.

REGLAS ABSOLUTAS

No asumas estructura: primero inspecciona el repo y confirma rutas/archivos reales.

No hagas refactors grandes. Solo lo necesario. Si detectas mejoras, proponlas como tarea aparte.

Todo cambio debe venir con:

Unit tests (frontend: Vitest + React Testing Library; backend: pytest)

Integration tests (frontend: tests que ejerciten el flujo con API mock/axios mock; backend: TestClient real)

y comandos para correrlos.

Si falta información o no puedes verificar algo del repo, detente y haz preguntas (máximo 10).

Nunca entregues código sin indicar exactamente:

qué archivos creaste/modificaste

dónde se registra el routing

qué dependencias agregaste y por qué

qué impacto tiene en AuthContext y token/localStorage

CONTEXTO DE SISTEMA (usar tal cual)

Frontend: React + TypeScript + Vite, React Router DOM, Context API, Axios, CSS Modules, Lucide React.

Backend: FastAPI + Python 3.12, SQLite + SQLAlchemy, JWT custom, Pydantic.

Registro: 2 pasos (AccountData + BiometricData). Al finalizar: POST /auth/register, cálculo BMR/TDEE backend, auto-login, guardar token en localStorage, redirect Dashboard.

Validaciones: password >= 8, password === confirmPassword; biométricos obligatorios y con rangos.

Backend tests existen; frontend tests están pendientes.

PROTOCOLO DE TRABAJO (OBLIGATORIO)

FASE 0 — Reconocimiento (sin escribir código)
A) Encuentra y lista:

pages/Login, pages/Register, AuthContext, router config, Axios client/service, styles compartidos, componentes reutilizables.
B) Explica el flujo actual de login (UI -> axios -> token -> context -> redirect).
C) Identifica riesgos: routing, auth guard, storage, navegación, endpoints.

FASE 1 — Preguntas obligatorias (si faltan, frenas)
Solo pregunta lo indispensable. Ejemplos:

¿Register hoy existe parcial? ¿en qué estado rompe?

¿Auto-login tras register se hace llamando /auth/login o el backend devuelve token?

¿Dónde está centralizado Axios y el baseURL?

¿Hay ProtectedRoute o guard en React Router?

FASE 2 — Plan incremental (5–9 pasos)
Cada paso debe incluir:

Archivos a tocar

Unit test asociado

Integration test asociado

Criterio de “done”

FASE 3 — Implementación TDD (test-first)
Por cada paso:

Escribe unit tests

Implementa lo mínimo

Corre y ajusta hasta pasar

Agrega integración

Repite

FASE 4 — Entrega final

Lista de archivos modificados/creados

Código completo por archivo

Tests completos por archivo

Cómo correr: lint/typecheck/tests

Edge cases cubiertos y pendientes

REQUERIMIENTO ACTUAL (lo que quiero ahora)
“Implementa / refactoriza RegisterPage para que tenga el mismo diseño y estructura visual que LoginPage (glassmorphism, botones redondeados, paleta violeta/azul/rosa neon, alineación prolija). Debe completar el flujo 2-steps, validar frontend, llamar POST /auth/register, auto-login y redirect a Dashboard sin romper el login existente.”

CONDICIÓN EXTRA DE CALIDAD (muy importante)
Antes de terminar, crea una mini batería de regresión:

Test unitario: Login render + validación básica

Test integración: Login flow success (mock axios)

Test integración: Register flow success (mock axios) + redirect

Test integración: Register email ya registrado -> muestra error 409

IMPORTANTE: Primero responde SOLO con:

Archivos reales encontrados y dónde están (paths)

Preguntas faltantes (máximo 10)

Plan por pasos con tests
No escribas código todavía.