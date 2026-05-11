# NeuroPentWeb - Backend Only Startup Script

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  NEUROPENTWEB - BACKEND STARTUP" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = 'Stop'

$projectRoot = "D:\NeuroPentWeb"
$backendRoot = Join-Path $projectRoot "backend"
$venvActivate = Join-Path $backendRoot ".venv\Scripts\Activate.ps1"
$envExample = Join-Path $backendRoot ".env.example"
$envFile = Join-Path $backendRoot ".env"

if (-not (Test-Path $backendRoot)) {
    Write-Host "✗ Backend folder not found: $backendRoot" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $venvActivate)) {
    Write-Host "✗ Python virtual environment not found at $venvActivate" -ForegroundColor Red
    Write-Host "  Create it with:" -ForegroundColor Yellow
    Write-Host "  cd D:\NeuroPentWeb\backend" -ForegroundColor Gray
    Write-Host "  py -3.11 -m venv .venv" -ForegroundColor Gray
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Gray
    exit 1
}

if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host "✓ Created backend/.env from .env.example" -ForegroundColor Green
}

Set-Location $backendRoot

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& $venvActivate

Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Cyan
Write-Host "API Root:  http://localhost:8000/" -ForegroundColor Green
Write-Host "API Docs:  http://localhost:8000/api/v1/docs`n" -ForegroundColor Green

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
