# ============================================================
# TACTICAL RAG SYSTEM - FIELD DEPLOYMENT SCRIPT
# ============================================================

# Display DoD Warning Banner
Write-Host ""
Write-Host "***********************************************************************" -ForegroundColor Red
Write-Host "                         WARNING NOTICE" -ForegroundColor Red
Write-Host "***********************************************************************" -ForegroundColor Yellow
Write-Host ""
Write-Host "You are accessing a U.S. Government (USG) Information System (IS) that" -ForegroundColor White
Write-Host "is provided for USG-authorized use only." -ForegroundColor White
Write-Host ""
Write-Host "By using this IS (which includes any device attached to this IS), you" -ForegroundColor White
Write-Host "consent to the following conditions:" -ForegroundColor White
Write-Host ""
Write-Host "- The USG routinely intercepts and monitors communications on this IS" -ForegroundColor White
Write-Host "  for purposes including, but not limited to, penetration testing," -ForegroundColor White
Write-Host "  COMSEC monitoring, network operations and defense, personnel" -ForegroundColor White
Write-Host "  misconduct (PM), law enforcement (LE), and counterintelligence (CI)" -ForegroundColor White
Write-Host "  investigations." -ForegroundColor White
Write-Host ""
Write-Host "- At any time, the USG may inspect and seize data stored on this IS." -ForegroundColor White
Write-Host ""
Write-Host "- Communications using, or data stored on, this IS are not private," -ForegroundColor White
Write-Host "  are subject to routine monitoring, interception, and search, and may" -ForegroundColor White
Write-Host "  be disclosed or used for any USG-authorized purpose." -ForegroundColor White
Write-Host ""
Write-Host "- This IS includes security measures (e.g., authentication and access" -ForegroundColor White
Write-Host "  controls) to protect USG interests--not for your personal benefit or" -ForegroundColor White
Write-Host "  privacy." -ForegroundColor White
Write-Host ""
Write-Host "***********************************************************************" -ForegroundColor Red
Write-Host ""
$consent = Read-Host "Type 'I AGREE' to continue"
if ($consent -ne "I AGREE") {
    Write-Host "Access denied. Exiting..." -ForegroundColor Red
    exit
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    TACTICAL RAG SYSTEM - DEPLOYMENT SCRIPT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
$dockerRunning = $null
try {
    $dockerRunning = docker ps 2>$null
}
catch {
    $dockerRunning = $null
}

if (-not $dockerRunning) {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and run this script again." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}
Write-Host "checkmark Docker is running" -ForegroundColor Green
Write-Host ""

# Check for code changes
Write-Host "Checking for code changes..." -ForegroundColor Yellow
$NeedsRebuild = $false
$ragImageExists = docker images -q ollama-rag-app:latest
$ollamaImageExists = docker images -q ollama/ollama:latest

if (-not $ragImageExists -or -not $ollamaImageExists) {
    Write-Host "Docker images not found - will build from scratch" -ForegroundColor Yellow
    $NeedsRebuild = $true
    
    # Check if tar files exist
    if ((Test-Path "rag-app-image.tar") -and (Test-Path "ollama-image.tar")) {
        Write-Host ""
        Write-Host "Found pre-built images - loading from files..." -ForegroundColor Cyan
        Write-Host "This is a ONE-TIME setup (takes 3-5 minutes)" -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "[1/3] Loading RAG application image..." -ForegroundColor Yellow
        docker load -i rag-app-image.tar
        Write-Host "checkmark RAG image loaded" -ForegroundColor Green
        
        Write-Host "[2/3] Loading Ollama image..." -ForegroundColor Yellow
        docker load -i ollama-image.tar
        Write-Host "checkmark Ollama image loaded" -ForegroundColor Green
        
        if (Test-Path "ollama-models.tar.gz") {
            Write-Host "[3/3] Restoring AI models..." -ForegroundColor Yellow
            docker run --rm -v ollama_ollama-data:/data -v ${PWD}:/backup alpine sh -c 'cd /data; tar xzf /backup/ollama-models.tar.gz'
            Write-Host "checkmark Models restored" -ForegroundColor Green
        }
        
        $NeedsRebuild = $false
        Write-Host ""
        Write-Host "checkmark Images loaded successfully!" -ForegroundColor Green
    }
}
elseif (Test-Path "_src") {
    $imageDate = docker inspect -f '{{.Created}}' ollama-rag-app:latest 2>$null
    if ($imageDate) {
        $imageTime = [DateTime]::Parse($imageDate)
        $newestFile = Get-ChildItem -Path "_src" -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        
        if ($newestFile -and $newestFile.LastWriteTime -gt $imageTime) {
            Write-Host "checkmark Code changes detected in: $($newestFile.Name)" -ForegroundColor Yellow
            Write-Host "  Modified: $($newestFile.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
            Write-Host "  Image built: $($imageTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
            $NeedsRebuild = $true
        }
        else {
            Write-Host "checkmark No code changes - using existing images" -ForegroundColor Green
        }
    }
}
else {
    Write-Host "checkmark Using existing images" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    STARTING SYSTEM" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check documents
if (-not (Test-Path "documents")) {
    Write-Host "Creating documents folder..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "documents" | Out-Null
    Write-Host "warning WARNING: documents/ folder is empty" -ForegroundColor Yellow
    Write-Host "  Add your mission documents to the documents/ folder" -ForegroundColor Yellow
    Write-Host ""
}

$docCount = (Get-ChildItem -Path "documents" -File -Recurse | Where-Object { $_.Extension -match '\.(pdf|txt|docx|doc|md)$' }).Count
Write-Host "Documents found: $docCount" -ForegroundColor Cyan

# Check database
if (Test-Path "chroma_db") {
    $dbFiles = Get-ChildItem -Path "chroma_db" -Recurse -File
    Write-Host "Vector database: EXISTS ($($dbFiles.Count) files)" -ForegroundColor Green
    Write-Host "  -> Will use cached index" -ForegroundColor Cyan
}
else {
    Write-Host "Vector database: NOT FOUND" -ForegroundColor Yellow
    Write-Host "  -> Will index $docCount documents on startup" -ForegroundColor Cyan
    Write-Host "  -> Estimated time: 1-5 minutes" -ForegroundColor Yellow
}

Write-Host ""

# Force rebuild if --rebuild flag passed
if ($args -contains "--rebuild") {
    Write-Host "Forcing rebuild..." -ForegroundColor Yellow
    docker-compose build
}

# Start containers
if ($NeedsRebuild) {
    Write-Host "Building and starting containers..." -ForegroundColor Yellow
    docker-compose up -d --build
}
else {
    Write-Host "Starting containers..." -ForegroundColor Yellow
    docker-compose up -d
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    INITIALIZATION IN PROGRESS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Health monitoring
$maxAttempts = 60
$attempt = 0
$allHealthy = $false
$lastLogLine = ""

while ($attempt -lt $maxAttempts -and -not $allHealthy) {
    $attempt++
    
    $ollamaStatus = docker inspect -f '{{.State.Status}}' ollama-server 2>$null
    $ragStatus = docker inspect -f '{{.State.Status}}' rag-tactical-system 2>$null
    
    Write-Host "`r[Check $attempt/$maxAttempts] " -NoNewline
    
    if ($ollamaStatus -eq "running") {
        Write-Host "Ollama: UP" -NoNewline -ForegroundColor Green
    }
    else {
        Write-Host "Ollama: STARTING" -NoNewline -ForegroundColor Yellow
    }
    
    Write-Host " | " -NoNewline
    
    if ($ragStatus -eq "running") {
        Write-Host "RAG: UP" -NoNewline -ForegroundColor Green
    }
    else {
        Write-Host "RAG: STARTING" -NoNewline -ForegroundColor Yellow
    }
    
    # Monitor logs
    if ($ragStatus -eq "running") {
        $logs = docker logs rag-tactical-system --tail 1 2>$null
        if ($logs -and $logs -ne $lastLogLine) {
            $lastLogLine = $logs
            
            if ($logs -match "Ollama server is ready") {
                Write-Host "`n  checkmark Ollama server connected" -ForegroundColor Green
            }
            elseif ($logs -match "model pulled|model already installed") {
                Write-Host "`n  checkmark AI models loaded" -ForegroundColor Green
            }
            elseif ($logs -match "Embedding model ready") {
                Write-Host "`n  checkmark Embedding model initialized" -ForegroundColor Green
            }
            elseif ($logs -match "Vector store loaded") {
                Write-Host "`n  checkmark Vector database loaded" -ForegroundColor Green
            }
            elseif ($logs -match "Indexing completed|successfully processed") {
                Write-Host "`n  checkmark Document indexing complete" -ForegroundColor Green
            }
            elseif ($logs -match "LLM ready") {
                Write-Host "`n  checkmark Language model ready" -ForegroundColor Green
            }
            elseif ($logs -match "retrieval engine ready") {
                Write-Host "`n  checkmark Retrieval engine initialized" -ForegroundColor Green
            }
            elseif ($logs -match "Generated.*example") {
                Write-Host "`n  checkmark Example questions generated" -ForegroundColor Green
            }
            elseif ($logs -match "SYSTEM READY") {
                Write-Host "`n  checkmark System initialization complete!" -ForegroundColor Green
            }
            elseif ($logs -match "Running on.*7860") {
                Write-Host "`n  checkmark Web interface started" -ForegroundColor Green
            }
            elseif ($logs -match "ERROR|Failed|failed") {
                Write-Host "`n  warning $logs" -ForegroundColor Red
            }
        }
    }
    
    # Check web interface
    if ($ollamaStatus -eq "running" -and $ragStatus -eq "running") {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:7860" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "`n`ncheckmark Web interface is responding!" -ForegroundColor Green
                $allHealthy = $true
                break
            }
        }
        catch {
            # Still starting
        }
    }
    
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host ""

if ($allHealthy) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "    SYSTEM READY" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "checkmark All services operational" -ForegroundColor Green
    Write-Host "checkmark $docCount documents indexed" -ForegroundColor Green
    Write-Host "checkmark Web interface accessible" -ForegroundColor Green
}
else {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "    STARTUP IN PROGRESS" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "warning System is taking longer than expected" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Monitor progress with: docker-compose logs -f rag-app" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Cyan
Start-Process "http://localhost:7860"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    QUICK REFERENCE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access system:    http://localhost:7860" -ForegroundColor White
Write-Host "View logs:        docker-compose logs -f rag-app" -ForegroundColor White
Write-Host "Stop system:      .\stop.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"