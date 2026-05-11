# Quick Service Status Check for NeuroPentWeb

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "NeuroPentWeb - Service Status Check" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Check PostgreSQL
Write-Host "Checking PostgreSQL..." -NoNewline
try {
    $pgTest = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue
    if ($pgTest.TcpTestSucceeded) {
        Write-Host " [RUNNING]" -ForegroundColor Green
    } else {
        Write-Host " [NOT RUNNING]" -ForegroundColor Red
    }
} catch {
    Write-Host " [ERROR]" -ForegroundColor Red
}

# Check Redis
Write-Host "Checking Redis..." -NoNewline
try {
    $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if ($redisTest.TcpTestSucceeded) {
        Write-Host " [RUNNING]" -ForegroundColor Green
    } else {
        Write-Host " [NOT RUNNING]" -ForegroundColor Red
    }
} catch {
    Write-Host " [ERROR]" -ForegroundColor Red
}

# Check Backend API
Write-Host "Checking Backend API..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -TimeoutSec 3
    Write-Host " [RUNNING]" -ForegroundColor Green
    Write-Host "  Version: $($response.version)" -ForegroundColor White
} catch {
    Write-Host " [NOT RUNNING]" -ForegroundColor Red
}

# Check Celery Worker (by checking Redis queue)
Write-Host "Checking Celery Worker..." -NoNewline
try {
    cd D:\NeuroPentWeb\backend
    & .\.venv\Scripts\python.exe -c "import redis; r = redis.Redis(host='localhost', port=6379, db=1); workers = r.keys('celery-task-meta-*'); print(f'Active tasks: {len(workers)}')" 2>$null
    Write-Host " [INFO]" -ForegroundColor Yellow
} catch {
    Write-Host " [UNKNOWN]" -ForegroundColor Yellow
}

Write-Host "`n--------------------------------------------" -ForegroundColor Cyan

# Get recent scans
Write-Host "`nRecent Scans:" -ForegroundColor Cyan
try {
    $scans = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" -Method Get -TimeoutSec 3
    if ($scans.Count -gt 0) {
        $scans | Select-Object -First 5 | ForEach-Object {
            Write-Host "  $($_.scan_id) - Status: $($_.status) - Target: $($_.target_url)" -ForegroundColor White
        }
    } else {
        Write-Host "  No scans yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Unable to fetch scans" -ForegroundColor Red
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Quick Actions:" -ForegroundColor Yellow
Write-Host "  1. View API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor White
Write-Host "  2. Test UI: D:\NeuroPentWeb\scripts\test_discovery_ui.html" -ForegroundColor White
Write-Host "  3. Create scan: Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/scans/' -Method POST -ContentType 'application/json' -Body '{\"target_url\": \"http://example.com\", \"scan_type\": \"full\"}'" -ForegroundColor White
Write-Host "============================================`n" -ForegroundColor Cyan

cd D:\NeuroPentWeb
