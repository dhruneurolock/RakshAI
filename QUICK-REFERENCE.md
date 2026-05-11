# NeuroPentWeb Local Development - Quick Reference

## One-Minute Quick Start

```powershell
# First time only: Setup
python verify-setup.py
copy backend\.env.local.example backend\.env
copy frontend\.env.local.example frontend\.env.local

# Start servers (in one command)
powershell -ExecutionPolicy Bypass -File start-local-dev.ps1

# Access application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/v1/docs
```

---

## Essential Commands

### First-Time Setup

```powershell
# Check if environment is ready
python verify-setup.py

# Create Python virtual environment (only if missing)
cd backend && python -m venv .venv && cd ..

# Create configuration files from templates
copy backend\.env.local.example backend\.env
copy frontend\.env.local.example frontend\.env.local

# Install Python dependencies
cd backend && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt && cd ..

# Initialize SQLite database
cd backend && alembic upgrade head && cd ..

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Running the Application

```powershell
# Option 1: Start both servers at once (Recommended)
powershell -ExecutionPolicy Bypass -File start-local-dev.ps1

# Option 2: Start backend only
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 3: Start frontend only
cd frontend
npm run dev

# Option 4: Build frontend for production
cd frontend
npm run build
```

### Stopping Services

```powershell
# In each terminal: Press Ctrl+C

# Or kill a process using a specific port
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
```

### Database Commands

```powershell
# Activate backend virtual environment
cd backend && .\.venv\Scripts\Activate.ps1

# Initialize/reset database
alembic upgrade head

# Create a new migration (after changing models)
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic branches
alembic history
```

### Python Development

```powershell
cd backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run linter
flake8 app/

# Run type checker
mypy app/

# Run tests
pytest tests/

# Run specific test
pytest tests/test_rule_engine.py::test_simple_rule

# Interactive Python shell with app context
ipython
```

### Frontend Development

```powershell
cd frontend

# Start dev server with HMR (Hot Module Replacement)
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Lint TypeScript/React
npm run lint

# Format code
npm run format
```

---

## Important File Locations

```
d:\NeuroPentWeb\
│
├── backend/
│   ├── .env                           # Configuration file
│   ├── neuropent_local.db             # SQLite database
│   ├── storage/                       # Uploaded files, screenshots
│   ├── app/main.py                    # FastAPI app entry
│   └── .venv/Scripts/Activate.ps1     # Virtual env activation
│
├── frontend/
│   ├── .env.local                     # Configuration file
│   ├── src/main.tsx                   # React app entry
│   ├── package.json                   # Dependencies
│   └── node_modules/                  # Installed packages
│
├── LOCAL-DEVELOPMENT-GUIDE.md         # Full setup guide
├── LOCAL-DEVELOPMENT-SETUP-SUMMARY.md # Setup overview
├── start-local-dev.ps1                # Start both servers
└── verify-setup.py                    # Check environment
```

---

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Web UI |
| API Docs | http://localhost:8000/api/v1/docs | Swagger UI |
| API ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Health | http://localhost:8000/health | Backend health check |

---

## Common Tasks

### Add a Python Dependency

```powershell
cd backend

# Activate environment
.\.venv\Scripts\Activate.ps1

# Install package
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt

# Share with team
git add requirements.txt && git commit -m "Add new dependency"
```

### Add a Node Package

```powershell
cd frontend

# Install package (with TypeScript types)
npm install package-name --save

# Install dev dependency
npm install --save-dev package-name

# Update lock file
git add package.json package-lock.json
```

### View Logs

```powershell
# Backend logs appear in the terminal running uvicorn
# Frontend logs appear in the terminal running npm run dev

# Or view system logs in Windows Event Viewer:
# Win + R → eventvwr → Windows Logs → System

# Check backend .env for LOG_LEVEL
DEBUG=true
LOG_LEVEL=DEBUG  # For verbose logging
```

### Reset Everything

```powershell
# Stop all servers (Ctrl+C in each terminal)

# Delete database
Remove-Item backend\neuropent_local.db

# Delete storage
Remove-Item backend\storage -Recurse -Force

# Delete Python cache
Remove-Item backend\__pycache__ -Recurse -Force
Remove-Item backend\.pytest_cache -Recurse -Force

# Delete frontend build
Remove-Item frontend\dist -Recurse -Force

# Reinstall and reinit
cd backend && alembic upgrade head && cd ..
cd frontend && npm install && cd ..
```

---

## Troubleshooting Checklist

### Backend Not Starting

- [ ] Virtual environment activated? `.\.venv\Scripts\Activate.ps1`
- [ ] Dependencies installed? `pip install -r requirements.txt`
- [ ] Database initialized? `alembic upgrade head`
- [ ] Port 8000 free? `Get-NetTCPConnection -LocalPort 8000`
- [ ] Python version OK? `python --version` (need 3.9+)

### Frontend Not Starting

- [ ] Node.js installed? `node --version`
- [ ] npm installed? `npm --version`
- [ ] Dependencies installed? `npm install`
- [ ] Port 5173 free? (or check for 5174 fallback)

### Can't Connect Frontend to Backend

- [ ] Backend running? Check http://localhost:8000/health
- [ ] Frontend .env.local has right URL?
- [ ] CORS enabled in backend? Check `CORS_ORIGINS` in `.env`
- [ ] Browser console has errors? (F12 → Console)

### Database Issues

- [ ] SQLite file exists? `Test-Path backend\neuropent_local.db`
- [ ] Schema created? `alembic upgrade head`
- [ ] No stale locks? (Stop all processes and restart)

---

## Performance Tips

```powershell
# Reduce logging verbosity (faster)
# In backend/.env:
LOG_LEVEL=WARNING

# Disable debug mode for faster startup
DEBUG=false

# Increase Python startup timeout (might help on slow machines)
$env:PYTHONDONTWRITEBYTECODE=0

# Clear Python cache if experiencing issues
Remove-Item backend\__pycache__ -Recurse -Force
```

---

## Testing Checklist

```powershell
# Test backend health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Test API documentation
# Navigate to: http://localhost:8000/api/v1/docs

# Test frontend loads
# Navigate to: http://localhost:5173
# Check browser console for errors (F12)

# Test login
# Use any username/password (mock auth enabled)

# Test API call from frontend
# Go to Dashboard page, check Network tab (F12)
```

---

## Getting Help

1. **Check the full guide:** `LOCAL-DEVELOPMENT-GUIDE.md`
2. **Run verification:** `python verify-setup.py`
3. **View logs:** Check terminal output
4. **Review browser console:** F12 → Console tab
5. **Restart services:** Stop (Ctrl+C) and restart

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Stop server | Ctrl + C |
| Clear terminal | Ctrl + L |
| Reload browser | F5 or Ctrl + R |
| Browser DevTools | F12 |
| Hard refresh | Ctrl + Shift + R |

---

## Useful Links

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **TypeScript Docs:** https://www.typescriptlang.org/
- **Vite Docs:** https://vitejs.dev/
- **SQLite Docs:** https://www.sqlite.org/docs.html
- **Alembic Docs:** https://alembic.sqlalchemy.org/

---

**Pro Tips:**

✅ Always run `python verify-setup.py` before reporting issues

✅ Keep `.env` files out of git (add to `.gitignore`)

✅ Use `--reload` flag for development (auto-restart on changes)

✅ Check browser console (F12) for frontend errors first

✅ Restart services if experiencing strange behavior

---

**Last Updated:** 2024  
**NeuroPentWeb Version:** 1.0.0
