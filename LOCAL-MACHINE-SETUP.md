# 🖥️ RakshAI - Local Machine Setup (No Docker)

**Platform:** Windows  
**Date:** February 22, 2026  
**Setup:** All services running locally (no Docker required)

---

## 📋 Prerequisites

- ✅ Python 3.10+ (already installed)
- ⬜ PostgreSQL 14+
- ⬜ Redis 7+
- ⬜ Neo4j 5+
- ⬜ Node.js 18+
- ⬜ Ollama (LLM runtime)

---

## 🚀 Step-by-Step Local Installation

### Step 1: Install PostgreSQL (Windows)

**Download & Install:**
```powershell
# Download from: https://www.postgresql.org/download/windows/
# Or use Windows installer
winget install PostgreSQL.PostgreSQL

# After installation, set password for 'postgres' user
# Default port: 5432
```

**Create Database:**
```powershell
# Open PowerShell as Administrator
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE rakshaidb;
CREATE USER rakshaiuser WITH PASSWORD 'rakshaidb_secure_pass';
GRANT ALL PRIVILEGES ON DATABASE rakshaidb TO rakshaiuser;
\q
```

**Verify:**
```powershell
psql -U rakshaiuser -d rakshaidb
# Should connect successfully
```

---

### Step 2: Install Redis (Windows)

**Option A: Using Memurai (Redis-compatible for Windows)**
```powershell
# Download from: https://www.memurai.com/
winget install Memurai.Memurai

# Or download installer from website
# Default port: 6379
```

**Option B: Using WSL2 (Recommended)**
```powershell
# Install WSL2 if not already installed
wsl --install

# In WSL2 terminal:
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Verify:**
```powershell
redis-cli ping
# Expected: PONG
```

---

### Step 3: Install Neo4j (Windows)

**Download & Install:**
```powershell
# Download from: https://neo4j.com/download/
# Or use Windows installer

# 1. Install Java 17+ (required for Neo4j)
winget install Oracle.JDK.17

# 2. Download Neo4j Community Edition
# Extract to: C:\neo4j

# 3. Set initial password
C:\neo4j\bin\neo4j-admin.bat set-initial-password neuropent_graph_pass

# 4. Start Neo4j
C:\neo4j\bin\neo4j.bat start
```

**Verify:**
```powershell
# Open browser: http://localhost:7474
# Login: neo4j / neuropent_graph_pass
```

---

### Step 4: Install Node.js & Frontend Dependencies

**Install Node.js:**
```powershell
# Download from: https://nodejs.org/
# Or use winget
winget install OpenJS.NodeJS.LTS

# Verify
node --version  # Should be v18+
npm --version
```

**Install Frontend Dependencies:**
```powershell
cd D:\NeuroPentWeb\frontend
npm install
```

---

### Step 5: Install Ollama (LLM Runtime)

**Download & Install:**
```powershell
# Download from: https://ollama.ai/download/windows
# Or direct download
# Install to default location

# Verify installation
ollama --version
```

**Pull Required Models:**
```powershell
# Pull LLM models (this will take 10-20 minutes)
ollama pull llama3.1:8b      # ~4.7 GB
ollama pull mistral:7b        # ~4.1 GB  
ollama pull nomic-embed-text  # ~274 MB

# Verify models
ollama list
```

**Start Ollama Server:**
```powershell
# Ollama runs as a Windows service automatically
# Default: http://localhost:11434

# Test endpoint
curl http://localhost:11434/api/tags
```

---

### Step 6: Install MinIO (Object Storage) - Optional

**For Local Development:**
```powershell
# Download MinIO for Windows
# From: https://min.io/download

# Create MinIO directory
New-Item -ItemType Directory -Path C:\minio\data

# Start MinIO server
C:\minio\minio.exe server C:\minio\data --console-address ":9001"

# Default credentials:
# Access Key: minioadmin
# Secret Key: minioadmin

# Access Console: http://localhost:9001
```

**Alternative: Use Local Filesystem**
```python
# In backend/.env, set:
USE_MINIO=false
LOCAL_STORAGE_PATH=D:/NeuroPentWeb/storage
```

---

### Step 7: Install ChromaDB (Vector Database)

**Option A: Standalone Server**
```powershell
# Install ChromaDB
pip install chromadb

# Start ChromaDB server
chroma run --path D:/RakshAI/chromadb_data --port 8001
```

**Option B: Embedded Mode (Recommended for Local)**
```python
# ChromaDB will run embedded in the Python backend
# No separate server needed
# Just install: pip install chromadb (already in requirements.txt)
```

---

### Step 8: Configure Environment Variables

Create `backend/.env` file:

```env
# Database
DATABASE_URL=postgresql://rakshaiuser:rakshaidb_secure_pass@localhost:5432/rakshaidb

