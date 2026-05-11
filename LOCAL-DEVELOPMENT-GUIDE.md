# NeuroPentWeb Local Development - Getting Started Guide

## Overview

This guide walks you through setting up and running NeuroPentWeb entirely on your local machine without Docker.

**Quick Summary:**
- Backend: FastAPI + SQLite (port 8000)
- Frontend: React + Vite (port 5173)
- Database: SQLite file-based (no PostgreSQL needed)
- LLM: Mock mode (no Ollama needed)
- Cache: File-based (no Redis needed)
- Storage: Local filesystem (no MinIO needed)

---

## Prerequisites

Before starting, ensure you have:

1. **Python 3.9+** installed
   - Check: `python --version`
   
2. **Node.js 18+** and npm 9+
   - Check: `node --version` and `npm --version`
   - Install: https://nodejs.org/ (LTS version recommended)

3. **Git** (optional, for version control)
   - Check: `git --version`

---

## Setup Instructions

### Step 1: Verify Your Setup

Run the automated verification script to check all requirements:

```powershell
python verify-setup.py
```

This will check:
- ✅ Python virtual environment
- ✅ Python packages
- ✅ Node.js and npm
- ✅ Frontend dependencies
- ✅ Configuration files
- ✅ Database setup

### Step 2: Create Python Virtual Environment (First Time Only)

If the verification shows the virtual environment is missing:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

### Step 3: Setup Configuration Files

Create local configuration files from templates:

```powershell
# Backend configuration
copy backend\.env.local.example backend\.env

# Frontend configuration
copy frontend\.env.local.example frontend\.env.local
```

**Optional**: Edit `backend/.env` to customize:
- `DATABASE_URL`: Where to store SQLite database
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `CORS_ORIGINS`: Allowed frontend URLs

### Step 4: Initialize the Database (First Time Only)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
cd ..
```

This creates the local SQLite database with all required tables.

### Step 5: Install Frontend Dependencies (First Time Only)

```powershell
cd frontend
npm install
cd ..
```

---

## Running the Application

### Option 1: Automated Startup (Recommended)

Run both servers with one command using the startup script:

**Using PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File start-local-dev.ps1
```

**Using Command Prompt:**
```cmd
start-local-dev.bat
```

This will:
- Create configuration files if missing
- Start the backend server on http://localhost:8000
- Start the frontend dev server on http://localhost:5173
- Open both in new terminal windows

### Option 2: Manual Startup (Advanced)

Run each component in a separate terminal:

**Terminal 1 - Backend:**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

---

## Accessing the Application

Once both servers are running:

- **Frontend UI**: http://localhost:5173
  - Login with any username/password (mock auth enabled)
  - Create scans, view findings, generate reports

- **Backend API Documentation**: http://localhost:8000/api/v1/docs
  - Interactive API explorer (Swagger UI)
  - Test endpoints directly
  - View request/response schemas

- **Backend Health Check**: http://localhost:8000/health
  - Returns: `{"status": "healthy"}`

---

## Using the Application

### Creating Your First Security Scan

1. Open http://localhost:5173 in your browser
2. Login with any credentials (mock authentication)
3. Go to **"New Scan"** page
4. Enter a HTTP target URL (e.g., `http://localhost:8000`)
5. Click **"Start Scan"**
6. Monitor progress in the **"Scans"** page
7. View findings in the **"Vulnerabilities"** page

### Generating Reports

- Go to **"Reports"** page
- Select a scan
- Generate PDF/HTML report

---

## File Structure

After running setup, your local directory structure will be:

```
d:\NeuroPentWeb\
│
├── backend/
│   ├── .venv/                    # Python virtual environment (created)
│   ├── .env                      # Local configuration (created from .env.local.example)
│   ├── neuropent_local.db        # SQLite database (created by alembic)
│   ├── storage/                  # Local file storage (created on first use)
│   ├── requirements.txt          # Python dependencies
│   └── app/                      # FastAPI application code
│
├── frontend/
│   ├── .env.local                # Frontend configuration (created from .env.local.example)
│   ├── node_modules/             # Node.js packages (created by npm install)
│   ├── package.json              # Node.js dependencies
│   └── src/                      # React application code
│
├── knowledge-base/               # Security testing patterns and rules
├── start-local-dev.ps1           # Startup script (PowerShell)
├── start-local-dev.bat           # Startup script (Batch)
└── verify-setup.py               # Setup verification script
```

