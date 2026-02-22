# API Reference - Módulo de Progreso

## Endpoints

### 1. Evaluación de Progreso

**`POST /users/me/progress-evaluation`**

Evalúa el progreso del usuario según su objetivo fitness en un período específico.

#### Headers
```
Authorization: Bearer {token}
Content-Type: application/json
```

#### Request Body
```json
{
  "periodo": "mes"  // Opcional: "semana", "mes", "anio". Default: "mes"
}
```

#### Response 200 OK
```json
{
  "score": -25,
  "estado": "en_progreso",
  "resumen": "Evaluando progreso en mes: Has perdido 2.0 kg y reducido tu % de grasa en 1.8%.",
  "metricas": {
    "peso_inicial_kg": 82.0,
    "peso_actual_kg": 80.0,
    "delta_peso_kg": -2.0,
    "porcentaje_grasa_inicial": 19.2,
    "porcentaje_grasa_actual": 17.4,
    "delta_grasa_pct": -1.8,
    "porcentaje_magra_inicial": 80.8,
    "porcentaje_magra_actual": 82.6,
    "delta_magra_pct": 1.8
  },
  "periodo_usado": "mes",
  "advertencias": []
}
```

#### Response Codes
- **200 OK** - Evaluación exitosa
- **400 Bad Request** - Usuario sin objetivo configurado
- **401 Unauthorized** - Token inválido o faltante
- **422 Unprocessable Entity** - Período inválido en body

#### Interpretación del Score
| Score | Estado | Significado |
|-------|--------|-------------|
| > 70  | excelente | Progreso excepcional hacia el objetivo |
| 40-70 | muy_bien | Buen progreso, en el camino correcto |
| 10-40 | en_progreso | Progreso moderado, continuar |
| -10-10 | estable | Sin cambios significativos |
| -40--10 | atencion | Progreso lento o desviado, revisar plan |
| < -40 | revisar_plan | Progreso opuesto al objetivo, ajustar estrategia |

#### Periodo vs Multiplicador
| Periodo | Días | Multiplicador | Uso |
|---------|------|---------------|-----|
| semana  | 7    | 0.5x         | Evaluación conservadora, menos sensible a fluctuaciones |
| mes     | 30   | 1.0x         | Evaluación estándar, balanceada |
| anio    | 365  | 1.2x         | Reconoce transformaciones estructurales de largo plazo |

---

### 2. Timeline de Progreso

**`GET /users/me/progress/timeline`**

Obtiene datos históricos del usuario listos para graficar.

#### Headers
```
Authorization: Bearer {token}
```

#### Query Parameters
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| periodo   | string | "mes" | Período de datos: "semana", "mes", "anio" |

#### Response 200 OK
```json
{
  "periodo": "mes",
  "rango_inicio": "2026-01-22",
  "rango_fin": "2026-02-22",
  "series": {
    "peso": [
      {
        "fecha": "2026-02-01T10:30:00-06:00",
        "valor": 82.5
      },
      {
        "fecha": "2026-02-08T11:15:00-06:00",
        "valor": 81.2
      },
      {
        "fecha": "2026-02-15T09:45:00-06:00",
        "valor": 80.0
      }
    ],
    "porcentaje_grasa": [
      {
        "fecha": "2026-02-01T10:30:00-06:00",
        "valor": 18.5
      },
      {
        "fecha": "2026-02-08T11:15:00-06:00",
        "valor": 17.8
      },
      {
        "fecha": "2026-02-15T09:45:00-06:00",
        "valor": 17.0
      }
    ],
    "porcentaje_masa_magra": [
      {
        "fecha": "2026-02-01T10:30:00-06:00",
        "valor": 81.5
      },
      {
        "fecha": "2026-02-08T11:15:00-06:00",
        "valor": 82.2
      },
      {
        "fecha": "2026-02-15T09:45:00-06:00",
        "valor": 83.0
      }
    ],
    "calorias_diarias": [
      {
        "fecha": "2026-02-14",
        "consumidas": 2150,
        "meta": 2000
      },
      {
        "fecha": "2026-02-15",
        "consumidas": 1980,
        "meta": 2000
      },
      {
        "fecha": "2026-02-16",
        "consumidas": 2050,
        "meta": 2000
      }
    ],
    "macros_porcentaje": [
      {
        "fecha": "2026-02-14",
        "carbohidratos_pct": 48.5,
        "proteinas_pct": 29.8,
        "grasas_pct": 21.7
      },
      {
        "fecha": "2026-02-15",
        "carbohidratos_pct": 47.2,
        "proteinas_pct": 31.0,
        "grasas_pct": 21.8
      },
      {
        "fecha": "2026-02-16",
        "carbohidratos_pct": 49.1,
        "proteinas_pct": 30.2,
        "grasas_pct": 20.7
      }
    ]
  },
  "resumen": {
    "calorias_semana_real": 14250,
    "calorias_semana_meta": 14000
  },
  "advertencias": [
    "No hay mediciones de pliegues cutáneos registradas en el periodo seleccionado."
  ]
}
```

