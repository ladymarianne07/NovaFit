# USDA FoodData Central - Postman

Archivos incluidos:
- `USDA_FoodData_Central.postman_collection.json`
- `USDA_FoodData_Central.postman_environment.json`

## Uso rápido (2 minutos)
1. Abrí Postman.
2. Importá ambos archivos (`collection` y `environment`).
3. Seleccioná el environment **USDA FoodData Central - Local**.
4. Cargá `USDA_API_KEY` en el environment.
5. Abrí `01 - Search Foods (POST)` y presioná **Send**.

## Flujo recomendado
1. Ejecutá `01 - Search Foods (POST)` con tu texto (`query`).
2. El test guarda automáticamente el primer `fdcId` encontrado en variable de entorno.
3. Ejecutá `03 - Get Food by FDC ID` para ver detalle completo nutricional.
4. Si querés traer varios resultados en lote, usá `04 - Get Multiple Foods`.

## Variables que más vas a editar
- `query` (ej: `baked potato`, `salmon`, `coffee with milk`)
- `pageSize`
- `pageNumber`
- body JSON en cada request

## Notas
- Todas las requests usan `api_key` por query param.
- Si recibís 401/403, revisá `USDA_API_KEY`.
- Si recibís resultados raros, probá queries más específicas (ej. `grilled fish fillet` en lugar de `fish`).
