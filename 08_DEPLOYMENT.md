# 08 — Deployment (Docker Compose, Nginx, Backup)

> Konfigurasi deployment SISKONKIN di VPS, fully containerized via Docker Compose, dengan Nginx reverse proxy di port 3399.

---

## 1. Arsitektur Deployment

```
                       Internet / Intranet PLN
                              │
                              ▼
                      ┌───────────────┐
                      │  VPS Public   │
                      │  Port 3399    │
                      └───────┬───────┘
                              │
                      ┌───────▼───────┐
                      │ Nginx Proxy   │  (di host atau dalam container)
                      └───────┬───────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │   Frontend   │    │   Backend    │    │  WebSocket   │
 │   (Nginx     │    │  (FastAPI    │    │   (FastAPI   │
 │   serving    │    │   uvicorn)   │    │    /ws)      │
 │   /dist)     │    │              │    │              │
 └──────────────┘    └──────┬───────┘    └──────┬───────┘
                            │                   │
                            └─────────┬─────────┘
                                      │
                            ┌─────────▼──────────┐
                            │    PostgreSQL 16   │
                            │   + pgvector       │
                            │   (volume mounted) │
                            └────────────────────┘
                                      │
                            ┌─────────┴──────────┐
                            │      Redis 7       │
                            │   (cache, queue)   │
                            └────────────────────┘
                                      │
                            ┌─────────┴──────────┐
                            │  OpenRouter API    │
                            │   (external)       │
                            └────────────────────┘
```

---

## 2. Struktur Folder Project

```
siskonkin/
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                       # config, security, db
│   │   ├── models/                     # SQLAlchemy models
│   │   ├── schemas/                    # Pydantic schemas
│   │   ├── api/                        # FastAPI routers
│   │   ├── services/                   # business logic + ai/
│   │   ├── websocket/
│   │   └── scripts/
│   │       ├── seed_konkin_2026.py
│   │       └── index_pedoman.py
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── src/                            # (lihat 05_FRONTEND_ARCHITECTURE.md)
│   └── public/
├── nginx/
│   ├── Dockerfile                      # opsional jika pakai Nginx custom image
│   ├── nginx.conf
│   ├── conf.d/
│   │   └── siskonkin.conf
│   └── ssl/                            # cert files (gitignored)
├── infra/
│   ├── backup/
│   │   ├── pg_backup.sh
│   │   └── restore.sh
│   └── monitoring/
│       └── prometheus.yml              # opsional
├── docs/                               # blueprint markdown ini
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.prod.yml             # override untuk prod
├── docker-compose.dev.yml              # override untuk dev
├── Makefile                            # shortcut command
└── README.md
```

---

## 3. `.env.example`

```bash
# === APP ===
APP_NAME=SISKONKIN
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=change-me-to-random-32-char-string
APP_BASE_URL=https://siskonkin.tenayan.local
TZ=Asia/Jakarta

# === DATABASE ===
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=siskonkin
POSTGRES_USER=siskonkin
POSTGRES_PASSWORD=change-me-strong-password
DATABASE_URL=postgresql+asyncpg://siskonkin:change-me-strong-password@db:5432/siskonkin

# === REDIS ===
REDIS_URL=redis://redis:6379/0

# === JWT ===
JWT_SECRET_KEY=change-me-to-different-random-string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=14

# === CORS ===
CORS_ORIGINS=https://siskonkin.tenayan.local

# === OPENROUTER (AI) ===
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL_FAST=google/gemini-2.5-flash
AI_MODEL_SMART=anthropic/claude-sonnet-4
AI_EMBEDDING_MODEL=openai/text-embedding-3-small
AI_RATE_LIMIT_PER_MIN=20

# === EMAIL (untuk notifikasi) ===
SMTP_HOST=mail.tenayan.local
SMTP_PORT=587
SMTP_USER=notif@siskonkin.local
SMTP_PASSWORD=...
SMTP_FROM=SISKONKIN <notif@siskonkin.local>

# === FRONTEND BUILD ===
VITE_API_BASE_URL=https://siskonkin.tenayan.local/api/v1
VITE_WS_BASE_URL=wss://siskonkin.tenayan.local/ws

# === BACKUP ===
BACKUP_DIR=/var/backups/siskonkin
BACKUP_RETENTION_DAYS=30
```