#### Response Codes
- **200 OK** - Timeline generado exitosamente (puede incluir series vacías si no hay datos)
- **401 Unauthorized** - Token inválido o faltante
- **422 Unprocessable Entity** - Período inválido en query

#### Estructuras de Datos

##### Serie de Peso/Composición
```typescript
{
  fecha: string;  // ISO 8601 con timezone
  valor: number;  // kg para peso, % para composición
}
```

##### Serie de Calorías
```typescript
{
  fecha: string;      // YYYY-MM-DD
  consumidas: number; // Calorías consumidas ese día
  meta: number;       // Calorías meta según objetivo
}
```

##### Serie de Macros
```typescript
{
  fecha: string;            // YYYY-MM-DD
  carbohidratos_pct: number; // % de calorías de carbohidratos
  proteinas_pct: number;     // % de calorías de proteínas
  grasas_pct: number;        // % de calorías de grasas
}
```

#### Fuentes de Datos

| Serie | Fuente(s) | Condiciones |
|-------|-----------|-------------|
| peso | Event (type='weight') + SkinfoldMeasurement.weight_kg | Auto-generado al actualizar biometrics |
| porcentaje_grasa | SkinfoldMeasurement.body_fat_percent | Requiere mediciones de pliegues |
| porcentaje_masa_magra | SkinfoldMeasurement.fat_free_mass_percent | Requiere mediciones de pliegues |
| calorias_diarias | DailyNutrition.total_calories + target_calories | Require logging de alimentos |
| macros_porcentaje | DailyNutrition.consumed_* + target_* | Calculado de macros consumidos vs meta |

#### Advertencias Comunes

- `"No hay eventos de peso registrados en el periodo seleccionado."`
- `"No hay mediciones de pliegues cutáneos registradas en el periodo seleccionado."`
- `"No hay consumo calórico diario registrado en el periodo seleccionado."`
- `"Periodo no reconocido. Se usó 'mes' por defecto."`

---

## Casos de Uso

### Caso 1: Dashboard de Progreso Mensual

```typescript
async function showMonthlyProgress(userId: string, token: string) {
  // Obtener evaluación
  const evalRes = await fetch('/users/me/progress-evaluation', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ periodo: 'mes' })
  });
  const evaluation = await evalRes.json();

  // Obtener timeline
  const timelineRes = await fetch('/users/me/progress/timeline?periodo=mes', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const timeline = await timelineRes.json();

  // Renderizar
  renderProgressCard({
    score: evaluation.score,
    summary: evaluation.resumen,
    metrics: evaluation.metricas
  });

  renderWeightChart(timeline.series.peso);
  renderCompositionChart({
    fat: timeline.series.porcentaje_grasa,
    lean: timeline.series.porcentaje_masa_magra
  });
  renderCaloriesChart(timeline.series.calorias_diarias);
  renderMacrosChart(timeline.series.macros_porcentaje);
}
```

