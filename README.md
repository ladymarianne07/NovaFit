# NovaFitness

Aplicación de fitness personalizada con IA. Permite a usuarios registrar comidas, entrenamientos y rutinas, y a entrenadores gestionar alumnos con un sistema de invitaciones.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python · FastAPI · SQLAlchemy · PostgreSQL (Supabase) |
| IA | Google Gemini (parsing de alimentos, generación y edición de rutinas) |
| Nutrición externa | FatSecret API + USDA |
| Frontend | React 18 · TypeScript · Vite · CSS custom properties |
| Auth | JWT (access + refresh tokens) |
| Testing | pytest (backend) · Jest + Testing Library (frontend) |

---

## Correr localmente

### Backend

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Variables de entorno requeridas: `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `FATSECRET_CLIENT_ID`, `FATSECRET_CLIENT_SECRET`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### Tests

```bash
# Backend
python -m pytest app/tests/ -q

# Frontend
cd frontend && npx jest --passWithNoTests
```

Falla pre-existente conocida y exenta: `Login.regression.test.tsx` (clase CSS `.animate-spin` ya no existe).

---

## Módulos implementados

### Autenticación
- Registro con datos biométricos (peso, altura, edad, sexo, nivel de actividad)
- Login JWT con refresh automático en cada recarga
- Roles: `user` y `trainer`
- Sistema de invitación de alumnos por código único (trainers)

### Nutrición — `Comidas`
- Ingreso por lenguaje natural (IA Gemini) con modal de confirmación antes de registrar
- Búsqueda en FatSecret + USDA con ranking de relevancia
- Historial diario por fecha con carrusel swipeable
- Cálculo de macros: proteínas, carbohidratos, grasas, calorías por comida (desayuno, almuerzo, cena, snack)

### Entrenamiento — `Mis Entrenos`
- **Botón "Ingresar entreno por IA"**: gradient cyan, full width; parsea texto libre en español → bloques actividad + duración + intensidad
- **Bottom sheet modal**: si hay rutina activa y no fue completada, pregunta si el nuevo entreno reemplaza la sesión del día o es extra (evita doble conteo de calorías)
- **Card "Próximo entreno"**: muestra la sesión de rutina del día con pills de duración / kcal / intensidad y toggle de completado
- **Toggle "Marcar como completado"**: al activarlo, descuenta las kcal de la rutina del balance diario visualmente
- **Lista de entrenamientos del día**: items con tags `Rutina` (cyan) / `IA` (violeta) y botón de eliminar — reemplaza el carrusel anterior
- **Card "Calorías del día"**: Ingeridas / Ejercicio / Neto en una sola card; Neto en cyan si positivo, verde neón (`#39ff14`) si quemó más de lo que ingirió
- Empty state con CTA hacia Mi Rutina si no hay rutina activa

### Rutinas — `Mi Rutina`
- Generación por IA con formulario de intake: objetivo, duración, condiciones de salud, lesiones (requerido), equipamiento, experiencia, frecuencia, duración de sesión
- Subida por archivo (PDF, imagen, texto) — la IA parsea e infiere datos faltantes; no hay modal de datos faltantes para esta vía
- Edición de rutina existente con instrucción en lenguaje natural
- Modal "Crear / Reemplazar rutina" (portal a `document.body`)
- Modal "Datos faltantes" con opción "La IA infiere" para saltear campos opcionales
- Vista de sesiones semanales: day label, color del punto, título de sesión, kcal estimadas, cantidad de ejercicios
- Visualizador HTML completo de la rutina en modal fullscreen
- Badge de origen: "Generada con IA" / "Subida"
- Advertencia de salud si la IA detecta condiciones relevantes
- 26 tests de integración cubriendo todos los flujos

### Progreso — `Progreso`
- Evaluación periódica generada por IA (semana / mes / año)
- Timeline de métricas corporales
- Cálculo de pliegues cutáneos (3, 4 o 7 pliegues)

### Perfil — `Perfil`
- Panel de biométricos editable (peso, altura, edad, sexo, actividad)
- Cálculo de TDEE y distribución de macros objetivo

### Trainer Dashboard
- Vista de alumnos asignados con acceso a su perfil
- Dashboard vacío con CTA para el primer alumno

### Notificaciones
- Bell en el header con listado de notificaciones y estado leído/no leído

---

## UI / Design System

