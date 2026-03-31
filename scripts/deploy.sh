#!/bin/bash
# INEC Election Results Agent - Deployment Helper Script

set -e

echo "🇳🇬 INEC Election Results Agent - Deployment Setup"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    git add .
    git commit -m "Initial commit: INEC Election Results Agent"
    echo -e "${GREEN}✓ Git repository initialized${NC}"
else
    echo -e "${GREEN}✓ Git repository exists${NC}"
fi

echo ""
echo "=================================================="
echo "STEP 1: Create GitHub Repository"
echo "=================================================="
echo ""
echo "1. Go to https://github.com/new"
echo "2. Create a new repository named 'inec-election-results'"
echo "3. Don't initialize with README (we have one)"
echo "4. Copy the repository URL"
echo ""
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo): " GITHUB_URL

if [ -n "$GITHUB_URL" ]; then
    git remote add origin "$GITHUB_URL" 2>/dev/null || git remote set-url origin "$GITHUB_URL"
    echo -e "${GREEN}✓ GitHub remote configured${NC}"
fi

echo ""
echo "=================================================="
echo "STEP 2: Create Neon PostgreSQL Database"
echo "=================================================="
echo ""
echo "1. Go to https://neon.tech"
echo "2. Sign up/Login with GitHub"
echo "3. Create a new project"
echo "4. Copy the connection string"
echo ""
read -p "Enter your Neon DATABASE_URL: " DATABASE_URL

if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL=$DATABASE_URL" > .env.production
    echo -e "${GREEN}✓ Database URL saved to .env.production${NC}"
    
    # Run migrations
    echo ""
    echo "Running database migrations..."
    cd backend
    DATABASE_URL="$DATABASE_URL" ../.venv/bin/alembic upgrade head 2>/dev/null || \
    DATABASE_URL="$DATABASE_URL" .venv/bin/alembic upgrade head 2>/dev/null || \
    echo -e "${YELLOW}⚠ Could not run migrations automatically. Run manually:${NC}"
    echo "  cd backend && DATABASE_URL=\"$DATABASE_URL\" alembic upgrade head"
    cd ..
fi

echo ""
echo "=================================================="
echo "STEP 3: Deploy Backend to Render"
echo "=================================================="
echo ""
echo "1. Go to https://render.com"
echo "2. Sign up/Login with GitHub"
echo "3. Click 'New' → 'Web Service'"
echo "4. Connect your GitHub repository"
echo "5. Configure:"
echo "   - Name: inec-backend"
echo "   - Root Directory: backend"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo "6. Add Environment Variables:"
echo "   - DATABASE_URL = (your Neon connection string)"
echo "   - ENVIRONMENT = production"
echo "   - CORS_ORIGINS = https://your-frontend.vercel.app"
echo ""
read -p "Enter your Render backend URL (after deployment): " RENDER_URL

echo ""
echo "=================================================="
echo "STEP 4: Deploy Frontend to Vercel"
echo "=================================================="
echo ""
echo "1. Go to https://vercel.com"
echo "2. Sign up/Login with GitHub"
echo "3. Click 'Add New' → 'Project'"
echo "4. Import your GitHub repository"
echo "5. Configure:"
echo "   - Framework Preset: Next.js"
echo "   - Root Directory: frontend"
echo "6. Add Environment Variable:"
echo "   - NEXT_PUBLIC_API_URL = $RENDER_URL"
echo ""
read -p "Enter your Vercel frontend URL (after deployment): " VERCEL_URL

echo ""
echo "=================================================="
echo "DEPLOYMENT SUMMARY"
echo "=================================================="
echo ""
echo -e "${GREEN}Database:${NC} Neon PostgreSQL"
echo -e "${GREEN}Backend:${NC} $RENDER_URL"
echo -e "${GREEN}Frontend:${NC} $VERCEL_URL"
echo ""
echo "=================================================="
echo "NEXT STEPS"
echo "=================================================="
echo ""
echo "1. Push code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Configure for deployment'"
echo "   git push -u origin main"
echo ""
echo "2. Update Render CORS_ORIGINS with your Vercel URL"
echo ""
echo "3. Run local poller:"
echo "   cd backend"
echo "   BACKEND_URL=$RENDER_URL python local_poller.py --dry-run"
echo ""
echo -e "${GREEN}✓ Deployment configuration complete!${NC}"
