# NovaFitness — Inventario Visual de Pantallas y Componentes

Este documento describe todas las pantallas, secciones y componentes visuales del frontend de NovaFitness. Está pensado para que un diseñador pueda entender qué hay hoy y proponer un rediseño.

---

## Stack y sistema de diseño actual

- **Framework:** React 18 + TypeScript
- **Estilos:** CSS puro con variables globales (`globals.css`) — sin Tailwind ni librería de UI
- **Íconos:** `lucide-react`
- **Fuentes:** Sistema (no se define fuente custom en el stack principal)
- **Navegación:** React Router DOM — una sola ruta `/dashboard` con paneles deslizables internos

### Variables de color actuales

| Variable | Valor | Uso |
|---|---|---|
| `--color-primary` | `#ec4899` | Botones primarios, acentos |
| `--color-secondary` | `#8b5cf6` | Gradientes, secundario |
| `--gradient-primary` | `#ec4899 → #8b5cf6` | Botones, badges |
| Fondo oscuro | `#0e0e0f` / `#161618` | Cards y fondos |
| Texto principal | `#f0ede8` | Títulos |
| Texto muted | `#7a7870` | Labels, hints |
| Borde | `#2a2a2e` | Separadores |
| Error | `#ef4444` | Mensajes de error |

### Efectos visuales presentes

- Glassmorphism (blur + transparencia en cards)
- Gradiente animado en botones (2s ease-in-out infinite)
- Neon loader (conic-gradient con glow en cyan, verde neón, amarillo, rosa, púrpura)
- Sombras: `sm`, estándar, `lg`
- Animación `fade-in` (0.3s ease)

---

## Pantallas

### 1. Login

**Ruta:** `/login`

**Propósito:** Autenticación del usuario.

#### Secciones

| Sección | Contenido |
|---|---|
| Branding | Logo (imagen grande), nombre de la app, tagline motivacional |
| Formulario | Email + contraseña (con toggle show/hide) |
| CTA | Botón "Iniciar sesión" con ícono Zap |
| Footer | Link "¿No tenés cuenta? Registrate" |

#### Estados visuales
- Botón deshabilitado + spinner mientras carga
- Mensaje de error en rojo bajo el formulario
- Fondo con gradiente de color (`#667eea → #764ba2 → #f093fb`)

---

### 2. Registro

**Ruta:** `/register`

**Propósito:** Alta de usuario nuevo. Flujo de 3 pasos.

#### Paso 1 — Cuenta
| Campo | Tipo |
|---|---|
| Email | Input texto |
| Contraseña | Input password con toggle |
| Confirmar contraseña | Input password con toggle |
| Nombre | Input texto |
| Apellido | Input texto |

#### Paso 2 — Datos físicos
| Campo | Tipo |
|---|---|
| Edad | Input numérico |
| Género | Dropdown (Masculino / Femenino) |
| Peso | Input numérico (kg) |
| Altura | Input numérico (cm) |
| Nivel de actividad | Dropdown (5 opciones: sedentario → muy activo) |

#### Paso 3 — Objetivo
| Campo | Tipo |
|---|---|
| Objetivo fitness | Dropdown (Mantenimiento, Pérdida de grasa, Ganancia muscular, Recomposición, Performance) |
| Agresividad | Selector de intensidad (1–3) |

#### Elementos UI comunes
- Barra de progreso (3 pasos) con indicador numérico actual
- Botón "Continuar" / "Atrás"
- Link al login para usuarios ya registrados

---

### 3. Dashboard

**Ruta:** `/dashboard`

Es la pantalla principal. Contiene un sistema de navegación por tabs con paneles deslizables (tipo carrusel horizontal con swipe táctil).

#### Estructura global

```
┌─────────────────────────────────────────┐
│ DashboardHeader (fijo, top)             │
├─────────────────────────────────────────┤
│                                         │
│  Panel deslizable (activo según tab)    │
│  → Inicio                               │
│  → Comidas                              │
│  → Entrenamiento                        │
│  → Progreso                             │
│                                         │
├─────────────────────────────────────────┤
│ BottomNavigation (fijo, bottom)         │
└─────────────────────────────────────────┘
```