- **3 temas**: Original (purple/violet) · Dark (electric cyan) · Light (aqua tech)
- Switcheable en runtime vía `ThemeContext` + atributo `data-theme` en el `<html>`
- **Fuente**: Inter (Google Fonts) — aplicada globalmente vía `--font-family` en el `body`
- CSS custom properties para todos los colores de tema: `--theme-accent`, `--theme-bg-gradient`, `--theme-header-bg`, etc.
- Scrollbar global sutil: 4px, casi invisible, con hover suave
- Modales via `createPortal` al `document.body` — todos en `z-index: 1100` (header fijo en `z-index: 1001`)
- Bottom navigation role-aware (oculta tab de Alumnos a usuarios regulares)
- CSS: ~8.500 líneas, completamente organizado por componente y con overrides para los 3 temas

---

## Estructura del proyecto

```
NovaFitness/
├── app/                            # Backend FastAPI
│   ├── api/                        # HTTP routers
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── routine.py
│   │   ├── trainer.py
│   │   ├── invite.py
│   │   └── notifications.py
│   ├── routers/
│   │   └── food.py
│   ├── db/
│   │   ├── models.py               # SQLAlchemy models
│   │   └── database.py
│   ├── schemas/                    # Pydantic schemas
│   ├── services/                   # Business logic
│   │   ├── food_service.py
│   │   ├── routine_service.py
│   │   ├── trainer_service.py
│   │   ├── notification_service.py
│   │   ├── ai_parser_service.py
│   │   └── skinfold_service.py
│   ├── tests/                      # pytest
│   └── main.py
│
└── frontend/                       # React + TypeScript
    ├── index.html                  # Fonts, tokens CSS, PWA meta
    └── src/
        ├── components/
        │   ├── WorkoutModule.tsx   # Mis Entrenos
        │   ├── RoutineModule.tsx   # Mi Rutina
        │   ├── NutritionModule.tsx # Comidas
        │   ├── ProgressModule.tsx  # Progreso
        │   ├── DashboardHeader.tsx
        │   ├── BottomNavigation.tsx
        │   ├── NotificationBell.tsx
        │   ├── ThemePickerModal.tsx
        │   ├── AiMealConfirmModal.tsx
        │   ├── RoutineLogModal.tsx
        │   ├── TrainerStudentsModule.tsx
        │   └── TrainerStudentHome.tsx
        ├── contexts/
        │   ├── AuthContext.tsx
        │   └── ThemeContext.tsx
        ├── pages/
        │   ├── Dashboard.tsx
        │   ├── Login.tsx
        │   └── Register.tsx
        ├── services/
        │   └── api.ts              # Todos los endpoints tipados con Axios
        ├── styles/
        │   └── globals.css
        └── tests/                  # Jest + Testing Library
```

---

## Seguridad

- Contraseñas hasheadas con bcrypt
- JWT con access + refresh token (refresh automático en 401)
- CORS configurado para PWA
- Protección contra SQL injection vía ORM
- Aislamiento de datos por usuario a nivel de BD

---

## Changelog

### 2026-03-21
- **Mis Entrenos**: rediseño completo — botón IA gradient cyan, card "Próximo entreno" con toggle de completado, bottom sheet modal para evitar doble conteo de calorías al ingresar entreno IA con rutina activa, lista plana de hoy con tags, card única de calorías con color dinámico por balance
- **Mi Rutina**: rediseño UI — eliminación del patrón doble-tab, card header con badge top-right, botones Reemplazar/Pedir cambios side-by-side, sección "Semana de entrenamiento" separada con layout de columna por sesión
- **Modales**: fix de z-index (header en 1001 tapaba modales; ahora todos en 1100); iframe del visualizador HTML con altura completa
- **Scrollbar global**: 4px, casi invisible, con hover sutil — reemplaza scrollbar nativo grueso del browser
- **Fuente**: unificación en Inter en toda la app; eliminado uso incorrecto de Barlow (no estaba cargada)
- **Campo lesiones**: ahora requerido en generación de rutina por IA
- **Tests RoutineModule**: 26 tests de integración cubriendo todos los flujos del módulo

### Anteriores
- Módulo de rutinas completo (generación IA, subida por archivo, edición, visualizador HTML)
- Sistema de trainer con dashboard e invitaciones
- Módulo de notificaciones
- 3 temas de color switcheables en runtime
- Integración FatSecret + USDA para búsqueda de alimentos
- PWA con service worker y notificación de actualización
- Módulo de pliegues cutáneos y evaluación de progreso por IA
