#!/usr/bin/env powershell
# NeuroPentWeb Local Development Startup (PowerShell)

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  NeuroPentWeb Local Development Environment" -ForegroundColor Green
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend/.env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "[INFO] Copying backend\.env.local.example to backend\.env" -ForegroundColor Yellow
    Copy-Item "backend\.env.local.example" "backend\.env"
    Write-Host "[INFO] Configure backend\.env if needed" -ForegroundColor Yellow
}

# Check if frontend/.env.local exists
if (-not (Test-Path "frontend\.env.local")) {
    Write-Host "[INFO] Copying frontend\.env.local.example to frontend\.env.local" -ForegroundColor Yellow
    Copy-Item "frontend\.env.local.example" "frontend\.env.local"
}

Write-Host ""
Write-Host "Starting Backend (Python FastAPI on port 8000)..." -ForegroundColor Cyan
Write-Host ""

Start-Process powershell -ArgumentList @"
  Set-Location 'd:\NeuroPentWeb\backend'
  `$env:PYTHONUNBUFFERED = 1
  if (Test-Path '.\.venv\Scripts\Activate.ps1') {
    .\.venv\Scripts\Activate.ps1
  }
  Write-Host 'Backend starting on http://0.0.0.0:8000' -ForegroundColor Green
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Starting Frontend (React Vite on port 5173)..." -ForegroundColor Cyan
Write-Host ""

Start-Process powershell -ArgumentList @"
  Set-Location 'd:\NeuroPentWeb\frontend'
  Write-Host 'Frontend starting on http://localhost:5173' -ForegroundColor Green
  npm run dev
"@

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Local Development Environment Started" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Database: ./backend/neuropent_local.db" -ForegroundColor Yellow
Write-Host "  Storage:  ./backend/storage/" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C in each terminal to stop services" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