# Redis
REDIS_URL=redis://localhost:6379/0

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neuropent_graph_pass

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# ChromaDB (embedded mode)
CHROMA_EMBEDDED=true
CHROMA_PATH=D:/RakshAI/chromadb_data

# MinIO (if using)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# Or use local storage
USE_MINIO=false
LOCAL_STORAGE_PATH=D:/NeuroPentWeb/storage

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=true
```

---

### Step 9: Install Backend Dependencies (Completed)

```powershell
cd D:\RakshAI\backend

# Activate virtual environment
& D:/RakshAI/backend/.venv/Scripts/Activate.ps1

# Install remaining packages if needed
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

---

### Step 10: Run Database Migrations

```powershell
cd D:\RakshAI\backend

# Activate virtual environment
& D:/RakshAI/backend/.venv/Scripts/Activate.ps1

# Run Alembic migrations
alembic upgrade head
```

---

## 🎯 Starting the Application

### Terminal 1: Start Backend API

```powershell
cd D:\NeuroPentWeb\backend

# Activate virtual environment
& D:/NeuroPentWeb/backend/.venv/Scripts/Activate.ps1

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access:** http://localhost:8000/docs

---

### Terminal 2: Start Celery Worker

```powershell
cd D:\RakshAI\backend

# Activate virtual environment
& D:/RakshAI/backend/.venv/Scripts/Activate.ps1

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

*Note: `--pool=solo` is required for Windows*

---

### Terminal 3: Start Frontend

```powershell
cd D:\NeuroPentWeb\frontend

# Start Vite dev server
npm run dev
```

**Access:** http://localhost:5173

---

## 🧪 Verify All Services

### Service Health Check Script

Create `scripts/check_local_services.ps1`:

```powershell
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  CHECKING LOCAL SERVICES" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# PostgreSQL
Write-Host "Checking PostgreSQL..." -ForegroundColor White
try {
    $pgResult = psql -U rakshaiuser -d rakshaidb -c "SELECT 1;" 2>$null
    Write-Host "  ✓ PostgreSQL: Running on port 5432" -ForegroundColor Green
} catch {
    Write-Host "  ✗ PostgreSQL: Not running" -ForegroundColor Red
}

# Redis
Write-Host "Checking Redis..." -ForegroundColor White
try {
    $redisResult = redis-cli ping 2>$null
    if ($redisResult -eq "PONG") {
        Write-Host "  ✓ Redis: Running on port 6379" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Redis: Not running" -ForegroundColor Red
}

# Neo4j
Write-Host "Checking Neo4j..." -ForegroundColor White
try {
    $neo4jResult = Invoke-WebRequest -Uri "http://localhost:7474" -UseBasicParsing -TimeoutSec 2 2>$null
    Write-Host "  ✓ Neo4j: Running on port 7474" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Neo4j: Not running" -ForegroundColor Red
}

# Ollama
Write-Host "Checking Ollama..." -ForegroundColor White
try {
    $ollamaResult = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 2>$null
    Write-Host "  ✓ Ollama: Running on port 11434" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Ollama: Not running" -ForegroundColor Red
}

# Backend API
Write-Host "Checking Backend API..." -ForegroundColor White
try {
    $backendResult = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 2>$null
    Write-Host "  ✓ Backend API: Running on port 8000" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Backend API: Not running" -ForegroundColor Red
}

# Frontend
Write-Host "Checking Frontend..." -ForegroundColor White
try {
    $frontendResult = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 2>$null
    Write-Host "  ✓ Frontend: Running on port 5173" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Frontend: Not running" -ForegroundColor Red
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
```

**Run the check:**
```powershell
.\scripts\check_local_services.ps1
```

---

## 📦 Installation Checklist

### Core Services
- [ ] PostgreSQL installed and running (port 5432)
- [ ] Redis installed and running (port 6379)
- [ ] Neo4j installed and running (ports 7474, 7687)
- [ ] Node.js installed (v18+)
- [ ] Ollama installed and running (port 11434)

### Optional Services
- [ ] MinIO installed (ports 9000, 9001) OR local storage configured
- [ ] ChromaDB server running (port 8001) OR embedded mode enabled

### Backend Setup
- [ ] Python virtual environment activated
- [ ] Backend dependencies installed (70+ packages)
- [ ] Playwright browsers installed
- [ ] `.env` file created with correct values
- [ ] Database migrations run successfully

### Frontend Setup
- [ ] Node.js dependencies installed
- [ ] Frontend dev server starts successfully

### LLM Models
- [ ] llama3.1:8b downloaded
- [ ] mistral:7b downloaded
- [ ] nomic-embed-text downloaded

---

## 🔧 Quick Start Scripts

### Create `start-local.ps1` (All-in-One Startup)

