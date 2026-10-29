# Deployment Guide

VPS deployment for **boxitracker.com**.

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              VPS (160.191.162.101)           │
                    │                                             │
Internet ──────────▶│  Nginx (ports 80/443)                       │
                    │    ├── / ──────────▶ Frontend (Next.js:3000)│
                    │    ├── /api/ ──────▶ Backend (FastAPI:8000) │
                    │    ├── /docs ──────▶ Backend                │
                    │    └── /health ────▶ Backend                │
                    │                                             │
                    │  PostgreSQL 15 (internal:5432)              │
                    │  Redis 7 (internal:6379)                    │
                    │  Certbot (auto SSL renewal)                 │
                    └─────────────────────────────────────────────┘
```

## Services

| Service | Image | Container Name | Purpose |
|---------|-------|----------------|---------|
| Nginx | `nginx:alpine` | `inec_nginx` | Reverse proxy, SSL termination, rate limiting |
| Certbot | `certbot/certbot` | `inec_certbot` | Let's Encrypt SSL certificate management |
| Backend | Custom (Python 3.11) | `inec_backend` | FastAPI REST API |
| Frontend | Custom (Node 20) | `inec_frontend` | Next.js dashboard |
| PostgreSQL | `postgres:15-alpine` | `inec_postgres` | Primary database |
| Redis | `redis:7-alpine` | `inec_redis` | Cache / Celery broker |

## Prerequisites

- VPS with SSH access (currently `root@160.191.162.101`)
- Domain `boxitracker.com` pointing to the VPS IP
- Docker and Docker Compose installed on the VPS

## First-Time Deployment

### 1. Point DNS to VPS

Create an A record for your domain:

```
boxitracker.com  →  160.191.162.101
```

Wait for DNS propagation (can take up to 48h, usually minutes).

### 2. Run the deploy script

From your local machine (project root):

```bash
chmod +x scripts/deploy-vps.sh
./scripts/deploy-vps.sh
```

This script will:
1. Install Docker on the VPS (if not present)
2. Copy project files via rsync
3. Build and start all containers
4. Run database migrations

### 3. Set up SSL certificates (first time only)

SSH into the VPS and obtain the initial certificate:

```bash
ssh root@160.191.162.101
cd /opt/inec-election-results

# First, temporarily comment out the SSL server block in nginx.conf
# or start nginx with HTTP only to pass the ACME challenge.

# Option A: Use certbot standalone (stop nginx first)
docker compose -f docker-compose.prod.yml stop nginx
docker run --rm -p 80:80 \
  -v ./certbot/conf:/etc/letsencrypt \
  -v ./certbot/www:/var/www/certbot \
  certbot/certbot certonly \
  --standalone \
  -d boxitracker.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Restart everything
docker compose -f docker-compose.prod.yml up -d
```

After the initial certificate is obtained, Certbot auto-renews every 12 hours via the container.

### 4. Configure environment variables

SSH into the VPS and create the backend `.env`:

```bash
ssh root@160.191.162.101
cd /opt/inec-election-results/backend

cat > .env << 'EOF'
ENVIRONMENT=production
DEBUG=false

# Database (matches docker-compose.prod.yml)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=inec_elections
DB_USER=postgres
DB_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# OpenAI (for GPT-4 Vision OCR)
OPENAI_API_KEY=sk-your-key-here

# CORS
CORS_ORIGINS=["https://boxitracker.com","http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
```

Then restart the backend:

```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Subsequent Deployments

From your local machine:

```bash
./scripts/deploy-vps.sh
```

Or manually:

```bash
# Copy updated files
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='.next' \
  --exclude='__pycache__' --exclude='.venv' --exclude='*.pyc' \
  --exclude='.env' --exclude='logs/*' --exclude='backend/data/result_sheets/*' \
  ./ root@160.191.162.101:/opt/inec-election-results/

# SSH in and rebuild
ssh root@160.191.162.101
cd /opt/inec-election-results
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations if needed
docker exec inec_backend alembic upgrade head
```

## Managing the Deployment

### Check status

```bash
ssh root@160.191.162.101
cd /opt/inec-election-results
docker compose -f docker-compose.prod.yml ps
```

### View logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart a service

```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Stop everything

```bash
docker compose -f docker-compose.prod.yml down
```

### Run database migrations

```bash
docker exec inec_backend alembic upgrade head
```

### Access the database

```bash
docker exec -it inec_postgres psql -U postgres -d inec_elections
```

## URLs

| URL | Description |
|-----|-------------|
| `https://boxitracker.com` | Frontend dashboard |
| `https://boxitracker.com/api/v1/...` | REST API |
| `https://boxitracker.com/docs` | Swagger API docs |
| `https://boxitracker.com/redoc` | ReDoc API docs |
| `https://boxitracker.com/health` | Health check |

## Nginx Configuration

The Nginx reverse proxy handles:

- **HTTP → HTTPS redirect** on port 80
- **SSL termination** with Let's Encrypt certificates (auto-renewed)
- **Rate limiting** on `/api/` routes (10 req/s per IP, burst 20)
- **Security headers** (HSTS, X-Frame-Options, X-Content-Type-Options, XSS protection)
- **Routing**: `/api/`, `/docs`, `/redoc`, `/health` → backend; everything else → frontend

## SSL Certificate Renewal

Certbot runs inside a container and checks for renewal every 12 hours. Nginx reloads every 6 hours to pick up new certificates. This is fully automatic — no manual intervention needed.

To force a renewal:

```bash
docker exec inec_certbot certbot renew --force-renewal
docker exec inec_nginx nginx -s reload
```

## Troubleshooting

### Site not loading

1. Check DNS: `dig boxitracker.com` should return `160.191.162.101`
2. Check containers: `docker compose -f docker-compose.prod.yml ps`
3. Check nginx logs: `docker compose -f docker-compose.prod.yml logs nginx`

### SSL certificate errors

```bash
# Check certificate status
docker exec inec_certbot certbot certificates

# Re-issue if needed
docker compose -f docker-compose.prod.yml stop nginx
docker exec inec_certbot certbot certonly --standalone \
  -d boxitracker.com --force-renewal
docker compose -f docker-compose.prod.yml start nginx
```

### Backend 502 errors

The backend container may have crashed:

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50
docker compose -f docker-compose.prod.yml restart backend
```

### Database connection issues

```bash
# Check postgres is running
docker compose -f docker-compose.prod.yml logs postgres

# Verify connectivity from backend
docker exec inec_backend python -c "
from app.db.session import engine
import asyncio
async def check():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('DB OK')
asyncio.run(check())
"
```

### Disk space

```bash
# Check disk usage
df -h

# Clean up Docker resources
docker system prune -a --volumes
```
