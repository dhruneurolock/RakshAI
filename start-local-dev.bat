@echo off
REM NeuroPentWeb Local Development Startup (Windows Batch)

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo.
echo   NeuroPentWeb Local Development Environment
echo.
echo ================================================================================
echo.

REM Check if backend/.env exists
if not exist "backend\.env" (
    echo [INFO] Copying backend/.env.local.example to backend/.env
    copy backend\.env.local.example backend\.env
    echo [INFO] Configure backend\.env if needed before running
)

REM Check if frontend/.env.local exists
if not exist "frontend\.env.local" (
    echo [INFO] Copying frontend/.env.local.example to frontend/.env.local
    copy frontend\.env.local.example frontend\.env.local
)

echo.
echo Starting Backend (Python FastAPI on port 8000)...
echo.
cd backend
start cmd /k ".\.venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3

echo.
echo Starting Frontend (React Vite on port 5173)...
echo.
cd ..\frontend
start cmd /k "npm run dev"

cd ..

echo.
echo ================================================================================
echo.
echo ✅ Local Development Environment Started
echo.
echo.  Frontend: http://localhost:5173
echo.  Backend:  http://localhost:8000
echo.  API Docs: http://localhost:8000/api/v1/docs
echo.
echo.  Press Ctrl+C in each terminal to stop services
echo.
echo ================================================================================
echo.

pause
