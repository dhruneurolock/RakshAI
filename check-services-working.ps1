#!/usr/bin/env powershell
# Clean and robust service status check for RakshAI

function Test-TcpPort {
    param(
        [int]$Port,
        [string]$ComputerName = "localhost",
        [int]$TimeoutMs = 1000
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

Write-Host "`n====== RakshAI Services Status ======`n" -ForegroundColor Cyan

$pgUp = Test-TcpPort -Port 5432
$redisUp = Test-TcpPort -Port 6379
$neo4jHttp = Get-HttpStatus -Url "http://localhost:7474"
$neo4jBolt = Test-TcpPort -Port 7687
$neo4jUp = $neo4jBolt -or ($neo4jHttp -in @(200, 401))
$ollamaUp = (Get-HttpStatus -Url "http://localhost:11434/api/tags") -eq 200
$backendUp = (Get-HttpStatus -Url "http://localhost:8000/health") -eq 200
$frontendUp = (Get-HttpStatus -Url "http://localhost:5173") -eq 200

# Optional services
$minioHttp = Get-HttpStatus -Url "http://localhost:9000"
$minioApi = Test-TcpPort -Port 9000
$minioConsole = Test-TcpPort -Port 9001
$minioUp = $minioApi -or ($minioHttp -in @(200, 403))

$critical = @(
    @{ Name = "PostgreSQL"; Up = $pgUp },
    @{ Name = "Redis"; Up = $redisUp },
    @{ Name = "Neo4j"; Up = $neo4jUp },
    @{ Name = "Ollama"; Up = $ollamaUp },
    @{ Name = "Backend API"; Up = $backendUp },
    @{ Name = "Frontend"; Up = $frontendUp }
)

$allRunning = $true
foreach ($service in $critical) {
    $status = if ($service.Up) { "[OK]" } else { "[DOWN]" }
    $color = if ($service.Up) { "Green" } else { "Red" }
    if (-not $service.Up) { $allRunning = $false }
    Write-Host ("{0,-25} {1}" -f $service.Name, $status) -ForegroundColor $color
}

Write-Host ""
Write-Host "Optional:" -ForegroundColor Cyan
Write-Host ("{0,-25} {1}" -f "MinIO", ($(if ($minioUp) { "[OK]" } else { "[INFO]" }))) -ForegroundColor ($(if ($minioUp) { "Green" } else { "Gray" }))
if ($minioUp) {
    Write-Host ("  HTTP={0}, API_PORT={1}, CONSOLE_PORT={2}" -f $minioHttp, $minioApi, $minioConsole) -ForegroundColor Gray
}

Write-Host ""
if ($allRunning) {
    Write-Host "All critical services are running!" -ForegroundColor Green
} else {
    Write-Host "Some critical services are not running" -ForegroundColor Yellow
}

Write-Host ""
