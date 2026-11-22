# EncroWatch AI — Production Deployment Guide

> **Enterprise Urban Accessibility & Municipal Incident Management Platform**  
> Operational DevOps, Containerization, and Deployment Specification

---

## 1. System Architecture Overview

EncroWatch AI operates as a containerized, security-hardened three-tier architecture:

```
[ Public Internet / Clients ]
               │
        Port 80 / 443
               ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Frontend Web & Reverse Proxy Tier (Nginx on Alpine)      │
│    - Serves optimized React 18 + Vite production build      │
│    - Applies security headers (HSTS, CSP, Permissions, etc.) │
│    - Proxies /api/ requests to Backend (Port 8000)          │
│    - Proxies /ws/ persistent WebSockets to Backend          │
│    - Proxies /uploads/ media files with caching headers     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Internal Bridge Network
                               │ (encrowatch_prod_network)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Application & AI Engine Tier (FastAPI + Python 3.12)     │
│    - Runs as non-root user 'encrowatch' (UID 1001)          │
│    - Pretrained YOLOv5n-ONNX Object Detection Engine        │
│    - OpenCV Spatial Corridor & Walkability Analysis Pipeline│
│    - JWT Cryptographic Role Authorization Engine            │
│    - SHA-256 Tamper-Evident Cryptographic Audit Chaining    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Internal Bridge Network
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Persistence Tier (MongoDB 7.0 Enterprise Community)       │
│    - Isolated from public host network (no exposed ports)   │
│    - Persistent Named Volumes for data durability           │
│    - Native healthcheck via mongosh ping                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### Local Container Deployment:
- **Docker Desktop** (Engine 24.0+, Compose v2/v5+)
- **Windows PowerShell** or bash
- **CPU:** Minimum 2 cores (4 cores recommended for concurrent AI inference)
- **RAM:** Minimum 4 GB available memory
- **Disk:** 10 GB free SSD storage

### Standalone Local Development:
- **Python 3.12+** (with `pip`, `venv`)
- **Node.js 20+** (with `npm`)
- **MongoDB 7.0+** running locally on port `27017`

---

## 3. Environment & Secrets Setup

1. Copy `.env.example` to create your active `.env` file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Generate a cryptographically secure 256-bit `SECRET_KEY` and database credentials:
   ```powershell
   python scripts/generate_secret_key.py
   ```

3. Update `.env` with the generated values:
   ```ini
   ENVIRONMENT=production
   PORT=80
   SECRET_KEY=paste_your_generated_64_character_hex_key_here
   MONGODB_URI=mongodb://mongodb:27017
   DATABASE_NAME=encrowatch_ai_db
   CORS_ORIGINS=http://localhost,https://encrowatch.yourdomain.com
   ALLOW_DEMO_SWITCH=false
   ALLOW_DEMO_MODE=false
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

> [!CAUTION]
> Never commit `.env` containing live secrets to Git. The `.gitignore` file is pre-configured to strictly exclude `.env`, `*.env`, and `backups/`.

---

## 4. Local Container Deployment (Development / Evaluation)

To spin up all services with local development port exposures (Backend on `127.0.0.1:8000`, Frontend on `127.0.0.1:5173`, MongoDB on `127.0.0.1:27017`):

```powershell
# 1. Validate Docker Compose configuration
docker compose config

# 2. Build and launch containers
docker compose up -d --build

# 3. View live startup logs
docker compose logs -f

# 4. Verify container status and health
docker compose ps
```

Access the services:
- **Web Application & UI:** `http://localhost:5173`
- **Backend API & Health:** `http://localhost:8000/api/health`
- **Interactive OpenAPI Docs:** `http://localhost:8000/docs`

---

## 5. Production Hardened Deployment

The production deployment uses `docker-compose.prod.yml`. In this mode:
- External access is restricted strictly to Port 80 (Nginx).
- Backend (Port 8000) and MongoDB (Port 27017) are **internal only**.
- Memory and CPU limits are strictly enforced.

```powershell
# 1. Validate production compose configuration
docker compose -f docker-compose.prod.yml config

# 2. Start production stack in detached daemon mode
docker compose -f docker-compose.prod.yml up -d --build

# 3. Verify healthchecks
docker compose -f docker-compose.prod.yml ps
```

---

## 6. Healthchecks & Diagnostics

All containers include automated healthchecks configured in Docker Compose:

| Container | Healthcheck Command | Interval | Retries |
| :--- | :--- | :--- | :--- |
| `mongodb` | `mongosh --eval "db.adminCommand('ping')"` | 10s | 5 |
| `backend` | `curl -f http://localhost:8000/api/health` | 15s | 3 |
| `frontend`| `wget -q --spider http://localhost/` | 15s | 3 |

To check the operational health of the live application:
```powershell
# Using PowerShell Invoke-RestMethod
Invoke-RestMethod -Uri http://localhost:8000/api/health

# Or using curl
curl http://localhost:8000/api/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "platform": "EncroWatch AI",
  "version": "2.0.0",
  "database_mode": "mongodb",
  "ai_engine": "OpenCV-Vision-Pipeline + Modular-YOLO-Hook",
  "security_hardened": true
}
```

---

## 7. Container Logs & Troubleshooting

```powershell
# Tail logs for all containers
docker compose logs -f

# Tail logs specifically for the AI backend
docker compose logs -f backend

# Tail logs specifically for the Nginx frontend reverse proxy
docker compose logs -f frontend

# Tail MongoDB database logs
docker compose logs -f mongodb
```

### Common Issues & Resolutions:

1. **Port 80 or 5173 Conflict:**
   If port 80 is occupied by IIS or another service, change `PORT=8080` in `.env`.
2. **MongoDB Connection Refused:**
   Ensure the `mongodb` service is marked `healthy` before backend starts (`depends_on: condition: service_healthy` handles this automatically).
3. **OpenCV Memory Overhead:**
   If running on constrained nodes (< 2 GB RAM), ensure swap is enabled or allocate at least 2 GB memory to the backend container in `docker-compose.prod.yml`.

---

## 8. Graceful Shutdown & Maintenance

To stop the application without losing any database records or uploaded evidence:

```powershell
# Gracefully stop containers (preserves all named volumes and data)
docker compose down

# For production stack
docker compose -f docker-compose.prod.yml down
```

> [!WARNING]
> Never run `docker compose down -v` in production. The `-v` flag deletes named persistent volumes, which destroys database records and uploaded evidence.