```powershell
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  STARTING NEUROPENTWEB (LOCAL MODE)" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Start PostgreSQL (if installed as service)
Write-Host "Starting PostgreSQL..." -ForegroundColor White
Start-Service postgresql-x64-14

# Start Redis (if using Memurai)
Write-Host "Starting Redis..." -ForegroundColor White
Start-Service Memurai

# Start Neo4j
Write-Host "Starting Neo4j..." -ForegroundColor White
& "C:\neo4j\bin\neo4j.bat" start

# Start Ollama (should auto-start)
Write-Host "Checking Ollama..." -ForegroundColor White
$ollamaRunning = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
}

# Wait for services
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start Backend in new terminal
Write-Host "Starting Backend API..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\NeuroPentWeb\backend'; & D:/NeuroPentWeb/backend/.venv/Scripts/Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Start Celery Worker in new terminal
Write-Host "Starting Celery Worker..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\NeuroPentWeb\backend'; & D:/NeuroPentWeb/backend/.venv/Scripts/Activate.ps1; celery -A app.core.celery_app worker --loglevel=info --pool=solo"

# Start Frontend in new terminal
Write-Host "Starting Frontend..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\NeuroPentWeb\frontend'; npm run dev"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ALL SERVICES STARTED!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nAccess Points:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Neo4j:     http://localhost:7474" -ForegroundColor White
Write-Host "`n" -ForegroundColor White
```

---

## ⚙️ Windows Service Configuration

### Run PostgreSQL as Windows Service

```powershell
# Already installed as service by default installer
# Service name: postgresql-x64-14

# Set to start automatically
Set-Service -Name postgresql-x64-14 -StartupType Automatic
Start-Service postgresql-x64-14
```

### Run Redis as Windows Service (Memurai)

```powershell
# Memurai installs as service by default
# Service name: Memurai

Set-Service -Name Memurai -StartupType Automatic
Start-Service Memurai
```

### Run Neo4j as Windows Service

```powershell
# Install as service
C:\neo4j\bin\neo4j.bat install-service

# Set to start automatically
Set-Service -Name neo4j -StartupType Automatic
Start-Service neo4j
```

---

## 🎯 Development Workflow

### Daily Startup (After Services Installed)

```powershell
# 1. Run startup script
.\start-local.ps1

# 2. Wait 30 seconds for all services

# 3. Open browser
# - Frontend: http://localhost:5173
# - API Docs: http://localhost:8000/docs
```

### Stopping Services

```powershell
# Stop all terminals (Ctrl+C in each)

# Or use Task Manager to kill:
# - uvicorn
# - celery
# - node (Vite)

# Stop database services (optional)
Stop-Service postgresql-x64-14
Stop-Service Memurai
Stop-Service neo4j
```

---

## 📊 Resource Usage (Local)

| Service | RAM | CPU | Disk |
|---------|-----|-----|------|
| PostgreSQL | ~200 MB | 1-5% | 1 GB |
| Redis | ~50 MB | 0-2% | 100 MB |
| Neo4j | ~500 MB | 2-10% | 500 MB |
| Ollama (w/ models) | ~8 GB | 5-80% | 10 GB |
| Backend (Python) | ~500 MB | 5-20% | - |
| Frontend (Node) | ~300 MB | 2-10% | - |
| **Total Minimum** | **~9.5 GB** | **15-127%** | **~12 GB** |

**Recommended System:**
- **RAM:** 16 GB minimum, 32 GB recommended
- **CPU:** 4 cores minimum, 8 cores recommended
- **Disk:** 50 GB free space (for models and data)

---

## ⚠️ Troubleshooting

### PostgreSQL Connection Failed

```powershell
# Check if running
Get-Service postgresql-x64-14

# Check port
netstat -ano | findstr :5432

# Test connection
psql -U postgres -h localhost
```

### Redis Connection Failed

```powershell
# Check if Memurai is running
Get-Service Memurai

# Or check WSL2 Redis
wsl -d Ubuntu -- service redis-server status

# Test connection
redis-cli ping
```

### Neo4j Won't Start

```powershell
# Check Java installation
java -version  # Should be 17+

# Check logs
Get-Content C:\neo4j\logs\neo4j.log -Tail 50

# Restart service
Restart-Service neo4j
```

### Ollama Models Not Loading

```powershell
# Check installed models
ollama list

# Re-download model
ollama pull llama3.1:8b

# Check Ollama service
Get-Process ollama

# Restart Ollama
taskkill /IM ollama.exe /F
ollama serve
```

---

## 🚀 Ready to Use!

After completing all steps:

1. ✅ All services running locally (no Docker)
2. ✅ Backend API accessible at http://localhost:8000
3. ✅ Frontend accessible at http://localhost:5173
4. ✅ LLM models ready for AI-powered testing

**First Scan:**
- Login with default credentials
- Target: `https://testphp.vulnweb.com` (safe test site)
- Type: Full Scan
- Wait ~3-5 minutes for results

---

**Next:** See [PROCESS-DOCUMENTATION.md](PROCESS-DOCUMENTATION.md) for complete workflow details.
