# RakshAI - Local Services Health Check
# Robust checker for local development dependencies and apps.

$ErrorActionPreference = "Continue"

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

function Get-HttpStatus {
    param(
        [string]$Url,
        [int]$TimeoutSec = 3
    )

    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return [int]$resp.StatusCode
    } catch {
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            return [int]$_.Exception.Response.StatusCode
        }
        return -1
    }
}

function Write-ServiceStatus {
    param(
        [string]$Name,
        [bool]$IsUp,
        [string]$DetailWhenUp = "",
        [string]$DetailWhenDown = ""
    )

    if ($IsUp) {
        Write-Host ("  [OK]   " + $Name) -ForegroundColor Green
        if ($DetailWhenUp) {
            Write-Host ("         " + $DetailWhenUp) -ForegroundColor Gray
        }
    } else {
        Write-Host ("  [DOWN] " + $Name) -ForegroundColor Red
        if ($DetailWhenDown) {
            Write-Host ("         " + $DetailWhenDown) -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LOCAL SERVICES HEALTH CHECK" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allHealthy = $true

# 1) PostgreSQL
$pgUp = Test-TcpPort -Port 5432
Write-ServiceStatus -Name "PostgreSQL (5432)" -IsUp $pgUp -DetailWhenDown "Start PostgreSQL service"
if (-not $pgUp) { $allHealthy = $false }
Write-Host ""

# 2) Redis
$redisUp = Test-TcpPort -Port 6379
Write-ServiceStatus -Name "Redis (6379)" -IsUp $redisUp -DetailWhenDown "Start Memurai/Redis service"
if (-not $redisUp) { $allHealthy = $false }
Write-Host ""

# 3) Neo4j (accept either browser http or bolt listener)
$neo4jBrowserStatus = Get-HttpStatus -Url "http://localhost:7474"
$neo4jBoltUp = Test-TcpPort -Port 7687
$neo4jUp = $neo4jBoltUp -or ($neo4jBrowserStatus -in @(200, 401))
Write-ServiceStatus -Name "Neo4j (7474/7687)" -IsUp $neo4jUp -DetailWhenUp ("HTTP=" + $neo4jBrowserStatus + ", BOLT=" + $neo4jBoltUp) -DetailWhenDown "Start Neo4j from D:\neo4j\...\bin\neo4j.bat"
if (-not $neo4jUp) { $allHealthy = $false }
Write-Host ""

# 4) Ollama
$ollamaStatus = Get-HttpStatus -Url "http://localhost:11434/api/tags"
$ollamaUp = $ollamaStatus -eq 200
Write-ServiceStatus -Name "Ollama (11434)" -IsUp $ollamaUp -DetailWhenUp "API /api/tags reachable" -DetailWhenDown "Run: ollama serve"
if (-not $ollamaUp) { $allHealthy = $false }
Write-Host ""

# 5) Backend API (health endpoint is authoritative)
$backendHealthStatus = Get-HttpStatus -Url "http://localhost:8000/health"
$backendDocsStatus = Get-HttpStatus -Url "http://localhost:8000/api/v1/docs"
$backendUp = ($backendHealthStatus -eq 200) -or ($backendDocsStatus -eq 200)
Write-ServiceStatus -Name "Backend API (8000)" -IsUp $backendUp -DetailWhenUp ("/health=" + $backendHealthStatus + ", /api/v1/docs=" + $backendDocsStatus) -DetailWhenDown "Run: .\start-local.ps1"
if (-not $backendUp) { $allHealthy = $false }
Write-Host ""

# 6) Celery worker (optional but useful)
$celeryProc = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "celery\s+-A\s+app\.core\.celery_app\s+worker" }
$celeryUp = $null -ne $celeryProc
if ($celeryUp) {
    $pidText = ($celeryProc | Select-Object -First 1).ProcessId
    Write-ServiceStatus -Name "Celery Worker" -IsUp $true -DetailWhenUp ("PID=" + $pidText)
} else {
    Write-Host "  [WARN] Celery Worker" -ForegroundColor Yellow
    Write-Host "         Not running (optional for UI/API smoke checks)" -ForegroundColor Gray
}
Write-Host ""

# 7) Frontend
$frontendStatus = Get-HttpStatus -Url "http://localhost:5173"
$frontendUp = $frontendStatus -eq 200
Write-ServiceStatus -Name "Frontend (5173)" -IsUp $frontendUp -DetailWhenDown "Run: cd frontend; npm run dev"
if (-not $frontendUp) { $allHealthy = $false }
Write-Host ""

# 8) Optional Services
Write-Host "Optional Services:" -ForegroundColor Cyan

# MinIO may return 200 or 403 depending on endpoint/auth config.
$minioStatus = Get-HttpStatus -Url "http://localhost:9000"
$minioPortUp = Test-TcpPort -Port 9000
$minioConsoleUp = Test-TcpPort -Port 9001
$minioUp = $minioPortUp -or ($minioStatus -in @(200, 403))
if ($minioUp) {
    Write-Host "  [OK]   MinIO (9000/9001)" -ForegroundColor Green
    Write-Host ("         HTTP=" + $minioStatus + ", API_PORT=" + $minioPortUp + ", CONSOLE_PORT=" + $minioConsoleUp) -ForegroundColor Gray
} else {
    Write-Host "  [INFO] MinIO (optional)" -ForegroundColor Gray
    Write-Host "         Not detected" -ForegroundColor Gray
}

$chromaStatus = Get-HttpStatus -Url "http://localhost:8001"
if ($chromaStatus -eq 200) {
    Write-Host "  [OK]   ChromaDB (8001)" -ForegroundColor Green
} else {
    Write-Host "  [INFO] ChromaDB (optional)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allHealthy) {
    Write-Host "  [OK]   ALL CRITICAL SERVICES HEALTHY" -ForegroundColor Green
} else {
    Write-Host "  [DOWN] SOME CRITICAL SERVICES ARE NOT RUNNING" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "System Resources:" -ForegroundColor Cyan
$cpu = Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average
$mem = Get-WmiObject Win32_OperatingSystem
$memUsedGB = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / 1MB, 2)
$memTotalGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
$memPercent = [math]::Round(($memUsedGB / $memTotalGB) * 100, 1)
Write-Host ("  CPU Usage: " + $cpu + "%") -ForegroundColor White
Write-Host ("  RAM Usage: " + $memUsedGB + " GB / " + $memTotalGB + " GB (" + $memPercent + "%)") -ForegroundColor White

Write-Host ""
$drive = Get-PSDrive D
$freeGB = [math]::Round($drive.Free / 1GB, 2)
$totalGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
$usedPercent = [math]::Round((($totalGB - $freeGB) / $totalGB) * 100, 1)
Write-Host "Disk Space (D:):" -ForegroundColor Cyan
Write-Host ("  Free: " + $freeGB + " GB / " + $totalGB + " GB (" + $usedPercent + "% used)") -ForegroundColor White
Write-Host ""

if (-not $allHealthy) {
    Write-Host "Quick Fix:" -ForegroundColor Yellow
    Write-Host "  .\start-local.ps1" -ForegroundColor Gray
    Write-Host "" 
}

Write-Host "For setup details, see LOCAL-MACHINE-SETUP.md" -ForegroundColor Cyan
Write-Host ""

