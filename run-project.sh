#!/bin/bash

# INEC Election Results Agent - Project Runner
# This script helps start all services for the project

set -e

echo "🇳🇬 INEC Election Results Agent - Starting Services"
echo "=================================================="

# Check Docker
echo ""
echo "1. Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "   On macOS: Open Docker Desktop application"
    exit 1
fi
echo "✅ Docker is running"

# Start database services
echo ""
echo "2. Starting PostgreSQL and Redis..."
docker compose up -d
echo "✅ Database services started"

# Wait for PostgreSQL to be ready
echo ""
echo "3. Waiting for PostgreSQL to be ready..."
until docker exec inec_postgres pg_isready -U postgres -d inec_elections > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Run migrations
echo ""
echo "4. Running database migrations..."
cd backend
.venv/bin/alembic upgrade head
cd ..
echo "✅ Migrations complete"

# Start backend
echo ""
echo "5. Starting FastAPI backend..."
echo "   Backend will run at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo ""
echo "6. Starting Next.js frontend..."
echo "   Frontend will run at: http://localhost:3000"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================================="
echo "🚀 All services started!"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================================="

# Wait for interrupt
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker compose down; echo 'Done.'" INT
wait
