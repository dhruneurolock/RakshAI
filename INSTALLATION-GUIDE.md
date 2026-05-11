# 📦 RakshAI - Complete Installation Guide

**Last Updated:** February 22, 2026  
**Platform:** Windows  
**Python Version:** 3.10+  
**Node.js Version:** 18+  

---

## ✅ Installation Status

### Backend Dependencies (Python)

The backend uses **70+ Python packages** including:

**Core Framework:**
- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- Celery 5.3.6
- Pydantic 2.5.3

**LLM & AI:**
- LangChain 0.1.6
- Ollama 0.1.7
- ChromaDB 0.4.22
- Sentence-Transformers 2.3.1

**Graph Database:**
- Neo4j 5.17.0
- Py2neo 2021.2.4

**Object Storage:**
- MinIO 7.2.3
- Boto3 1.34.34

**Reporting:**
- WeasyPrint 60.2 (PDF generation)
- python-docx 1.1.0 (Word documents)
- openpyxl 3.1.2 (Excel spreadsheets)

**Security Tools:**
- Playwright 1.41.1 (browser automation)
- Scrapy 2.11.0 (web crawling)
- httpx 0.25.2 (HTTP client)

---

## 🚀 Step-by-Step Installation

### Step 1: Install Backend Dependencies ✅ (IN PROGRESS)

```powershell
# Navigate to backend directory
cd D:\NeuroPentWeb\backend

# Install Python packages (currently running)
D:/NeuroPentWeb/backend/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

**Status:** Installing... (Dependency resolution may take 5-10 minutes)

**Fixed Issues:**
- ✅ Updated `py2neo` from 2021.2.3 → 2021.2.4
- ✅ Updated `httpx` from 0.26.0 → 0.25.2 (ollama compatibility)

---

### Step 2: Install Playwright Browsers

```powershell
# Install Chromium browser for screenshots
D:/NeuroPentWeb/backend/.venv/Scripts/python.exe -m playwright install chromium
```

**Why needed:** PoC Agent uses Playwright to capture vulnerability screenshots

---

### Step 3: Install Frontend Dependencies

```powershell
# Navigate to frontend directory
cd D:\NeuroPentWeb\frontend

# Install Node.js packages
npm install
```

**Packages installed:**
- React 18.2.0
- TypeScript 5.3.3
- Vite 5.0.11
- shadcn/ui components
- Recharts (for graphs)
- Axios (HTTP client)
- React Router v6
- TanStack Query

---

### Step 4: Verify Installation

#### Check Backend Packages

```powershell
D:/NeuroPentWeb/backend/.venv/Scripts/python.exe -m pip list
```

**Expected output:** 70+ packages installed

#### Check Frontend Packages

```powershell
cd D:\NeuroPentWeb\frontend
npm list --depth=0
```

**Expected output:** ~45 packages installed

---

## 🐳 Docker Services Setup

### Start All Services

```powershell
# From project root
.\start-enterprise.ps1
```

**Services started:**
1. **PostgreSQL** - Main database (port 5432)
2. **Neo4j** - Graph database (ports 7474, 7687)
3. **Redis** - Message queue + cache (port 6379)
4. **MinIO** - Object storage (ports 9000, 9001)
5. **ChromaDB** - Vector database (port 8001)
6. **Ollama** - LLM runtime (port 11434)

### Verify Docker Services

```powershell
docker ps
```

**Expected:** 6 containers running

---

## 🧪 Test Installation

### Test Backend

```powershell
cd D:\NeuroPentWeb\backend

# Activate virtual environment
& D:/NeuroPentWeb/backend/.venv/Scripts/Activate.ps1

# Run FastAPI dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access:** http://localhost:8000/docs

### Test Frontend

```powershell
cd D:\NeuroPentWeb\frontend

# Start development server
npm run dev
```

**Access:** http://localhost:5173

---

## 📊 Installation Verification Checklist

