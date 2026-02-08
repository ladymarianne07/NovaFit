# Render.com deployment configuration for NovaFitness Backend

# Build Command for Backend
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start Command for Backend (will be configured in Render web interface)
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT