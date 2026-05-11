#!/usr/bin/env powershell
# NeuroPentWeb - Stable local startup script
# Starts required services for local development in separate terminals.

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NEUROPENTWEB - LOCAL STARTUP" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Test-TcpPort {
    param(
        [int]$Port,
        [string]$ComputerName = "localhost",
        [int]$TimeoutMs = 1500
    )

    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect($ComputerName, $Port, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
        if ($ok -and $client.Connected) {
            $client.EndConnect($async) | Out-Null
            $client.Close()
            return $true
        }
        $client.Close()
        return $false
    } catch {
        return $false
    }
}

function Start-WindowCommand {
    param(
        [string]$Title,
        [string]$Command
    )

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
    ) | Out-Null
}

function Wait-ForPort {
    param(
        [int]$Port,
        [int]$MaxSeconds = 25
    )

    $elapsed = 0
    while ($elapsed -lt $MaxSeconds) {
        if (Test-TcpPort -Port $Port) {
            return $true
        }
        Start-Sleep -Seconds 1
        $elapsed++
    }
    return $false
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$root = $scriptDir
$backendPath = Join-Path $root "backend"
$frontendPath = Join-Path $root "frontend"
$venvActivate = if (Test-Path (Join-Path $backendPath ".venv\Scripts\Activate.ps1")) {
    Join-Path $backendPath ".venv\Scripts\Activate.ps1"
} elseif (Test-Path (Join-Path $backendPath "venv\Scripts\Activate.ps1")) {
    Join-Path $backendPath "venv\Scripts\Activate.ps1"
} else {
    Join-Path $backendPath ".venv\Scripts\Activate.ps1"
}

if (-not (Test-Path $backendPath)) {
    Write-Host "[ERROR] backend folder not found at $backendPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $frontendPath)) {
    Write-Host "[ERROR] frontend folder not found at $frontendPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $venvActivate)) {
    Write-Host "[ERROR] Python venv not found at $venvActivate" -ForegroundColor Red
    exit 1
}

# Start Neo4j if missing
if (Test-TcpPort -Port 7687) {
    Write-Host "[OK] Neo4j already running on 7687" -ForegroundColor Green
} else {
    $neo4jBat = $null
    $candidates = @(
        "D:\neo4j\neo4j-enterprise-2026.01.4\bin\neo4j.bat",
        "D:\neo4j\bin\neo4j.bat",
        "C:\neo4j\bin\neo4j.bat"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $neo4jBat = $candidate
            break
        }
    }

    if (-not $neo4jBat) {
        $found = Get-ChildItem -Path "D:\neo4j" -Filter "neo4j.bat" -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($found) {
            $neo4jBat = $found
        }
    }

    if (-not $neo4jBat) {
        $found = Get-ChildItem -Path "C:\neo4j" -Filter "neo4j.bat" -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($found) {
            $neo4jBat = $found
        }
    }

    if ($neo4jBat) {
        Write-Host "[INFO] Starting Neo4j (console mode): $neo4jBat" -ForegroundColor Yellow
        $neo4jHome = Split-Path -Parent (Split-Path -Parent $neo4jBat)
        Start-WindowCommand -Title "Neo4j Console" -Command "Set-Location '$neo4jHome'; & '$neo4jBat' console"

        if (Wait-ForPort -Port 7687 -MaxSeconds 35) {
            Write-Host "[OK] Neo4j is up" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Neo4j did not become ready yet; check Neo4j Console window" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] Neo4j executable not found under D:\neo4j or C:\neo4j" -ForegroundColor Yellow
    }
}

# Start Ollama (LLM) if missing
if (Test-TcpPort -Port 11434) {
    Write-Host "[OK] Ollama (LLM) already running on 11434" -ForegroundColor Green
} else {
    Write-Host "[INFO] Starting Ollama (LLM)" -ForegroundColor Yellow
    $ollamaCmd = "ollama serve"
    Start-WindowCommand -Title "Ollama Server" -Command $ollamaCmd
    if (Wait-ForPort -Port 11434 -MaxSeconds 25) {
        Write-Host "[OK] Ollama is up" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Ollama did not become ready yet; check Ollama server window" -ForegroundColor Yellow
    }
}

# Start Backend API if missing
if (Test-TcpPort -Port 8000) {
    Write-Host "[OK] Backend already running on 8000" -ForegroundColor Green
} else {
    Write-Host "[INFO] Starting Backend API" -ForegroundColor Yellow
    $backendCmd = "Set-Location '$backendPath'; & '$venvActivate'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Start-WindowCommand -Title "NeuroPent Backend" -Command $backendCmd
    if (Wait-ForPort -Port 8000 -MaxSeconds 25) {
        Write-Host "[OK] Backend is up" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Backend did not become ready yet; check backend window" -ForegroundColor Yellow
    }
}

# Start Celery worker if missing
$celeryRunning = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "celery\s+-A\s+app\.core\.celery_app\s+worker" }

if ($celeryRunning) {
    Write-Host "[OK] Celery worker already running" -ForegroundColor Green
} else {
    Write-Host "[INFO] Starting Celery worker" -ForegroundColor Yellow
    $celeryCmd = "Set-Location '$backendPath'; & '$venvActivate'; celery -A app.core.celery_app worker --loglevel=info --pool=solo"
    Start-WindowCommand -Title "NeuroPent Celery" -Command $celeryCmd
    Start-Sleep -Seconds 3
}

# Start Frontend if missing
if (Test-TcpPort -Port 5173) {
    Write-Host "[OK] Frontend already running on 5173" -ForegroundColor Green
} else {
    Write-Host "[INFO] Starting Frontend" -ForegroundColor Yellow
    $frontendCmd = "Set-Location '$frontendPath'; npm run dev"
    Start-WindowCommand -Title "NeuroPent Frontend" -Command $frontendCmd
    if (Wait-ForPort -Port 5173 -MaxSeconds 35) {
        Write-Host "[OK] Frontend is up" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Frontend did not become ready yet; check frontend window" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  STARTUP COMMANDS ISSUED" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Docs:     http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run check-local-services.ps1 to confirm health." -ForegroundColor Gray