---

## Troubleshooting

### Port Already in Use

If you get "Port xxx already in use":

**For Backend (Port 8000):**
```powershell
# Find and kill the process using port 8000
$process = Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $process -Force
```

**For Frontend (Port 5173):**
- The Vite dev server will automatically use port 5174 if 5173 is taken
- Check the terminal output for which port is being used

### Virtual Environment Not Activating

Make sure you're using PowerShell (not Command Prompt):

```powershell
# Check current shell
$PSVersionTable.PSVersion

# If not PowerShell, you may need to enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation
cd backend
.\.venv\Scripts\Activate.ps1
```

### Dependencies Not Installing

```powershell
# Clear pip cache and reinstall
cd backend
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

### Database Connection Error

The database is SQLite with no network connection needed:

```powershell
# Verify database file exists
Test-Path backend\neuropent_local.db

# If not, create it
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

### Frontend Can't Connect to Backend

Check that:

1. Backend is running on http://localhost:8000
2. Frontend is calling the correct URL:
   ```
   # Check frontend/.env.local
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

3. Check browser console for CORS errors
4. Verify backend CORS is configured for localhost:
   ```
   # In backend/.env
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

---

## Configuration Reference

### Backend Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `true` | Enable debug mode |
| `ENVIRONMENT` | `development` | Deployment environment |
| `DATABASE_URL` | `sqlite:///./neuropent_local.db` | SQLite database location |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |
| `REDIS_ENABLED` | `false` | Disable Redis (uses in-memory fallback) |
| `OLLAMA_ENABLED` | `false` | Disable Ollama (uses mock responses) |
| `NEO4J_ENABLED` | `false` | Disable Neo4j (uses mock graph) |
| `MINIO_ENABLED` | `false` | Disable MinIO (uses local filesystem) |
| `STORAGE_TYPE` | `local` | Use local filesystem for storage |
| `CORS_ORIGINS` | `http://localhost:5173...` | Allowed frontend URLs |

### Frontend Environment Variables (.env.local)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Backend API URL |

---

## Performance Notes

### Local Development Limitations

When running without services (Redis, Neo4j, MinIO):

1. **Cache**: Uses in-memory cache (per Python process)
   - Cache doesn't persist across server restarts
   - No cache sharing between multiple workers

2. **LLM**: Uses mock responses
   - Threat modeling returns generic patterns
   - PoC generation uses templates

3. **Graph Database**: Uses in-memory mock
   - Vulnerability relationships not persisted
   - Resets on server restart

4. **Storage**: Uses local filesystem
   - Screenshots and reports stored in `backend/storage/`
   - Can fill disk if you run many scans


### Recommended: Run One Scan at a Time

The local setup is optimized for development. For testing:

```
Max Concurrent Scans: 2 (instead of 5 in production)
Scan Timeout: 10 minutes (instead of 1 hour)
```

You can adjust in `backend/.env`:
```
MAX_CONCURRENT_SCANS=2
SCAN_TIMEOUT_SECONDS=600
```

---

## Stopping the Services

### Using Automated Startup

Simply press **Ctrl+C** in each terminal window to stop the servers.

### Cleanup

To reset the local environment:

```powershell
# Stop both servers (Ctrl+C in each terminal)

# Delete database (optional - you can keep data)
Remove-Item backend\neuropent_local.db

# Delete storage (optional)
Remove-Item backend\storage -Recurse -Force

# Delete frontend cache (optional)
Remove-Item frontend\node_modules -Recurse -Force
```

---

## Next Steps

1. **Run the setup verification:**
   ```powershell
   python verify-setup.py
   ```

2. **Fix any issues** mentioned by the verification script

3. **Start the application:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File start-local-dev.ps1
   ```

4. **Access the UI:**
   - Open http://localhost:5173
   - Login with sample credentials
   - Create a scan and explore features

5. **Review the logs:**
   - Backend logs appear in Terminal 1
   - Frontend logs appear in Terminal 2
   - Both show activity as you use the UI

---

## Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **Vite Docs**: https://vitejs.dev/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Alembic Docs**: https://alembic.sqlalchemy.org/

---

## Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review logs in the terminal windows
3. Run `python verify-setup.py` to check your setup
4. Ensure all prerequisites are installed
5. Try stopping and restarting the services

---

**Happy hacking! 🔒**

*Last updated: 2024*
*RakshAI v1.0.0 - Enterprise Penetration Testing Platform*
