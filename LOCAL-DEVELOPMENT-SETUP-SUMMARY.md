# RakshAI Local Development Setup - Summary

## What Was Created

This document summarizes all files created for running RakshAI locally *without Docker*.

---

## Configuration Files

### Backend Configuration Template
**File:** `backend/.env.local.example`
- Environment variables for local development
- SQLite database configuration
- All optional services disabled
- Can be copied to `backend/.env` to customize settings

### Frontend Configuration Template  
**File:** `frontend/.env.local.example`
- Frontend environment variables
- API base URL pointing to local backend

---

## Startup Scripts

### PowerShell Startup Script
**File:** `start-local-dev.ps1`
- Launches both backend and frontend servers
- Creates configuration files if missing
- Opens servers in separate terminal windows
- Displays access URLs and instructions
- **Usage:** `powershell -ExecutionPolicy Bypass -File start-local-dev.ps1`

### Batch Startup Script
**File:** `start-local-dev.bat`
- Windows Batch version of startup script
- Same functionality as PowerShell version
- **Usage:** `start-local-dev.bat` (double-click or run from cmd)

---

## Verification & Troubleshooting

### Setup Verification Script
**File:** `verify-setup.py`
- Automated environment validation
- Checks Python virtual environment
- Verifies package installation
- Validates Node.js and npm
- Confirms configuration files exist
- Validates database setup
- **Usage:** `python verify-setup.py`

---

## Documentation

### Local Development Getting Started
**File:** `LOCAL-DEVELOPMENT-GUIDE.md` (750+ lines)
- Complete setup walkthrough
- Step-by-step installation instructions
- Multiple ways to start services
- Troubleshooting guide
- Configuration reference
- File structure overview
- Performance notes
- Common issues and solutions

### Setup Summary (This File)
**File:** `LOCAL-DEVELOPMENT-SETUP-SUMMARY.md`
- Overview of all created files
- Quick start instructions
- Configuration details
- Known limitations

---

## Infrastructure Changes

### Updated Backend Configuration
**File:** `backend/app/core/config.py`
- Added feature flags:
  - `REDIS_ENABLED` (default: True)
  - `CELERY_ENABLED` (default: True)
  - `OLLAMA_ENABLED` (default: True)
  - `NEO4J_ENABLED` (default: True)
  - `MINIO_ENABLED` (default: True)
  
- Added storage configuration:
  - `STORAGE_TYPE`: "minio" or "local"
  - `STORAGE_PATH`: "./storage"
  - MinIO settings (endpoint, credentials, bucket)

- All settings respect environment variables from `.env` file

---

## Quick Start

### First Time Setup (Complete)

```powershell
# 1. Verify environment
python verify-setup.py

# 2. If verification passes, create Python environment (if needed)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# 3. Initialize configuration files
copy backend\.env.local.example backend\.env
copy frontend\.env.local.example frontend\.env.local

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Initialize database
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
cd ..
```

### Run Application

```powershell
# Option 1: Automated startup (Recommended)
powershell -ExecutionPolicy Bypass -File start-local-dev.ps1

# Option 2: Manual startup
# Terminal 1:
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2:
cd frontend
npm run dev
```

### Access Application

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/api/v1/docs
- **Health Check:** http://localhost:8000/health

---

## Service Configuration

### Services Disabled by Default (Local Mode)

When running locally, these services are disabled to avoid setup complexity:

| Service | Purpose | Local Alternative |
|---------|---------|-------------------|
| PostgreSQL | Database | SQLite (file-based) |
| Redis | Cache | In-memory dictionary |
| Neo4j | Graph DB | Python dict/Mock |
| MinIO | Object Storage | Local filesystem |
| Ollama | LLM | Mock responses |
| Celery | Task Queue | Synchronous execution |

### How Services are Disabled

1. **Environment Variables** (`.env` file)
   ```
   REDIS_ENABLED=false
   NEO4J_ENABLED=false
   MINIO_ENABLED=false
   OLLAMA_ENABLED=false
   ```

2. **Graceful Degradation** (Python code)
   - Services wrapped in try/except blocks
   - Fallbacks to local alternatives
   - Warning logs when service unavailable
   - No crash on missing optional services

3. **Configuration Classes**
   - `Settings` class loads from environment
   - Checks feature flags before initializing services
   - Uses appropriate connection strings/backends

---

## Database Setup

### SQLite (Local Development)

The local setup uses **SQLite** - a file-based database requiring no server:

**Database File:** `backend/neuropent_local.db`
- Auto-created by Alembic on first run
- Stores all scan results, findings, and metadata
- Persists across server restarts
- Can be backed up by copying the file

**Initialization:**
```powershell
cd backend
alembic upgrade head
```

**Schema:**
- Automatically created from SQLAlchemy models
- Includes tables for: scans, findings, agents, users, reports, etc.
- Latest migration management via Alembic

### Database Reset

To reset the database (delete all data):

```powershell
# Delete the database file
Remove-Item backend\neuropent_local.db

# Recreate it with fresh schema
cd backend
alembic upgrade head
```

---

## Frontend Development

### Dev Server

The frontend uses **Vite** development server:

- **Port:** 5173 (or 5174 if 5173 in use)
- **Hot Reload:** Automatic reload on code changes
- **Proxy:** Not configured (frontend calls backend directly)
- **Source Maps:** Enabled for debugging