---

## 4. `docker-compose.yml`

```yaml
version: "3.9"

services:
  db:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    container_name: siskonkin-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      TZ: ${TZ}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infra/db/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - siskonkin-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    container_name: siskonkin-redis
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redisdata:/data
    networks:
      - siskonkin-net

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    container_name: siskonkin-backend
    env_file: .env
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app                  # dev only; di prod build into image
      - backend-logs:/var/log/siskonkin
    networks:
      - siskonkin-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_BASE_URL: ${VITE_API_BASE_URL}
        VITE_WS_BASE_URL: ${VITE_WS_BASE_URL}
    restart: unless-stopped
    container_name: siskonkin-frontend
    networks:
      - siskonkin-net

  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    container_name: siskonkin-nginx
    ports:
      - "3399:80"
      # - "443:443"                      # uncomment kalau pakai SSL terminasi di sini
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx-logs:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - siskonkin-net

volumes:
  pgdata:
  redisdata:
  backend-logs:
  nginx-logs:

networks:
  siskonkin-net:
    driver: bridge
```

---

## 5. `backend/Dockerfile`

```dockerfile
# Multi-stage build untuk production
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install -e . && pip install uvicorn[standard] gunicorn

COPY . .

EXPOSE 8000

# Production: gunicorn dengan uvicorn worker
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "/var/log/siskonkin/access.log", \
     "--error-logfile", "/var/log/siskonkin/error.log"]
```

---

## 6. `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

COPY . .

ARG VITE_API_BASE_URL
ARG VITE_WS_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL

RUN pnpm build

# Serve stage — pakai Nginx ringan
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## 7. `nginx/conf.d/siskonkin.conf`

```nginx
# Upstreams
upstream backend_api {
    server backend:8000;
    keepalive 32;
}

upstream frontend_static {
    server frontend:80;
}

server {
    listen 80;
    server_name siskonkin.tenayan.local _;
    
    client_max_body_size 5m;
    client_body_timeout 60s;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        application/javascript application/json application/xml
        text/css text/javascript text/plain text/xml
        font/woff font/woff2 image/svg+xml;
    
    # Rate limiting (define di nginx.conf bagian http {})
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/s;
    limit_req_zone $binary_remote_addr zone=ai:10m rate=20r/m;
    
    # === API ===
    location /api/v1/ai {
        limit_req zone=ai burst=5 nodelay;
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
    
    # === WebSocket ===
    location /ws/ {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # === Frontend (SPA) ===
    location / {
        proxy_pass http://frontend_static;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Cache untuk asset statis
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?|ttf|eot)$ {
        proxy_pass http://frontend_static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 8. `Makefile` Shortcut

```makefile
.PHONY: help up down restart logs migrate seed shell-be shell-fe backup index-pedoman

help:
	@echo "make up           — start all services"
	@echo "make down         — stop all"
	@echo "make logs s=...   — tail logs of service"
	@echo "make migrate      — run alembic migration"
	@echo "make seed         — seed Konkin 2026 master data"
	@echo "make index-pedoman — re-index Pedoman ke pgvector"
	@echo "make backup       — manual DB backup"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f $(s)

migrate:
	docker compose exec backend alembic upgrade head

makemigration:
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

seed:
	docker compose exec backend python -m app.scripts.seed_konkin_2026

index-pedoman:
	docker compose exec backend python -m app.scripts.index_pedoman

shell-be:
	docker compose exec backend bash

shell-fe:
	docker compose exec frontend sh

backup:
	bash infra/backup/pg_backup.sh

restore:
	bash infra/backup/restore.sh $(file)
```

---

## 9. Backup Strategy

### `infra/backup/pg_backup.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/siskonkin}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="siskonkin_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

docker compose exec -T db \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --no-owner --no-acl \
    | gzip -9 > "$BACKUP_DIR/$FILENAME"

echo "Backup created: $BACKUP_DIR/$FILENAME ($(du -h "$BACKUP_DIR/$FILENAME" | cut -f1))"