### Caso 2: Comparación Semanal vs Mensual

```typescript
async function compareProgress(token: string) {
  const [weekEval, monthEval] = await Promise.all([
    fetch('/users/me/progress-evaluation', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ periodo: 'semana' })
    }).then(r => r.json()),
    
    fetch('/users/me/progress-evaluation', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ periodo: 'mes' })
    }).then(r => r.json())
  ]);

  console.log('Progreso Semanal:', weekEval.score);
  console.log('Progreso Mensual:', monthEval.score);
  
  if (weekEval.score < monthEval.score) {
    alert('Tu progreso se ha desacelerado esta semana.');
  }
}
```

### Caso 3: Gráfica de Peso con Chart.js

```typescript
async function renderWeightChart(token: string) {
  const res = await fetch('/users/me/progress/timeline?periodo=mes', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const timeline = await res.json();

  const ctx = document.getElementById('weightChart');
  new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Peso (kg)',
        data: timeline.series.peso.map(p => ({
          x: new Date(p.fecha),
          y: p.valor
        })),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }]
    },
    options: {
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'day'
          }
        }
      }
    }
  });
}
```

### Caso 4: Badge de Progreso Dinámico

```typescript
async function updateProgressBadge(token: string) {
  const res = await fetch('/users/me/progress-evaluation', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ periodo: 'mes' })
  });
  const { score, estado } = await res.json();

  const badge = document.getElementById('progressBadge');
  
  if (score > 70) {
    badge.className = 'badge badge-success';
    badge.textContent = '🏆 Excelente';
  } else if (score > 40) {
    badge.className = 'badge badge-info';
    badge.textContent = '✅ Muy Bien';
  } else if (score > 10) {
    badge.className = 'badge badge-primary';
    badge.textContent = '📈 En Progreso';
  } else if (score > -10) {
    badge.className = 'badge badge-secondary';
    badge.textContent = '➡️ Estable';
  } else if (score > -40) {
    badge.className = 'badge badge-warning';
    badge.textContent = '⚠️ Atención';
  } else {
    badge.className = 'badge badge-danger';
    badge.textContent = '🔄 Revisar Plan';
  }
}
```

---

## Notas de Implementación

### Timezone Handling
- Todas las fechas en `series.peso`, `porcentaje_grasa`, `porcentaje_masa_magra` están en timezone local del servidor (`APP_TIMEZONE`)
- Las fechas en `calorias_diarias` y `macros_porcentaje` son solo fecha (YYYY-MM-DD) sin hora
- El frontend debe parsear las fechas ISO 8601 correctamente con `new Date()`

### Performance
- El endpoint de timeline hace 3 queries a la DB (Event, SkinfoldMeasurement, DailyNutrition)
- Todas las queries tienen filtros por `user_id` y rango de fechas (indexed)
- Para datasets grandes (>1 año), considerar paginación o sub-sampling en frontend

### Caching Recomendado
```typescript
// Cache evaluación por 1 hora
const cacheKey = `progress_eval_${userId}_${periodo}`;
const cached = localStorage.getItem(cacheKey);
const cacheTime = localStorage.getItem(`${cacheKey}_time`);

if (cached && Date.now() - cacheTime < 3600000) {
  return JSON.parse(cached);
}

// Fetch fresh data...
localStorage.setItem(cacheKey, JSON.stringify(data));
localStorage.setItem(`${cacheKey}_time`, Date.now());
```

### Manejo de Series Vacías
```typescript
if (timeline.series.peso.length === 0) {
  showEmptyState('No hay datos de peso para este período.');
} else {
  renderChart(timeline.series.peso);
}

// Revisar advertencias
if (timeline.advertencias.length > 0) {
  showWarningBanner(timeline.advertencias.join('. '));
}
```
