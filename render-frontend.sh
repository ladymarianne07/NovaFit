# Render.com deployment configuration for NovaFitness Frontend

# Build Command for Frontend
echo "Installing Node.js dependencies..."
cd frontend
npm install

echo "Building React application..."
npm run build

# Static site - Render will serve the built files automatically