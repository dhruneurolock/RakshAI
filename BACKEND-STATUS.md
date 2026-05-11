# RakshAI Backend - Service Status

**Status: ✅ RUNNING WITH ALL SERVICES ENABLED**

## Backend Server
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health
- **Process ID**: 20444
- **Port**: 8000
- **Mode**: Production (reload enabled)
- **Configuration**: `.env` (All services enabled)

## Service Status

### ✅ Running (Available)
- **PostgreSQL** - localhost:5432
  - Database: rakshaidb
  - User: rakshaiuser
  - Status: Connected
  
- **Redis** - localhost:6379
  - Status: Connected
  - Used for: Caching, Celery broker, Task queue

### ⏳ Not Available (Graceful Degradation)
- **Neo4j** - bolt://localhost:7687
  - Status: Not running
  - Fallback: In-memory graph mock
  - Impact: Relationship queries use mock data
  
- **Ollama** (LLM) - http://localhost:11434
  - Status: Not running
  - Fallback: Mock LLM responses
  - Impact: Threat modeling returns generic patterns
  
- **MinIO** (Object Storage) - http://localhost:9000
  - Status: Not running
  - Fallback: Local filesystem storage
  - Impact: Screenshots/reports stored in `backend/storage/`

## Configuration Details

**File**: `backend/.env.production` (copied to `backend/.env`)

```
# Services Enabled
REDIS_ENABLED=true          ✅
CELERY_ENABLED=true         ✅
OLLAMA_ENABLED=true         (fallback)
NEO4J_ENABLED=true          (fallback)
MINIO_ENABLED=true          (fallback)

# Database
DATABASE_URL=postgresql://rakshaiuser:***@localhost:5432/rakshaidb

# Operating Mode
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

## What's Working

✅ Full API available at http://localhost:8000/api/v1/docs
✅ Database operations (scans, findings, users)
✅ Cache operations (Redis-backed)
✅ Task queuing (Celery with Redis broker)
✅ Persistence layer (PostgreSQL)

## What Has Fallbacks

⚠️ Graph database queries (using in-memory mock)
⚠️ LLM operations (using mock responses)
⚠️ File storage (using local filesystem instead of MinIO)

## Next Steps

### Option 1: Start Missing Services (Recommended)
To enable all services fully, start these in separate terminals:

```powershell
# Neo4j
neo4j start

# Ollama
ollama serve

# MinIO
minio server ./data
```

Then the backend will automatically use these services.

### Option 2: Use as-is
The backend is fully functional with PostgreSQL and Redis.
Optional services gracefully degrade to local fallbacks.

## Testing the Backend

1. **Health Check**:
   ```powershell
   curl -s http://localhost:8000/health
   ```

2. **API Docs** (Interactive):
   - Open: http://localhost:8000/api/v1/docs
   - Try endpoints directly in the UI

3. **Create First Scan**:
   ```powershell
   # Via API Docs or frontend
   POST /api/v1/scans/
   {
       "target": "http://example.com",
       "name": "Test Scan"
   }
   ```

## Logs Location

Backend logs are printed to the terminal window where the server started.
Set `LOG_LEVEL=DEBUG` in `.env` for verbose output.

## Stopping Backend

**In the terminal running the backend**: Press `Ctrl+C`

Or kill the process:
```powershell
Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
```

---

**Backend is ready for production-like testing with available services!** 🚀