El tab **Perfil** no forma parte del carrusel — se renderiza fuera del sistema de slides.

---

## Componentes del Dashboard

### 3.1 DashboardHeader

**Posición:** Fixed top.

| Elemento | Detalle |
|---|---|
| Logo + nombre | "NovaFitness" con logo a la izquierda |
| Título del tab actual | Texto dinámico (Inicio / Comidas / Entrenamiento / Progreso / Perfil) |
| Botón Perfil | Ícono de usuario, se activa al tocar |
| Botón Logout | Ícono de salida |

Al tocar Logout aparece un **modal de confirmación** con:
- Título "¿Seguro que querés salir?"
- Dos botones: "Cancelar" (ghost) / "Sí, salir" (danger)

---

### 3.2 BottomNavigation

**Posición:** Fixed bottom.

Cuatro botones con ícono + label:

| Tab | Ícono | Label |
|---|---|---|
| Inicio | Home | Inicio |
| Comidas | Utensils | Comidas |
| Entrenamiento | Dumbbell | Entreno |
| Progreso | TrendingUp | Progreso |

El botón activo tiene un estilo diferenciado (color primario).

---

### 3.3 Tab: Inicio

Muestra el resumen del día. Dos secciones principales:

#### DashboardNutritionOverview
Resumen calórico y de macros del día.

| Elemento | Detalle |
|---|---|
| Título | "Resumen de hoy" |
| Calorías | Número grande (consumidas vs. objetivo) |
| Modo calórico | Etiqueta dinámica: "ingesta" o "netas" (cuando hay ejercicio registrado) |
| Barra de progreso | Progreso de calorías del día |
| Calorías quemadas | Solo visible si hay entreno registrado |
| Grid de macros | 3 cards: Carbohidratos, Proteínas, Grasas (con gramos consumidos y % de objetivo) |

#### DashboardBodyComposition
Composición corporal y peso.

| Elemento | Detalle |
|---|---|
| Título | "Composición corporal" + fecha de última medición |
| Peso | Valor actual con ícono, editable con botón "Actualizar" |
| % Grasa corporal | Solo si hay medición (pliometría) |
| % Masa magra | Solo si hay medición |
| Campo de edición | Input numérico que aparece al activar edición de peso |

#### SuggestionCard
| Elemento | Detalle |
|---|---|
| Título | "Sugerencia del Día" + badge "IA" |
| Contenido | Texto generado por IA con recomendación del día |
| Estado carga | Spinner |

---

### 3.4 Tab: Comidas (`NutritionModule`)

#### Sección de input IA (colapsable)

| Elemento | Detalle |
|---|---|
| Toggle | Botón "Ingresar comida por IA" (ícono Brain) para mostrar/ocultar |
| Textarea | Campo libre para describir comidas en texto natural |
| Botón voz | Micrófono para dictado (si el navegador lo soporta) |
| Botón acción | "Calcular y previsualizar" → abre modal de confirmación |

#### Carrusel de comidas registradas

| Elemento | Detalle |
|---|---|
| Controles | Botones izquierda/derecha (chevron) + contador "Comida X de N" |
| Card de comida | Label de comida (Desayuno, Almuerzo, etc.) + badge de tipo + hora |
| Lista de items | Nombre de alimento (traducido al español) + cantidad en gramos |
| Resumen macros | 4 pills de colores: Calorías, Carbos, Proteínas, Grasas |
| Botón eliminar | Ícono papelera por cada comida |
| Dots navegación | Puntos en la parte inferior para acceso rápido |

#### AiMealConfirmModal (overlay)

Modal que aparece al previsualizar las comidas antes de guardar.

| Elemento | Detalle |
|---|---|
| Título | "Revisá tu comida antes de guardar" |
| Tabla por grupo de comida | Columnas: Alimento / Cantidad (g) editable / Calorías calculadas |
| Subtotal por grupo | Fila de subtotal de calorías |
| Total general | Solo si hay múltiples grupos |
| Botones | "Cancelar" + "Confirmar y guardar" |

---

