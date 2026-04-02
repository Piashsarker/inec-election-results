#!/bin/bash
# VPS Deployment Script for INEC Election Results Agent
# Usage: ./scripts/deploy-vps.sh

set -e

VPS_HOST="160.191.162.101"
VPS_USER="root"
APP_DIR="/opt/inec-election-results"

echo "🇳🇬 INEC Election Results Agent - VPS Deployment"
echo "=================================================="
echo "Target: $VPS_USER@$VPS_HOST"
echo ""

# Step 1: Setup VPS
echo "📦 Step 1: Setting up VPS environment..."
ssh $VPS_USER@$VPS_HOST << 'ENDSSH'
# Update system
apt-get update && apt-get upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
fi

# Create app directory
mkdir -p /opt/inec-election-results
echo "✅ VPS environment ready"
ENDSSH

# Step 2: Copy project files
echo ""
echo "📤 Step 2: Copying project files to VPS..."
rsync -avz --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs/*' \
    --exclude='backend/data/result_sheets/*' \
    ./ $VPS_USER@$VPS_HOST:$APP_DIR/

echo "✅ Files copied"

# Step 3: Deploy with Docker Compose
echo ""
echo "🚀 Step 3: Deploying application..."
ssh $VPS_USER@$VPS_HOST << ENDSSH
cd $APP_DIR

# Stop existing containers
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start containers
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Run database migrations
docker exec inec_backend alembic upgrade head

# Show status
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://$VPS_HOST:3000"
echo "   Backend API: http://$VPS_HOST:8000"
echo "   API Docs: http://$VPS_HOST:8000/docs"
ENDSSH

echo ""
echo "=================================================="
echo "🎉 Deployment finished!"
echo ""
echo "🌐 Your application is now live at:"
echo "   Frontend: http://$VPS_HOST:3000"
echo "   Backend API: http://$VPS_HOST:8000"
echo "   API Docs: http://$VPS_HOST:8000/docs"
