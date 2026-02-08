# NovaFitness Deployment Guide

## Local Development Setup (Windows)

### Prerequisites
- Python 3.8+ 
- Git (optional)
- ngrok or Cloudflare Tunnel for public access

### Step 1: Setup Environment

```powershell
# Navigate to project directory
cd C:\Users\Maru\OneDrive\Escritorio\NovaFitness

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

```powershell
# Copy environment template
copy .env.example .env

# Edit .env file with your settings
notepad .env
```

**Required .env changes:**
```bash
# Generate a secure secret key (use online generator or Python)
SECRET_KEY=your-very-long-random-secret-key-at-least-32-characters

# Add your tunnel URLs when available
ALLOWED_ORIGINS=["http://localhost:3000", "https://abc123.ngrok.io"]
```

### Step 3: Initialize Database

```powershell
# Run database initialization
python dev.py init-db
```

### Step 4: Start Server

```powershell
# Start development server
python dev.py server
```

Server will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs` (Swagger UI)

## Public Access Setup

### Option 1: ngrok (Recommended for Development)

1. **Install ngrok:**
   - Download from https://ngrok.com/
   - Create free account
   - Follow setup instructions

2. **Start tunnel:**
   ```powershell
   # In new terminal (keep server running)
   ngrok http 8000
   ```

3. **Update configuration:**
   - Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`)
   - Add to `ALLOWED_ORIGINS` in `.env`
   - Restart server

### Option 2: Cloudflare Tunnel (Free, More Stable)

1. **Install cloudflared:**
   ```powershell
   # Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
   ```

2. **Login and setup:**
   ```powershell
   cloudflared tunnel login
   cloudflared tunnel create novafitness
   ```

3. **Create config file** (`config.yml`):
   ```yaml
   tunnel: <tunnel-id>
   credentials-file: C:\Users\<username>\.cloudflared\<tunnel-id>.json
   
   ingress:
     - hostname: novafitness.your-domain.com
       service: http://localhost:8000
     - service: http_status:404
   ```

4. **Start tunnel:**
   ```powershell
   cloudflared tunnel run novafitness
   ```

## Database Management

### SQLite (Current MVP Setup)
- **Location:** `novafitness.db` in project root
- **Backup:** Simply copy the `.db` file
- **Limitations:** Single writer, limited concurrency

### PostgreSQL Migration (Future)

When ready to migrate to PostgreSQL:

1. **Install PostgreSQL:**
   - Download from https://www.postgresql.org/
   - Create database: `novafitness`
   - Create user with permissions

2. **Update configuration:**
   ```bash
   # In .env
   DATABASE_URL=postgresql://username:password@localhost/novafitness
   ```

3. **Migrate data:**
   ```powershell
   # Export current data
   python -c "
   import sqlite3
   import json
   conn = sqlite3.connect('novafitness.db')
   # ... export script (create when needed)
   "
   
   # Recreate tables
   python dev.py init-db
   
   # Import data (script to be created)
   ```

## Production Considerations

### Security Hardening
1. **Environment Variables:**
   ```bash
   # Strong secret key
   SECRET_KEY=<use-python-secrets-module-to-generate>
   
   # Disable debug
   DEBUG=false
   
   # Restrict CORS origins
   ALLOWED_ORIGINS=["https://your-app-domain.com"]
   ```

2. **Database Security:**
   - Use PostgreSQL with proper user permissions
   - Enable SSL connections
   - Regular backups

3. **API Rate Limiting** (Future enhancement):
   ```python
   # Add to main.py
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   # Add to endpoints:
   @limiter.limit("5/minute")
   def login(...):
   ```

### Monitoring & Logging

1. **Add structured logging:**
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Health monitoring:**
   - Use `/health` endpoint
   - Monitor database connection
   - Track API response times

### Backup Strategy

1. **SQLite backup:**
   ```powershell
   # Daily backup script
   copy novafitness.db backups\novafitness_$(Get-Date -Format "yyyy-MM-dd").db
   ```

2. **PostgreSQL backup:**
   ```bash
   pg_dump novafitness > backup_$(date +%Y%m%d).sql
   ```

## PWA Integration Notes

### Frontend Connection
```javascript
// In your PWA, configure API base URL
const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://your-tunnel-url.ngrok.io'
  : 'http://localhost:8000';

// Authentication
localStorage.setItem('token', response.access_token);

// API calls
fetch(`${API_BASE}/events/`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
  }
});
```

### Service Worker Considerations
- Cache API responses for offline functionality
- Sync data when connection restored
- Handle token expiration gracefully

## Troubleshooting

### Common Issues

1. **CORS errors in PWA:**
   - Ensure tunnel URL is in `ALLOWED_ORIGINS`
   - Check `.env` file is loaded properly

2. **Database locked (SQLite):**
   - Only one writer at a time
   - Close all connections properly
   - Consider PostgreSQL for multiple users

3. **Token expiration:**
   - Default: 24 hours (for PWA convenience)
   - Implement refresh logic in frontend

4. **Import errors:**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

### Development Commands

```powershell
# Full setup from scratch
python dev.py setup
python dev.py init-db
python dev.py server

# Run tests
python dev.py test

# Reset database (careful!)
del novafitness.db
python dev.py init-db

# Check logs
# Logs appear in terminal where server is running
```

## Scaling Considerations

### Current Limits (~10 users)
- SQLite handles this well
- Single server instance sufficient
- Local deployment acceptable

### Future Growth (>10 users)
- Migrate to PostgreSQL
- Consider cloud deployment
- Add Redis for caching
- Implement proper CI/CD
- Add monitoring (Prometheus/Grafana)

### Cloud Migration Path
1. **Container deployment:**
   ```dockerfile
   FROM python:3.11-slim
   COPY . /app
   WORKDIR /app
   RUN pip install -r requirements.txt
   CMD ["python", "-m", "app.main"]
   ```

2. **Database migration:**
   - Export SQLite data
   - Setup cloud PostgreSQL
   - Import data
   - Update connection string

3. **Configuration management:**
   - Use cloud secrets management
   - Environment-specific configs
   - Load balancing for multiple instances