### 3.5 Tab: Entrenamiento

Contiene dos componentes apilados: `WorkoutModule` y `RoutineModule`.

#### WorkoutModule

##### Sección input IA (colapsable)

| Elemento | Detalle |
|---|---|
| Toggle | Botón "Ingresar entreno por IA" (ícono Brain) |
| Textarea | Campo libre para describir ejercicios, duración e intensidad |
| Ejemplo hint | Texto de ayuda con ejemplo de entrada |
| Botón acción | "Guardar entrenamiento" (ícono Sparkles) |

##### Resumen energético del día

| Elemento | Detalle |
|---|---|
| Calorías ingeridas | Número + label |
| Calorías quemadas | Número + label |
| Calorías netas | Número + label (diferencia) |

##### Carrusel de sesiones registradas

| Elemento | Detalle |
|---|---|
| Controles | Botones izquierda/derecha + contador "Entreno X de N" |
| Card de sesión | Número de sesión + badge origen (IA / Manual / Rutina) |
| Bloques de ejercicio | Lista: número de bloque + actividad + duración + intensidad + kcal |
| Total de sesión | Calorías totales estimadas |
| Botón eliminar | Ícono papelera por sesión |
| Dots navegación | Puntos en la parte inferior |

#### RoutineModule

##### Vista de carga (sin rutina activa)

| Elemento | Detalle |
|---|---|
| Título | "Mi Rutina" |
| Subtítulo | Instrucción para subir archivo |
| Dropzone | Zona de arrastrar/soltar con ícono 📄 |
| Formatos aceptados | PDF · Imagen · Texto |
| Estado cargando | Spinner + "Procesando con IA..." |
| Error | Mensaje en rojo si falla |

##### Vista con rutina cargada

| Elemento | Detalle |
|---|---|
| Título | "Mi Rutina" + nombre del archivo fuente |
| Botón principal | "Registrar entrenamiento" |
| Botón secundario | "Ver rutina" (abre visor HTML) |
| Botón terciario | "Reemplazar" (vuelve a vista de carga) |
| Cards de sesiones | Una card por día de entrenamiento: punto de color + label del día + título + calorías estimadas |

##### Visor HTML (overlay full screen)
| Elemento | Detalle |
|---|---|
| Toolbar | Título "Tu rutina" + botón cerrar |
| Iframe | Rutina renderizada con diseño completo (mismo estilo que `rutina.html`) |

##### RoutineLogModal
| Elemento | Detalle |
|---|---|
| Dropdown sesión | Seleccionar cuál día de la rutina se hizo |
| Input fecha | Date picker (default: hoy) |
| Lista ejercicios | Checkbox por ejercicio — marcar los que NO se hicieron |
| Calorías por ejercicio | Mostradas al lado de cada ítem, tachadas si se saltea |
| Total estimado | Calorías ajustadas en tiempo real |
| Botones | "Cancelar" + "Confirmar" |

---

### 3.6 Tab: Progreso (`ProgressModule`)

Carrusel de 2 slides.

#### Selector de período

3 botones en la parte superior: **Semana** / **Mes** / **Año**

#### Slide 1 — Evaluación de Progreso

| Elemento | Detalle |
|---|---|
| Score badge | Ícono + etiqueta cualitativa (Excelente / Muy Bien / En Progreso / Estable / Atención / Revisar Plan) |
| Barra de score | Progreso visual de 0 a 100 |
| Valor numérico | Score de -100 a 100 (mostrado como 0–100) |
| Resumen textual | Párrafo generado por IA |
| Grid de métricas | Peso inicial vs. actual, % grasa inicial vs. actual, % masa magra inicial vs. actual |
| Deltas | Indicadores de cambio con color (verde positivo, rojo negativo) |

#### Slide 2 — Evolución Corporal

3 gráficos de línea SVG (con gradiente de relleno):

| Gráfico | Datos |
|---|---|
| Peso | Evolución en kg a lo largo del tiempo |
| % Grasa Corporal | Porcentaje a lo largo del tiempo |
| % Masa Magra | Porcentaje a lo largo del tiempo |

