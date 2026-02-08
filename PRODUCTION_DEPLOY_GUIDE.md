# NovaFitness Production Deployment Guide

## 🚀 Deploying to Production with Render.com

### Prerequisites
1. GitHub account with your NovaFitness repository
2. Render.com account (free)

### Step 1: Prepare Repository
```bash
git init
git add .
git commit -m "Initial commit - NovaFitness app ready for production"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy Backend (FastAPI)

1. **Go to Render.com Dashboard**
2. **Create New Web Service**
3. **Connect GitHub Repository**
4. **Configure Backend Service:**
   - **Name:** novafitness-backend
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
   
5. **Set Environment Variables:**
   ```
   DATABASE_URL=sqlite:///./novafitness_prod.db
   SECRET_KEY=your-super-secret-production-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

6. **Deploy** - Render will automatically build and deploy your backend

### Step 3: Deploy Frontend (React)

1. **Create New Static Site**
2. **Connect Same GitHub Repository**
3. **Configure Frontend Service:**
   - **Name:** novafitness-frontend
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/build`
   - **Instance Type:** Free

4. **Set Environment Variables:**
   ```
   REACT_APP_API_URL=https://novafitness-backend.onrender.com
   ```

### Step 4: Update Frontend API Configuration

Update `frontend/src/services/api.ts`:
```typescript
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://novafitness-backend.onrender.com'  // Your backend URL
  : 'http://localhost:8000';
```

### Step 5: Production URLs

After deployment, your app will be available at:
- **Frontend:** `https://novafitness-frontend.onrender.com`
- **Backend:** `https://novafitness-backend.onrender.com`
- **API Docs:** `https://novafitness-backend.onrender.com/docs`

### Step 6: Test Production Flow

1. Visit your frontend URL
2. Create a test account with biometric data
3. Verify dashboard shows correct BMR/TDEE calculations
4. Check backend `/users/all` endpoint to see database entries

## 🔒 Security Notes for Production

- Change SECRET_KEY to a strong, random string
- Set up proper CORS origins
- Consider using PostgreSQL instead of SQLite for better performance
- Implement rate limiting
- Add proper error logging

## 📊 Monitoring Your App

- Render provides built-in monitoring
- Check logs in Render dashboard
- Monitor app performance and uptime

## 🎉 Your NovaFitness App is Live!

Share your production URL with users and start collecting real biometric data!