# Auditoría de Código Muerto — NovaFitness Backend
**Fecha:** 2026-04-04 | **Tipo:** Solo lectura

## Resumen Ejecutivo

Se identificaron **2 elementos de código muerto** en el proyecto. El resto del código está activamente utilizado.

---

## 1. Import no utilizado: `cast` en `app/api/routine.py`

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/api/routine.py` |
| **Línea** | 6 |
| **Elemento** | `cast` (importado de `typing`) |
| **Estado** | Importado pero nunca utilizado |

**Evidencia:** Búsqueda por `cast(` en el archivo no encontró ningún uso. El import está declarado en la línea 6 pero ninguna función del archivo lo utiliza.

**Acción sugerida:** Eliminar la línea de import.

---

## 2. Función no invocada: `drop_tables()` en `app/db/database.py`

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/db/database.py` |
| **Líneas** | 183–185 |
| **Elemento** | Función `drop_tables()` |
| **Estado** | Definida pero nunca llamada |

**Código:**
```python
def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
```

**Evidencia:** Búsqueda global de `drop_tables(` encontró únicamente la definición en `database.py`. No existe ninguna invocación en todo el proyecto.

**Acción sugerida:** Si no es parte de scripts de mantenimiento activos:
- **Opción A:** Eliminar la función
- **Opción B:** Mover a un módulo de administración/mantenimiento separado con documentación explícita sobre cuándo usarla
- **Opción C:** Documentar como herramienta de emergencia con advertencias explícitas

---

## Análisis de Archivos sin Código Muerto

| Archivo | Estado |
|---------|--------|
| `app/main.py` | ✅ Todos los routers registrados vía `include_router()` |
| `app/constants.py` | ✅ Todas las clases constantes importadas y usadas |
| `app/api/diet.py` | ✅ Los 8 endpoints activos y decorados |
| `app/api/routine.py` | ✅ Los 6 endpoints activos (excepto import `cast`) |
| `app/db/models.py` | ✅ Todos los modelos usados en operaciones ORM |
| `app/schemas/diet.py` | ✅ Todos los schemas usados en validación |
| `app/schemas/routine.py` | ✅ Todos los schemas usados en validación |
| `app/services/diet_service.py` | ✅ Todos los métodos públicos y privados invocados |
| `app/services/routine_service.py` | ✅ Todos los métodos públicos y privados invocados |
| `app/db/database.py` | ⚠️ `drop_tables()` sin referencias |

---

## Tabla Resumen

| Elemento | Archivo | Línea | Tipo | Riesgo de eliminación |
|----------|---------|-------|------|----------------------|
| `cast` (import) | `app/api/routine.py` | 6 | Import | **Ninguno** |
| `drop_tables()` | `app/db/database.py` | 183–185 | Función | **Bajo** (verificar scripts externos) |