### Building for Production

```powershell
cd frontend
npm run build
# Output: dist/ folder with optimized code
```

---

## Backend Development

### Dev Server

The backend uses **Uvicorn** ASGI server with reload:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Options:**
- `--reload`: Auto-restart on file changes
- `--host 0.0.0.0`: Listen on all network interfaces
- `--port 8000`: Run on port 8000

### API Documentation

Auto-generated interactive documentation at:
- http://localhost:8000/api/v1/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

---

## Logging

### Backend Logs

Set in `backend/.env`:
```
LOG_LEVEL=DEBUG      # Verbose logging
LOG_LEVEL=INFO       # Standard logging  
LOG_LEVEL=WARNING    # Only warnings/errors
LOG_LEVEL=ERROR      # Only errors
```

### Frontend Logs

Check browser Developer Tools (F12 → Console tab):
- Network requests to backend
- React component rendering
- Application errors

---

## Common Issues & Solutions

### Issue: "Port 8000 already in use"

```powershell
# Find and kill the process
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
```

### Issue: "Python: command not found"

- Python not installed or not in PATH
- Verify: `python --version`
- Install: https://python.org

### Issue: "npm: command not found"

- Node.js not installed or not in PATH  
- Verify: `npm --version`
- Install: https://nodejs.org

### Issue: "Database locked"

- Another process is using the SQLite database
- Stop both servers and restart

### Issue: "Can't import sqlalchemy"

- Python packages not installed
- Run: `pip install -r backend/requirements.txt`

---

## Architecture Diagram (Local Mode)

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Local Machine                       │
│                                                              │
│  ┌──────────────────┐              ┌──────────────────┐   │
│  │    Frontend      │              │      Backend     │   │
│  │  React + Vite    │              │   FastAPI +      │   │
│  │   Port 5173      │ HTTP/JSON    │    Uvicorn       │   │
│  │                  │◄────────────►│   Port 8000      │   │
│  └──────────────────┘              └──────────────────┘   │
│         ▲                                    ▲              │
│         │                                    │              │
│    Browser                           ┌──────────────────┐  │
│ (localhost:5173)                     │  SQLite (Local)  │  │
│                                      │  Database File   │  │
│                                      │  (.db file)      │  │
│                                      └──────────────────┘  │
│                                             ▲               │
│                                             │ R/W           │
│                                      ┌──────────────────┐  │
│                                      │  Storage/Logs    │  │
│                                      │  Local Filesystem│  │
│                                      │  (./storage/)    │  │
│                                      └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘

All services run on localhost - no Docker, no external services needed
```

---

## File Checklist

After setup, you should have these files:

### Configuration Files ✅
- [ ] `backend/.env` (created from .env.local.example)
- [ ] `frontend/.env.local` (created from .env.local.example)

### Database ✅
- [ ] `backend/neuropent_local.db` (created by alembic upgrade head)

### Virtual Environment ✅
- [ ] `backend/.venv/` directory (created by python -m venv)
- [ ] `backend/.venv/Lib/site-packages/` (contains installed packages)

### Node Modules ✅
- [ ] `frontend/node_modules/` (created by npm install)

### Generated Directories ✅
- [ ] `backend/storage/` (created on first upload/screenshot)
- [ ] `backend/__pycache__/` (Python bytecode cache)
- [ ] `frontend/dist/` (created by npm run build)

---

## Performance Expectations

### Local Development Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Backend startup | 2-3s | Fast uvicorn reload |
| Frontend build | 1-2s | No optimization |
| SQLite query | < 100ms | In-process queries |
| Full scan | 5-15min | Depends on target size |
| Finding storage | < 1s | Local filesystem |
| Report generation | 2-5s | Synchronous |

### Scaling Notes

Local development is optimized for single-user development:
- Single Python process (no workers)
- In-memory cache (not distributed)
- Local storage (not replicated)
- SQLite (not production DB)

For team development or higher loads, upgrade to production setup with:
- PostgreSQL + connection pool
- Redis for distributed cache
- MinIO for distributed storage
- Multiple worker processes

---

## What's NOT Included (Local Mode)

These enterprise features require external services:

- **Real-time collaboration**: Needs WebSocket server + distributed cache
- **Horizontal scaling**: Needs multiple workers + load balancer
- **High availability**: Needs database replication + failover
- **Advanced LLM**: Needs Ollama running (can mock responses)
- **Threat intelligence**: Needs Neo4j graph DB (can disable)
- **Advanced storage**: Needs MinIO (uses local filesystem instead)

---

## Next Steps

1. **Read the full guide:**
   - `LOCAL-DEVELOPMENT-GUIDE.md`

2. **Verify your setup:**
   - `python verify-setup.py`

3. **Start the application:**
   - `powershell -ExecutionPolicy Bypass -File start-local-dev.ps1`

4. **Access and explore:**
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/api/v1/docs

5. **Create your first scan:**
   - Use the frontend to create a security scan
   - Monitor progress and review findings

---

**Happy hacking! 🔒**

*For detailed setup instructions, see `LOCAL-DEVELOPMENT-GUIDE.md`*
*For troubleshooting, see the Troubleshooting section in the guide*
