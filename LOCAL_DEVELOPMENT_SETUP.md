# Local Development Setup (No Docker)

This guide explains how to run **RakshAI** entirely on your local machine without Docker.

## Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **Git** (for version control)

## Architecture

```
Local Development Setup
├── Backend (Python FastAPI on port 8000)
├── Frontend (React Vite on port 5173)
├── Database (SQLite - local file)
├── Cache (File-based - local storage)
└── LLM (Mock mode - simulated responses)
```

---

## Backend Setup (Python)

### 1. Create Virtual Environment

```powershell
cd d:\NeuroPentWeb\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure for Local Development

Create `.env` file in `backend/` folder:

```bash
# Application
DEBUG=true
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production

# Database (SQLite - no external DB needed)
DATABASE_URL=sqlite:///./neuropent_local.db

# Redis (disabled for local - uses in-memory cache fallback)
REDIS_URL=redis://localhost:6379/0

# Ollama (Mock mode for development)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# Neo4j (disabled for local - graph functions will be mocked)
NEO4J_ENABLED=false

# MinIO (disabled - uses local file storage)
MINIO_ENABLED=false
STORAGE_TYPE=local

# Logging
LOG_LEVEL=DEBUG
```

### 4. Run Database Migrations

```powershell
cd d:\NeuroPentWeb\backend
alembic upgrade head
```

### 5. Start Backend

```powershell
cd d:\NeuroPentWeb\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
```

---

## Frontend Setup (React)

### 1. Install Dependencies

```powershell
cd d:\NeuroPentWeb\frontend
npm install
```

### 2. Configure API Endpoint

Create `.env.local` file in `frontend/` folder:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Start Development Server

```powershell
cd d:\NeuroPentWeb\frontend
npm run dev
```

**Expected output:**
```
  VITE v5.4.21  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.X.X:5173/
```

---

## Complete Local Startup (One Command)

### PowerShell Startup Script

Create `start-local-dev.ps1` in root:

```powershell
# PowerShell Local Development Startup

Write-Host "🚀 Starting RakshAI Local Development Environment" -ForegroundColor Green
Write-Host ""

# Terminal 1: Backend
Write-Host "Starting Backend on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @"
  Set-Location 'd:\NeuroPentWeb\backend'
  `$env:PYTHONUNBUFFERED = 1
  .\.venv\Scripts\Activate.ps1
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

Start-Sleep -Seconds 2

# Terminal 2: Frontend
Write-Host "Starting Frontend on port 5173..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @"
  Set-Location 'd:\NeuroPentWeb\frontend'
  npm run dev
"@

Write-Host ""
Write-Host "✅ Local Development Environment Started" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application:" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" 
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/api/v1/docs"
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop services"
```

Run it:
```powershell
cd d:\NeuroPentWeb
.\start-local-dev.ps1
```

---

## Verification

### 1. Check Backend Health

```powershell
curl http://127.0.0.1:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

### 2. Check API Documentation

Open in browser: **http://localhost:8000/api/v1/docs**

### 3. Access Frontend

Open in browser: **http://localhost:5173**

---

## Database

### Using SQLite (Recommended for Local Development)

SQLite stores data in `backend/neuropent_local.db` (local file).

**No setup required** - database is created automatically on first run.

### View Database (Optional)

Install DB Browser for SQLite:
```powershell
choco install db-browser-for-sqlite
```

Then open: `d:\RakshAI\backend\rakshaidb_local.db`

---

## Mock Services

### LLM Responses (Mock Mode)

When `OLLAMA_ENABLED=false`, LLM returns simulated responses for development.

Example response:
```json
{
  "attack_vectors": ["SQL Injection", "XSS", "CSRF"],
  "priority": "high",
  "rationale": "Common OWASP Top 10 categories"
}
```

### Graph Database (Neo4j)

When `NEO4J_ENABLED=false`, graph operations are logged but not stored.

### Storage (MinIO)

When `MINIO_ENABLED=false`, files saved to `./storage/` folder locally.

---

## Common Issues & Solutions

### Issue: "Module not found: app.main"

**Solution:** Ensure you're in the `backend/` directory and venv is activated.

```powershell
cd d:\NeuroPentWeb\backend
.\.venv\Scripts\Activate.ps1
```

### Issue: "Port 8000 already in use"

**Solution:** Kill the process using port 8000:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: "ModuleNotFoundError: No module named 'uvicorn'"

**Solution:** Reinstall dependencies:

```powershell
pip install --upgrade -r requirements.txt
```

### Issue: Frontend can't reach backend (CORS error)

**Solution:** Ensure backend is running on `http://127.0.0.1:8000` and `.env.local` has correct URL.

---

## Features Available Locally

| Feature | Local | Docker | Notes |
|---------|-------|--------|-------|
| API Server | ✅ | ✅ | Full functionality |
| Web UI | ✅ | ✅ | Full functionality |
| Database | ✅ SQLite | ✅ PostgreSQL | SQLite sufficient for dev |
| Agents | ✅ | ✅ | Graph DB functions mocked |
| LLM | ✅ Mock | ✅ Ollama | Mock responses in local mode |
| Real-time | ✅ File-based | ✅ Redis | Fallback to file polling |
| Reports | ✅ Local files | ✅ MinIO | Files saved to `./storage/` |

---

## Next Steps

1. **Backend**: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. **Frontend**: `npm run dev`
3. **Access**: http://localhost:5173
4. **Try a scan**: Create a new scan at http://localhost:5173/scans

---

## Production Setup (Later)

To switch to production with Docker:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

See `docker-compose.yml` for service definitions.
