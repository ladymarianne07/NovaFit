# Módulo de Evaluación y Visualización de Progreso

## Resumen

Se implementó un sistema completo para evaluar y visualizar el progreso del usuario en NovaFitness, con soporte para tres períodos de evaluación: **semana**, **mes**, y **año**.

## Componentes Implementados

### 1. **Evaluación de Progreso** (`POST /users/me/progress-evaluation`)

Endpoint que analiza el progreso del usuario según su objetivo fitness.

#### Características:
- Evaluación por período: `semana`, `mes`, `anio`
- Scoring adaptativo con multiplicadores por período:
  - Semana: 0.5x (más conservador)
  - Mes: 1.0x (estándar)
  - Año: 1.2x (reconoce transformaciones estructurales)
- Umbrales de ruido específicos por período
- Maneja múltiples objetivos: `perdida_grasa`, `mantenimiento`, `aumento_muscular`, `recomposicion`, `rendimiento`
- Fallback inteligente cuando no hay suficiente data para el período solicitado

#### Respuesta:
```json
{
  "score": -15,
  "estado": "en_progreso",
  "resumen": "Evaluando progreso en mes...",
  "metricas": {
    "peso_inicial_kg": 82.0,
    "peso_actual_kg": 80.0,
    "delta_peso_kg": -2.0,
    "porcentaje_grasa_inicial": 18.5,
    "porcentaje_grasa_actual": 17.0,
    "delta_grasa_pct": -1.5
  },
  "periodo_usado": "mes",
  "advertencias": []
}
```

### 2. **Timeline Histórico** (`GET /users/me/progress/timeline`)

Endpoint que devuelve datos históricos listos para graficar en el frontend.

#### Características:
- Soporta períodos: `?periodo=semana|mes|anio` (default: `mes`)
- Agrega datos de múltiples fuentes:
  - **Peso**: eventos explícitos de peso + mediciones de pliegues cutáneos
  - **Composición corporal**: % grasa y % masa magra de pliegues
  - **Calorías diarias**: consumidas vs meta
  - **Macros diarios**: distribución porcentual de carbohidratos/proteínas/grasas
- Resumen semanal de calorías consumidas vs meta
- Advertencias cuando faltan datos históricos

#### Respuesta:
```json
{
  "periodo": "mes",
  "rango_inicio": "2026-01-22",
  "rango_fin": "2026-02-22",
  "series": {
    "peso": [
      {"fecha": "2026-02-01T10:00:00+00:00", "valor": 82.5},
      {"fecha": "2026-02-08T10:15:00+00:00", "valor": 81.2}
    ],
    "porcentaje_grasa": [
      {"fecha": "2026-02-01T10:00:00+00:00", "valor": 18.5},
      {"fecha": "2026-02-08T10:15:00+00:00", "valor": 17.8}
    ],
    "porcentaje_masa_magra": [
      {"fecha": "2026-02-01T10:00:00+00:00", "valor": 81.5},
      {"fecha": "2026-02-08T10:15:00+00:00", "valor": 82.2}
    ],
    "calorias_diarias": [
      {"fecha": "2026-02-15", "consumidas": 2100, "meta": 2000},
      {"fecha": "2026-02-16", "consumidas": 1950, "meta": 2000}
    ],
    "macros_porcentaje": [
      {"fecha": "2026-02-15", "carbohidratos_pct": 48.5, "proteinas_pct": 30.2, "grasas_pct": 21.3},
      {"fecha": "2026-02-16", "carbohidratos_pct": 47.8, "proteinas_pct": 31.0, "grasas_pct": 21.2}
    ]
  },
  "resumen": {
    "calorias_semana_real": 14350,
    "calorias_semana_meta": 14000
  },
  "advertencias": []
}
```

### 3. **Captura Automática de Peso**

El sistema ahora guarda automáticamente un **evento de peso** cada vez que el usuario actualiza su peso en biometrics:

```python
# Al actualizar peso vía PUT /users/me/biometrics
# Se crea automáticamente un Event con:
{
  "event_type": "weight",
  "title": "Actualización de peso: 78.5 kg",
  "description": "Cambio de 80.0 kg a 78.5 kg",
  "data": {
    "weight_kg": 78.5,
    "previous_weight_kg": 80.0,
    "change_kg": -1.5
  }
}
```

Esto asegura que siempre haya histórico de peso para graficar.

## Archivos Creados/Modificados

### Servicios
- **`app/services/progress_evaluation_service.py`** ✨ (nuevo)
  - Función `evaluarProgreso()` con lógica de scoring adaptativo
  - Manejo de períodos, umbrales, y fallbacks

- **`app/services/progress_timeline_service.py`** ✨ (nuevo)
  - Clase `ProgressTimelineService` con método `build_timeline()`
  - Agrega datos de Event, SkinfoldMeasurement, DailyNutrition
  - Convierte datos a timezone apropiado para el frontend

- **`app/services/user_service.py`** 🔧 (modificado)
  - Agrega auto-guardado de eventos de peso en `update_user_biometrics()` y `update_user_profile_with_biometrics()`