- [ ] Python virtual environment activated
- [ ] 70+ Python packages installed
- [ ] Playwright browsers installed
- [ ] Frontend node_modules created
- [ ] All 6 Docker services running
- [ ] Backend API accessible (http://localhost:8000/docs)
- [ ] Frontend accessible (http://localhost:5173)
- [ ] Ollama models downloaded (llama3.1, mistral)

---

## ⚠️ Common Issues

### Issue 1: Dependency Conflicts

**Error:** `ERROR: Cannot install -r requirements.txt`

**Solution:**
```powershell
# Update pip
D:/NeuroPentWeb/backend/.venv/Scripts/python.exe -m pip install --upgrade pip

# Retry installation
D:/NeuroPentWeb/backend/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

---

### Issue 2: Playwright Install Fails

**Error:** `playwright install chromium` fails

**Solution:**
```powershell
# Manual install
D:/NeuroPentWeb/backend/.venv/Scripts/playwright.exe install chromium

# Or with dependencies
D:/NeuroPentWeb/backend/.venv/Scripts/playwright.exe install --with-deps chromium
```

---

### Issue 3: Docker Services Not Starting

**Error:** `docker-compose up` fails

**Solution:**
```powershell
# Check Docker Desktop is running
docker version

# Remove old containers
docker-compose down -v

# Restart
docker-compose up -d
```

---

### Issue 4: Port Already in Use

**Error:** `Address already in use`

**Solution:**
```powershell
# Find process using port (e.g., 8000)
netstat -ano | findstr :8000

# Kill process (replace <PID> with actual PID)
taskkill /PID <PID> /F
```

---

## 📦 Package Sizes

### Backend

| Category | Packages | Total Size |
|----------|----------|------------|
| **Core Framework** | 15 | ~150 MB |
| **LLM & AI** | 12 | ~2.5 GB |
| **Databases** | 8 | ~100 MB |
| **Web Scraping** | 10 | ~200 MB |
| **Reporting** | 7 | ~300 MB |
| **Testing & Quality** | 18 | ~150 MB |
| **Total** | **70+** | **~3.4 GB** |

### Frontend

| Category | Packages | Total Size |
|----------|----------|------------|
| **React & Core** | 10 | ~50 MB |
| **UI Components** | 15 | ~30 MB |
| **Build Tools** | 12 | ~100 MB |
| **TypeScript** | 8 | ~20 MB |
| **Total** | **45+** | **~200 MB** |

---

## 🕐 Installation Time Estimates

| Task | Time |
|------|------|
| Backend dependencies | 5-10 minutes |
| Playwright browsers | 2-3 minutes |
| Frontend dependencies | 2-3 minutes |
| Docker services | 3-5 minutes |
| Ollama models | 5-10 minutes |
| **Total** | **17-31 minutes** |

*(Times vary based on internet speed and system performance)*

---

## 📚 Next Steps After Installation

1. **Pull LLM Models**
   ```powershell
   docker exec -it ollama ollama pull llama3.1:8b
   docker exec -it ollama ollama pull mistral:7b
   docker exec -it ollama ollama pull nomic-embed-text
   ```

2. **Run Database Migrations**
   ```powershell
   cd D:\NeuroPentWeb\backend
   alembic upgrade head
   ```

3. **Create Admin User**
   ```powershell
   D:/NeuroPentWeb/backend/.venv/Scripts/python.exe -c "
   from app.core.database import SessionLocal
   from app.models.user import User
   from passlib.context import CryptContext
   
   db = SessionLocal()
   pwd_context = CryptContext(schemes=['bcrypt'])
   
   admin = User(
       email='admin@example.com',
       hashed_password=pwd_context.hash('admin123'),
       is_active=True,
       is_superuser=True
   )
   
   db.add(admin)
   db.commit()
   print('Admin user created!')
   "
   ```

4. **Start First Scan**
   - Open http://localhost:5173
   - Login with `admin@example.com` / `admin123`
   - Create new scan targeting `https://testphp.vulnweb.com`

---

## 🔧 Development Environment

### Recommended VS Code Extensions

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **ESLint** (dbaeumer.vscode-eslint)
- **TypeScript + React** (ms-vscode.vscode-typescript-next)
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
- **Docker** (ms-azuretools.vscode-docker)

### VS Code Settings

```json
{
  "python.defaultInterpreterPath": "D:/NeuroPentWeb/backend/.venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## 📖 Documentation References

- **[PROCESS-DOCUMENTATION.md](PROCESS-DOCUMENTATION.md)** - Complete system workflow
- **[COMPLETE-IMPLEMENTATION.md](COMPLETE-IMPLEMENTATION.MD)** - Technical architecture
- **[QUICK-START-ENTERPRISE.md](QUICK-START-ENTERPRISE.md)** - Quick start guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
- **[DOCKER-TROUBLESHOOTING.md](DOCKER-TROUBLESHOOTING.md)** - Docker issues

---

## ✅ Installation Complete!

Once all steps are complete, you'll have:

- ✅ **Backend:** FastAPI running with 7 agents + 4 services
- ✅ **Frontend:** React dashboard with real-time updates
- ✅ **Databases:** PostgreSQL, Neo4j, Redis, ChromaDB, MinIO
- ✅ **LLM:** Ollama with 3 models (llama3.1, mistral, embeddings)
- ✅ **Security Tools:** 39 penetration testing tools ready
- ✅ **Reports:** PDF, Word, Excel generation working

**Ready to scan!** 🚀

---

**Support:**
- GitHub Issues: [Report bugs]
- Documentation: [Full docs]
- Community: [Discord server]

**License:** MIT  
**Version:** 1.0.0  
**Status:** Production Ready
