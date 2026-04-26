# Auditoría de Templates y Strings Embebidos — NovaFitness Backend
**Fecha:** 2026-04-04 | **Tipo:** Solo lectura

## Resumen Ejecutivo

Se identificaron **7 templates mayores** embebidos en funciones Python. Total estimado: **~774 líneas** de templates. Todos están actualmente dentro de archivos de servicio. Se recomienda extraerlos a un módulo `app/templates/`.

---

## Inventario de Templates

### 1. `DIET_JSON_SCHEMA` — Instrucciones de Esquema JSON para Dietas

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/services/diet_service.py` |
| **Líneas** | 27–98 |
| **Tipo** | Especificación de restricciones para output de IA |
| **Tamaño** | 72 líneas |
| **Nombre sugerido** | `DIET_JSON_SCHEMA` |

**Usado en:**
- `_build_diet_generation_prompt()` (línea 258)
- `_build_diet_edit_prompt()` (línea 284)

---

### 2. `DIET_SYSTEM_PROMPT` — Prompt del Sistema para Nutricionista

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/services/diet_service.py` |
| **Líneas** | 100–141 |
| **Tipo** | Instrucción de sistema para IA |
| **Tamaño** | 42 líneas |
| **Nombre sugerido** | `DIET_SYSTEM_PROMPT` |

**Contenido clave:**
- Definición de rol de nutricionista
- Principios de cálculo de macros
- Fórmulas de ingesta de agua
- Restricciones de salud (vegetariano, vegano, gluten, lactosa, nueces)
- Condiciones de salud (diabetes, hipertensión, hipotiroidismo, SII, gota, anemia)
- Consideraciones de presupuesto y tiempo de cocción

**Usado en:**
- `_build_diet_generation_prompt()` (línea 223)
- `_build_diet_edit_prompt()` (línea 263)

---

### 3. `DIET_HTML_TEMPLATE` — Documento HTML Completo para Dietas

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/services/diet_service.py` |
| **Líneas** | 287–455 |
| **Tipo** | Template HTML autodocumentado |
| **Tamaño** | 169 líneas |
| **Nombre sugerido** | `DIET_HTML_TEMPLATE` o mantener como método |

**Características:**
- CSS embebido con soporte de temas (original, dark, light)
- Sistema de variables de tema
- Renderizado de tarjetas de comidas
- Tablas de macros
- Selector de tema interactivo
- Diseño responsive

**Usado en:**
- `DietService.generate_from_text()`
- `DietService.edit_diet()`
- `DietService.get_meal_alternative()`

---

### 4. `ROUTINE_JSON_SCHEMA` — Instrucciones de Esquema JSON para Rutinas

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/services/routine_service.py` |
| **Líneas** | 33–121 |
| **Tipo** | Especificación de restricciones para output de IA |
| **Tamaño** | 89 líneas |
| **Nombre sugerido** | `ROUTINE_JSON_SCHEMA` |

**Contenido clave:**
- Estructura JSON requerida (fases, schedule, sessions, month_data)
- Reglas de organización de ejercicios
- Pautas de periodización (Adaptación/Fuerza/Excéntrico)
- Requerimientos de análisis de salud
- Rangos de reps/sets

**Usado en:**
- `_FILE_PARSE_PROMPT` (línea 127)
- `_PT_SYSTEM_PROMPT` (línea 130)

---

### 5. `ROUTINE_FILE_PARSE_PROMPT` — Prompt para Parsear Archivos Subidos

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/services/routine_service.py` |
| **Líneas** | 123–128 |
| **Tipo** | Prompt prefijo para parsing de archivos |
| **Tamaño** | 6 líneas |
| **Nombre sugerido** | `ROUTINE_FILE_PARSE_PROMPT` |

---

### 6. `ROUTINE_SYSTEM_PROMPT` — Prompt del Sistema para Entrenador Personal

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/services/routine_service.py` |
| **Líneas** | 130–191 |
| **Tipo** | Instrucción de sistema para IA |
| **Tamaño** | 62 líneas |
| **Nombre sugerido** | `ROUTINE_SYSTEM_PROMPT` |

**Contenido clave:**
- Definición de rol de personal trainer
- Protocolo de validación de salud (5 pasos)
- Contraindicaciones por condición (rodilla, lumbar, cervical, tiroides, fibromialgia, artritis, escoliosis, hombro, hiperlaxitud, diabetes, hipertensión, embarazo/postparto)
- Programación por objetivo (pérdida de grasa, recomposición, ganancia muscular)
- Detección y manejo de CrossFit
- Inferencia ante datos insuficientes