### Schemas
- **`app/schemas/progress.py`** ✨ (nuevo)
  - `ProgressPeriod` - Enum para períodos
  - `ProgressMetrics` - Métricas calculadas
  - `ProgressEvaluationRequest/Response` - Contratos de evaluación
  - `TimelinePoint`, `DailyCaloriesPoint`, `DailyMacroPercentagePoint` - Puntos de datos
  - `ProgressTimelineSeries`, `ProgressTimelineResponse` - Respuestas de timeline

### API
- **`app/api/users.py`** 🔧 (modificado)
  - Agregado `POST /users/me/progress-evaluation`
  - Agregado `GET /users/me/progress/timeline`

### Constantes
- **`app/constants.py`** 🔧 (modificado)
  - `PERIOD_WINDOW_DAYS` - Ventanas de días por período
  - `PERIOD_SCORE_MULTIPLIER` - Multiplicadores de scoring
  - Umbrales de ruido por objetivo y período

### Tests
- **`app/tests/test_progress_evaluation_service.py`** ✨ (nuevo) - 10 tests
- **`app/tests/test_progress_evaluation_endpoint.py`** ✨ (nuevo) - 3 tests
- **`app/tests/test_progress_timeline_endpoint.py`** ✨ (nuevo) - 4 tests

**✅ Total: 17 tests pasando**

## Flujo de Datos

### Evaluación de Progreso
```
Usuario → POST /users/me/progress-evaluation
  |
  v
Endpoint valida objetivo y obtiene historial desde DB
  |
  v
evaluarProgreso() calcula score según período
  |
  v
Respuesta con score, estado, métricas, advertencias
```

### Timeline de Progreso
```
Usuario → GET /users/me/progress/timeline?periodo=mes
  |
  v
ProgressTimelineService.build_timeline()
  ├─ Consulta Event (peso)
  ├─ Consulta SkinfoldMeasurement (peso + composición)
  ├─ Consulta DailyNutrition (calorías + macros)
  └─ Agrega y formatea para gráficas
  |
  v
Respuesta con series por métrica + resumen + advertencias
```

### Auto-guardado de Peso
```
Usuario → PUT /users/me/biometrics (con nuevo peso)
  |
  v
UserService detecta cambio de peso
  |
  v
Crea nuevo Event(type='weight') automáticamente
  |
  v
Peso queda disponible para timeline de progreso
```

## Uso en Frontend

### 1. Evaluación de Progreso
```typescript
// Evaluar progreso del último mes
const response = await fetch('/users/me/progress-evaluation', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    periodo: 'mes'  // 'semana', 'mes', o 'anio'
  })
});

const { score, estado, resumen, metricas } = await response.json();

// Mostrar badge de progreso
if (score > 50) {
  showBadge('¡Excelente progreso!', 'success');
} else if (score > 0) {
  showBadge('En el camino correcto', 'info');
} else {
  showBadge('Necesita ajustes', 'warning');
}
```

### 2. Gráficas de Timeline
```typescript
// Obtener datos para gráfica del último mes
const response = await fetch('/users/me/progress/timeline?periodo=mes', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const { series, resumen } = await response.json();

// Graficar peso
createLineChart('peso-chart', {
  data: series.peso.map(p => ({ x: p.fecha, y: p.valor })),
  label: 'Peso (kg)'
});

// Graficar composición corporal
createLineChart('composicion-chart', {
  datasets: [
    { data: series.porcentaje_grasa, label: '% Grasa' },
    { data: series.porcentaje_masa_magra, label: '% Masa Magra' }
  ]
});

// Graficar calorías con meta
createBarChart('calorias-chart', {
  data: series.calorias_diarias.map(d => ({
    fecha: d.fecha,
    consumidas: d.consumidas,
    meta: d.meta
  }))
});

// Mostrar resumen semanal
showSummary(`Esta semana: ${resumen.calorias_semana_real} kcal de ${resumen.calorias_semana_meta} kcal meta`);
```

## Próximos Pasos (Futuro)

1. **Endpoint de Resumen por Objetivo** - GET `/users/me/progress/summary`
   - Comparar peso/composición inicial vs actual
   - Calcular % completado hacia meta del objetivo
   - Estimar tiempo para alcanzar objetivo

2. **Predicciones con IA**
   - Usar histórico para predecir progreso futuro
   - Sugerir ajustes en calorías/macros según tendencia

3. **Notificaciones Proactivas**
   - Alertas cuando el progreso se estanca
   - Celebraciones cuando se alcanzan hitos

4. **Reportes Exportables**
   - PDF con gráficas y métricas del período
   - Comparativa mensual/trimestral

## Testing

Ejecutar tests de progreso:
```bash
pytest app/tests/test_progress_evaluation_service.py -v
pytest app/tests/test_progress_evaluation_endpoint.py -v
pytest app/tests/test_progress_timeline_endpoint.py -v
```

Ejecutar todos juntos:
```bash
pytest app/tests/test_progress_*.py -v
```

## Notas Técnicas

- **Períodos soportados**: `semana` (7 días), `mes` (30 días), `anio` (365 días)
- **Timezone**: Se normaliza todo a UTC internamente, se convierte a `APP_TIMEZONE` en respuestas
- **Scoring**: Rango [-100, 100], donde 100 = progreso perfecto alineado con objetivo
- **Fallback**: Si no hay datos del período solicitado, usa el período más cercano disponible
- **Performance**: Queries optimizadas con filtros por fecha y usuario
