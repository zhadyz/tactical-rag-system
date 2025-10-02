# ============================================================
# TACTICAL RAG SYSTEM - SHUTDOWN SCRIPT
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    TACTICAL RAG SYSTEM - SHUTDOWN" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
$dockerRunning = $null
try {
    $dockerRunning = docker ps 2>$null
} catch {
    $dockerRunning = $null
}

if (-not $dockerRunning) {
    Write-Host "Docker is not running or no containers are active" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

# Check for running containers
Write-Host "Checking for active containers..." -ForegroundColor Yellow
$ragRunning = docker ps --filter "name=rag-tactical-system" --format "{{.Names}}" 2>$null
$ollamaRunning = docker ps --filter "name=ollama-server" --format "{{.Names}}" 2>$null

if (-not $ragRunning -and -not $ollamaRunning) {
    Write-Host "No RAG system containers are running" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

Write-Host ""
Write-Host "Active containers found:" -ForegroundColor Cyan
if ($ragRunning) {
    Write-Host "  • $ragRunning" -ForegroundColor Green
}
if ($ollamaRunning) {
    Write-Host "  • $ollamaRunning" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "    STOPPING SYSTEM" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

# Stop containers gracefully
Write-Host "Stopping containers gracefully..." -ForegroundColor Yellow
docker-compose stop

Write-Host ""
Write-Host "Removing containers..." -ForegroundColor Yellow
docker-compose down

# Verify shutdown
Write-Host ""
Write-Host "Verifying shutdown..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$stillRunning = docker ps --filter "name=rag-tactical-system" --filter "name=ollama-server" --format "{{.Names}}" 2>$null

if ($stillRunning) {
    Write-Host "WARNING: Some containers are still running" -ForegroundColor Red
    Write-Host "Run 'docker-compose down -v' to force remove" -ForegroundColor Yellow
} else {
    Write-Host "All containers stopped successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    SYSTEM STOPPED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Status:" -ForegroundColor Cyan
Write-Host "  ✓ Containers stopped and removed" -ForegroundColor Green
Write-Host "  ✓ Your documents are preserved in ./documents" -ForegroundColor Green
Write-Host "  ✓ Your database is preserved in ./chroma_db" -ForegroundColor Green
Write-Host "  ✓ Logs are preserved in ./logs" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  • To restart: Run .\deploy.ps1" -ForegroundColor Yellow
Write-Host "  • To clean everything: docker-compose down -v" -ForegroundColor Yellow
Write-Host "  • To view logs: docker-compose logs" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"