Cada gráfico muestra: valor inicial, valor actual, fecha de última medición.

#### Controles de carrusel
- Botones izquierda/derecha (chevron)
- 2 dots de navegación

---

### 3.7 Tab: Perfil (`ProfileBiometricsPanel`)

Tres tabs internos:

#### Tab Personal

| Campo | Tipo |
|---|---|
| Edad | Input numérico |
| Género | Dropdown |
| Peso | Input numérico (kg) |
| Altura | Input numérico (cm) |
| Objetivo fitness | Dropdown |
| Nivel de agresividad | Selector |
| Botón guardar | Deshabilitado si no hay cambios |

#### Tab Nutrición

| Campo | Tipo |
|---|---|
| Objetivo calórico diario | Input numérico (kcal) |
| % Carbohidratos | Input numérico |
| % Proteínas | Input numérico |
| % Grasas | Input numérico |
| Botón guardar | Deshabilitado si no hay cambios |

#### Tab Pliometría (medición corporal)

**Slider de 7 sitios de medición** (uno a la vez):

| Sitio | Campo |
|---|---|
| Pecho | mm |
| Axila media | mm |
| Tríceps | mm |
| Subescapular | mm |
| Abdomen | mm |
| Suprailiaca | mm |
| Muslo | mm |

Otros elementos:
- Toggle de **modo triplicado** (3 mediciones por sitio, se promedia)
- Texto de ayuda con técnica correcta de medición
- Botón "Calcular"
- Controles de slider (chevron + dots)
- Touch swipe habilitado

**Card de resultado:**

| Dato | Detalle |
|---|---|
| % Grasa corporal | Valor calculado |
| % Masa libre de grasa | Complemento |
| Suma de pliegues | Total en mm |
| Método | Jackson & Pollock 7 |
| Fecha de medición | Timestamp |
| Advertencias | Si las hay (edad fuera de rango, etc.) |

**Historial:** Muestra las últimas 3 mediciones.

---

## Resumen de flows de datos por pantalla

| Pantalla | Datos que muestra | Origen de datos |
|---|---|---|
| Login | — | — |
| Registro | Opciones de actividad y objetivo | Frontend (constantes) |
| Dashboard Inicio | Macros del día, calorías, composición corporal, sugerencia IA | API: `/nutrition/macros`, `/nutrition/suggestions`, `/users/me/skinfolds`, `/v1/days/{date}/energy` |
| Comidas | Comidas registradas del día, parsing IA | API: `/nutrition/meals`, `/food/parse-preview`, `/food/confirm-and-log` |
| Entrenamiento - Workout | Sesiones del día, energía diaria | API: `/v1/sessions`, `/v1/days/{date}/energy` |
| Entrenamiento - Rutina | Rutina activa del usuario | API: `/v1/routines/active`, `/v1/routines/upload`, `/v1/routines/log-session` |
| Progreso | Score de progreso, métricas históricas, gráficos | API: `/users/me/progress-evaluation`, `/users/me/progress/timeline` |
| Perfil Personal | Datos biométricos del usuario | API: `/users/me` (GET/PUT) |
| Perfil Nutrición | Targets de macros | API: `/users/me/nutrition-targets` |
| Perfil Pliometría | Historial de mediciones, cálculo nuevo | API: `/users/me/skinfolds` |

---

## Notas para el diseñador

1. **Es una PWA mobile-first** — la experiencia principal es en pantalla de celular. Existe un archivo `manifest.json` y service worker configurados.
2. **Navegación principal:** Header fijo arriba + Bottom Nav fija abajo. El contenido central es el único espacio variable.
3. **Interacción táctil:** Swipe horizontal está implementado en múltiples carruseles (tabs principales, comidas, sesiones, pliometría, progreso).
4. **Todos los modales** se renderizan fuera del árbol DOM principal (via `createPortal` sobre `document.body`).
5. **El módulo de rutina** genera un HTML self-contained que se visualiza en un `<iframe>` — ese HTML tiene su propio diseño (dark, editorial, tipografía Playfair Display).
6. **Lenguaje de la app:** Español rioplatense (voseo).
