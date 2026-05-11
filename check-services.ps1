# Simple Service Status Check for RakshAI

Write-Host "`n========================" -ForegroundColor Cyan
Write-Host "  Service Status Check  " -ForegroundColor Cyan
Write-Host "========================`n" -ForegroundColor Cyan

$services = @(
    @{ Name = "PostgreSQL"; Port = 5432 },
    @{ Name = "Redis"; Port = 6379 },
    @{ Name = "Neo4j (Bolt)"; Port = 7687 },
    @{ Name = "Neo4j (HTTP)"; Port = 7474 },
    @{ Name = "Ollama"; Port = 11434 },
    @{ Name = "MinIO"; Port = 9000 }
)

$running = @()
$notRunning = @()

foreach ($service in $services) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $async = $tcp.BeginConnect("127.0.0.1", $service.Port, $null, $null)
        $wait = $async.AsyncWaitHandle.WaitOne(500)
        
        if ($wait -and $tcp.Connected) {
            Write-Host "✅ $($service.Name)".PadRight(30) "Port $($service.Port)" -ForegroundColor Green
            $running += $service.Name
        } else {
            Write-Host "❌ $($service.Name)".PadRight(30) "Port $($service.Port)" -ForegroundColor Red
            $notRunning += $service.Name
        }
        $tcp.Close()
    } catch {
        Write-Host "❌ $($service.Name)".PadRight(30) "Port $($service.Port)" -ForegroundColor Red
        $notRunning += $service.Name
    }
}

Write-Host ""
if ($notRunning.Count -eq 0) {
    Write-Host "All services running!" -ForegroundColor Green
} else {
    Write-Host "Start missing services:" -ForegroundColor Yellow
    foreach ($svc in $notRunning) {
        Write-Host "  - $svc" -ForegroundColor Gray
    }
}
Write-Host ""