**Usado en:**
- `_build_pt_generation_prompt()` (línea 238)
- `_build_edit_prompt()` (línea 283)

---

### 7. `FOOD_PARSER_SYSTEM_PROMPT` — Prompt del Sistema para Parser de Alimentos

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/services/ai_parser_service.py` |
| **Líneas** | 39–99 |
| **Tipo** | Instrucción de sistema para IA |
| **Tamaño** | 61 líneas |
| **Nombre sugerido** | `FOOD_PARSER_SYSTEM_PROMPT` |

**Contenido clave:**
- Definición de rol de parser nutricional
- Reglas de validación de input (dominio inválido, datos insuficientes, ingesta cero)
- Reglas de resolución de tamaños/recipientes (vaso=250ml, bowl=350ml, huevo=60g)
- Manejo de suplementos (items no calóricos)
- Detección de contexto receta/preparación
- Especificaciones de formato de output

**Usado en:** `parse_food_with_gemini()` (línea 229)

---

## Estructura Propuesta

### Opción A: Módulos Separados por Dominio (Recomendada)

```
app/
├── templates/
│   ├── __init__.py
│   ├── diet.py          # DIET_JSON_SCHEMA, DIET_SYSTEM_PROMPT
│   ├── routine.py       # ROUTINE_JSON_SCHEMA, ROUTINE_SYSTEM_PROMPT, FILE_PARSE_PROMPT
│   └── food_parser.py   # FOOD_PARSER_SYSTEM_PROMPT
```

### Opción B: Un Solo `templates.py`

```
app/
├── templates.py         # Todos los templates en un archivo
```

---

## Dependencias a Actualizar

### `diet_service.py`
```python
from ..templates.diet import DIET_JSON_SCHEMA, DIET_SYSTEM_PROMPT
```
- `_build_diet_generation_prompt()` — remover definición inline
- `_build_diet_edit_prompt()` — remover definición inline

### `routine_service.py`
```python
from ..templates.routine import ROUTINE_JSON_SCHEMA, ROUTINE_SYSTEM_PROMPT, ROUTINE_FILE_PARSE_PROMPT
```
- `_build_pt_generation_prompt()` — remover definición inline
- `_build_edit_prompt()` — remover definición inline
- `_FILE_PARSE_PROMPT` — usar import en lugar de asignación

### `ai_parser_service.py`
```python
from ..templates.food_parser import FOOD_PARSER_SYSTEM_PROMPT
```
- `parse_food_with_gemini()` — referenciar constante importada

---

## Tabla Resumen por Tamaño y Prioridad

| Template | Archivo | Líneas | Complejidad | Prioridad de extracción |
|----------|---------|--------|-------------|------------------------|
| `DIET_JSON_SCHEMA` | diet_service.py | 72 | Alta | P1 |
| `DIET_SYSTEM_PROMPT` | diet_service.py | 42 | Alta | P1 |
| `ROUTINE_JSON_SCHEMA` | routine_service.py | 89 | Alta | P1 |
| `ROUTINE_SYSTEM_PROMPT` | routine_service.py | 62 | Muy Alta | P1 |
| `FOOD_PARSER_SYSTEM_PROMPT` | ai_parser_service.py | 61 | Alta | P1 |
| `ROUTINE_FILE_PARSE_PROMPT` | routine_service.py | 6 | Baja | P1 |
| HTML de Dieta | diet_service.py | 169 | Muy Alta | P2 |
| HTML de Rutina | routine_service.py | 279 | Muy Alta | P2 |

**Total código de templates: ~780 líneas**

---

## Notas y Observaciones

1. **Los prompts son construcciones dinámicas** — Las templates se usan dentro de funciones builder que inyectan datos específicos del usuario. Esto es buena práctica y debe mantenerse.
2. **No quedan magic strings sueltos** — Todos los strings mayores ya son constantes de módulo; solo están en el archivo incorrecto.
3. **HTML altamente optimizado** — Contiene sistemas CSS de variables, temas e JavaScript interactivo. Moverlos a archivos separados mejoraría la legibilidad.
4. **Idioma español en todo** — Todos los prompts orientados al usuario están en español. Localización puede ser necesaria a futuro.
5. **Restricciones de modelo específicas** — Comentarios referencian limitaciones del modelo Gemini 2.5 Flash y budgets de tokens (65536 → 12000/10000).
