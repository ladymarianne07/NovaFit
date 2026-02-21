# 🚀 Guía paso a paso: NovaFitness en producción gratis (primera vez)

Esta guía está pensada para tu caso real:
- Frontend en **Vercel** (gratis)
- Backend FastAPI en **Render** (plan free)
- Base de datos: recomendación cloud gratis y opción local en **disco D**

---

## 0) Arquitectura recomendada (gratis y estable)

### ✅ Recomendado para pruebas con usuarios reales
- **Frontend:** Vercel
- **Backend:** Render Web Service
- **DB:** Supabase Postgres (free)

**Por qué:** Vercel no es ideal para correr tu backend FastAPI completo con SQLite persistente. En Vercel, el filesystem no es persistente para una app backend clásica, así que SQLite local no es buena opción allí.

### ⚠️ Opción local en tu PC (disco D)
- Puedes usar SQLite en `D:` si el backend corre en tu compu.
- Si apagas la PC, se cae la app.
- No es "producción" real para usuarios externos 24/7.

---

## 1) Preparar el repositorio

1. Verificá que todo esté en GitHub (branch principal actualizado).
2. Confirmá que `frontend` compila localmente.
3. Confirmá que backend levanta (`dev.py server`).

---

## 2) Crear backend gratis en Render

1. Entrá a Render: https://render.com
2. `New` → `Web Service`
3. Conectá tu repo de GitHub.
4. Configurá:
   - **Root Directory:** (vacío, raíz del repo)
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. En `Environment Variables`, agregá mínimo:
   - `DEBUG=false`
   - `SECRET_KEY=<una-clave-larga-y-random>`
   - `ALGORITHM=HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES=525600`
   - `DATABASE_URL=<ver paso 3>`
   - `ALLOWED_ORIGINS=["https://TU_FRONTEND.vercel.app"]`
6. Deploy.
7. Probá health:
   - `https://TU_BACKEND.onrender.com/health`

---

## 3) Base de datos (elige una opción)

## Opción A (recomendada): Supabase Postgres free

1. Entrá a https://supabase.com
2. Creá proyecto nuevo (free).
3. Copiá la connection string de Postgres.
4. En Render, poné:
   - `DATABASE_URL=postgresql://...`
5. Redeploy del backend.

**Ventaja:** disponible siempre, sin depender de tu PC.

## Opción B: SQLite local en disco D (tu requerimiento)

Si querés mantener DB en tu PC:

1. Creá carpeta:
   - `D:\NovaFitnessData\`
2. En `.env` local del backend:
   - `DATABASE_URL=sqlite:///D:/NovaFitnessData/novafitness.db`
3. Inicializá DB:
   - `python dev.py init-db`

### Importante
- Esto sirve si el backend también corre en tu PC.
- No es recomendable para app pública 24/7.
- Si usás Render, **esa ruta D no existe allá**.

---

## 4) Crear frontend en Vercel (gratis)

1. Entrá a https://vercel.com
2. `Add New` → `Project`
3. Importá tu repo de GitHub.
4. Configuración del proyecto:
   - **Framework:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. En Variables de entorno de Vercel, agregá:
   - `VITE_API_BASE_URL=https://TU_BACKEND.onrender.com`
6. Deploy.

---

## 5) Configuración CORS final (backend)

Tu backend debe permitir exactamente tu dominio de Vercel:

- `ALLOWED_ORIGINS=["https://TU_FRONTEND.vercel.app"]`

Si usás dominio custom, agregalo también:

- `ALLOWED_ORIGINS=["https://app.tudominio.com"]`

Luego redeploy backend.

---

## 6) Smoke test completo (5 minutos)

1. Abrí frontend Vercel.
2. Registrá usuario.
3. Iniciá sesión.
4. Creá un meal/evento.
5. Refrescá y verificá persistencia.
6. Revisá logs en Render por si hay errores 401/422/CORS.

---

## 7) Problemas comunes y solución rápida

### Error CORS
- `ALLOWED_ORIGINS` no coincide exactamente con URL de Vercel.
- Solución: copiar URL exacta + redeploy backend.

### Frontend funciona, pero API falla
- `VITE_API_BASE_URL` mal configurada o sin `https://`.
- Solución: corregir variable y redeploy en Vercel.

### En Vercel no abre rutas internas (ej: /dashboard)
- Necesitás rewrite SPA. Ya está resuelto con `frontend/vercel.json`.

### DB local en D no funciona en Render
- Es normal: Render no puede acceder a tu disco local.
- Solución: usar Postgres cloud (Supabase) para producción.

---

## 8) Checklist final de "listo para probar"

- [ ] Backend público responde `/health`
- [ ] Frontend en Vercel abre correctamente
- [ ] `VITE_API_BASE_URL` apunta al backend
- [ ] `ALLOWED_ORIGINS` correcto
- [ ] Registro/Login funcionando
- [ ] Persistencia de datos verificada

---

## Recomendación final

Para empezar rápido y gratis sin dolores:
- **Vercel (frontend) + Render (backend) + Supabase (DB)**

Si querés, en el próximo paso te guío en modo "acompañamiento en vivo" (pantalla por pantalla):
1) primero Render,
2) después Supabase,
3) y por último Vercel,
con validaciones en cada etapa.
