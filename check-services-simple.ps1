#!/usr/bin/env powershell
<# 
    Simple Service Status Check for RakshAI
    Checks if required services are running on expected ports
#>

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         RakshAI Service Status Check                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$services = @(
    @{ Name = "PostgreSQL"; Port = 5432; URL = $null },
    @{ Name = "Redis"; Port = 6379; URL = $null },
    @{ Name = "Neo4j"; Port = 7687; URL = $null },
    @{ Name = "Neo4j Browser"; Port = 7474; URL = "http://localhost:7474" },
    @{ Name = "Ollama"; Port = 11434; URL = "http://localhost:11434/api/tags" },
    @{ Name = "MinIO"; Port = 9000; URL = "http://localhost:9000" },
)

$allRunning = $true

foreach ($service in $services) {
    $result = $false
    
    if ($service.URL) {
        # Test HTTP endpoint
        try {
            $response = Invoke-WebRequest -Uri $service.URL -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            $result = $response.StatusCode -eq 200
        } catch {
            $result = $false
        }
    } else {
        # Test TCP port
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $asyncResult = $tcpClient.BeginConnect("127.0.0.1", $service.Port, $null, $null)
            $result = $asyncResult.AsyncWaitHandle.WaitOne(1000, $false)
            $tcpClient.Close()
        } catch {
            $result = $false
        }
    }
    
    $status = if ($result) { "✅ RUNNING" } else { "❌ NOT RUNNING" }
    $color = if ($result) { "Green" } else { "Red" }
    
    if (-not $result) { $allRunning = $false }
    
    Write-Host "$($service.Name):".PadRight(20) -ForegroundColor White -NoNewline
    Write-Host $status -ForegroundColor $color
}

Write-Host ""
if ($allRunning) {
    Write-Host "✅ All services are running!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some services are not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start missing services:" -ForegroundColor Yellow
    Write-Host "  - PostgreSQL: start PostgreSQL service" -ForegroundColor Gray
    Write-Host "  - Redis: redis-server (or Memurai service for Windows)" -ForegroundColor Gray
    Write-Host "  - Neo4j: neo4j start" -ForegroundColor Gray
    Write-Host "  - Ollama: ollama serve" -ForegroundColor Gray
    Write-Host "  - MinIO: minio server ./storage" -ForegroundColor Gray
}

Write-Host ""
