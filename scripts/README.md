# 📁 Scripts Directory

This directory contains utility scripts for NeuroPentWeb setup, validation, and deployment.

---

## 🚀 Quick Start Scripts

### **install-dependencies.bat / .sh**
**Purpose:** Install Python and Node.js dependencies  
**Fixes:** All 272 VS Code import/dependency errors

**Usage:**
```powershell
# Windows
.\scripts\install-dependencies.bat

# Linux/macOS
chmod +x scripts/install-dependencies.sh
./scripts/install-dependencies.sh
```

**What it does:**
- Creates Python virtual environment in `backend/.venv`
- Installs all Python packages from `requirements.txt`
- Installs all Node packages from `package.json`
- Takes 5-10 minutes depending on internet speed

---

### **setup.bat / .sh**
**Purpose:** Complete project setup (dependencies + Docker + database)  
**Recommended for first-time setup**

**Usage:**
```powershell
# Windows
.\scripts\setup.bat

# Linux/macOS
./scripts/setup.sh
```

**What it does:**
- Everything from `install-dependencies` script
- Creates `.env` file
- Starts Docker containers
- Pulls Ollama LLM model
- Runs database migrations
- Installs Playwright browsers

---

## ✅ Validation Scripts

### **validate-all.bat / .sh**
**Purpose:** Validate knowledge base and rule engine integration

**Usage:**
```powershell
# Windows
.\scripts\validate-all.bat

# Linux/macOS
./scripts/validate-all.sh
```

**What it does:**
- Runs `backend/scripts/validate_kb.py`
- Runs `backend/scripts/test_rule_engine.py`
- Reports if YAML files are properly loaded

---

## 📊 Backend Scripts

Located in `backend/scripts/`:

### **validate_kb.py**
Validates knowledge base YAML files
```bash
cd backend
python scripts/validate_kb.py
```

### **test_rule_engine.py**
Tests complete rule engine pipeline
```bash
cd backend
python scripts/test_rule_engine.py
```

---

## 🎯 Which Script Should I Run?

### Scenario 1: First Time Setup
```powershell
.\scripts\setup.bat
```
- Complete setup including Docker
- Best for deployment

### Scenario 2: Just Fix VS Code Errors
```powershell
.\scripts\install-dependencies.bat
```
- Only installs dependencies
- Fast (5-10 minutes)
- Fixes all 272 problems

### Scenario 3: Validate After Changes
```powershell
.\scripts\validate-all.bat
```
- Check if knowledge base is working
- Verify rule engine integration

---

## 🔧 Development Workflow

1. **First time:**
   ```powershell
   .\scripts\install-dependencies.bat
   ```

2. **Reload VS Code** (Ctrl+Shift+P → "Reload Window")

3. **Verify errors are gone** (should be 0-5 problems)

4. **Start Docker:**
   ```powershell
   docker-compose up -d
   ```

5. **Develop!**

---

## ⚠️ Troubleshooting

### Script fails with "python not found"
**Solution:** Install Python 3.11+ from python.org and restart terminal

### Script fails with "npm not found"
**Solution:** Install Node.js 18+ from nodejs.org and restart terminal

### "Permission denied" on Linux/macOS
**Solution:**
```bash
chmod +x scripts/*.sh
```

### Still seeing errors after running script
**Solution:** Reload VS Code window (Ctrl+Shift+P → "Developer: Reload Window")

---

## 📝 Notes

- Scripts are safe to run multiple times
- Virtual environment is created in `backend/.venv`
- Node modules are installed in `frontend/node_modules`
- All scripts log their progress
- Scripts will pause on error for troubleshooting

---

**Need more help?** See [FIX-PROBLEMS.md](../FIX-PROBLEMS.md) in the project root.