# Cleanup old backups
find "$BACKUP_DIR" -name "siskonkin_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete

echo "Cleanup done. Current backups:"
ls -lh "$BACKUP_DIR" | tail -n +2
```

### Schedule via Cron (di host VPS):
```cron
# Daily backup at 2 AM
0 2 * * * cd /opt/siskonkin && /opt/siskonkin/infra/backup/pg_backup.sh >> /var/log/siskonkin-backup.log 2>&1

# Weekly: copy ke external storage (rsync ke NAS atau S3-compatible)
0 3 * * 0 rsync -av /var/backups/siskonkin/ user@nas.tenayan.local:/backup/siskonkin/
```

### Restore:
```bash
gunzip -c siskonkin_20260711_020000.sql.gz | \
  docker compose exec -T db psql -U siskonkin -d siskonkin
```

---

## 10. Monitoring & Logging

### Logging
- Backend: structured JSON logs ke `stdout` + file di volume
- Nginx: access + error logs di volume
- PostgreSQL: log slow queries (> 500ms)

### Health Checks
- `/api/v1/health` — basic liveness
- `/api/v1/health/detail` — DB, Redis, OpenRouter connectivity

### Optional: Prometheus + Grafana
Setup di phase 2 setelah aplikasi stabil. Metrics:
- Request rate per endpoint
- Latency p50/p95/p99
- DB connection pool usage
- AI token consumption

---

## 11. Initial Deployment Steps di VPS

```bash
# 1. SSH ke VPS
ssh user@vps-tenayan

# 2. Install Docker (Ubuntu 22.04)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Clone repo
sudo mkdir -p /opt/siskonkin
sudo chown $USER:$USER /opt/siskonkin
cd /opt/siskonkin
git clone https://github.com/cv-panda-global-teknologi/siskonkin.git .

# 4. Setup environment
cp .env.example .env
nano .env                                # isi semua secret

# 5. Build & start
docker compose pull
docker compose up -d --build

# 6. Run migrations
make migrate

# 7. Seed master data Konkin 2026
make seed

# 8. Index Pedoman ke pgvector (untuk RAG)
make index-pedoman

# 9. Setup cron untuk backup
crontab -e
# (paste cron line di atas)

# 10. Setup firewall (UFW)
sudo ufw allow 22/tcp
sudo ufw allow 3399/tcp
sudo ufw enable

# 11. Verifikasi
curl http://localhost:3399/api/v1/health
```

---

## 12. Update / Rolling Deploy

```bash
cd /opt/siskonkin

# 1. Pull update
git pull origin main

# 2. Rebuild yang berubah
docker compose build backend frontend

# 3. Migrasi DB jika ada
docker compose exec backend alembic upgrade head

# 4. Restart layanan secara graceful
docker compose up -d --no-deps backend
docker compose up -d --no-deps frontend
docker compose restart nginx

# 5. Verifikasi
curl http://localhost:3399/api/v1/health
```

---

## 13. Production Checklist

Sebelum go-live, pastikan:

- [ ] Semua secret di `.env` adalah **strong & unique** (tidak default)
- [ ] PostgreSQL bukan exposed ke public — hanya internal network
- [ ] Backup harian sudah jalan & test restore minimal sekali
- [ ] SSL certificate setup (Let's Encrypt atau internal CA PLN)
- [ ] Firewall hanya buka port yang perlu (22 untuk SSH, 3399 atau 443)
- [ ] Log rotation setup (logrotate untuk file logs)
- [ ] Monitoring health check eksternal (UptimeRobot atau internal)
- [ ] User admin pertama sudah dibuat dengan password kuat
- [ ] Master data Konkin 2026 sudah ter-seed lengkap
- [ ] Pedoman Konkin sudah ter-index ke pgvector untuk RAG
- [ ] OpenRouter API key valid & quota tersedia
- [ ] Test login + create assessment + submit minimal sekali end-to-end
- [ ] Documentation user manual sudah dibuat (terpisah dari blueprint ini)

---

**Selanjutnya:** [`09_DEVELOPMENT_ROADMAP.md`](09_DEVELOPMENT_ROADMAP.md) — fase pengembangan.
