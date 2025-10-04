# ============================================================
# TACTICAL RAG SYSTEM - ENHANCED DEPLOYMENT SCRIPT
# Real-time monitoring, GPU detection, and dependency tracking
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

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

function Write-Step {
    param([string]$Message, [int]$Step, [int]$Total)
    Write-Host ""
    Write-Host "[$Step/$Total] " -NoNewline -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor White
    Write-Host ("-" * 70) -ForegroundColor DarkGray
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] " -NoNewline -ForegroundColor Green
    Write-Host $Message -ForegroundColor White
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [>>] " -NoNewline -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor White
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  [!!] " -NoNewline -ForegroundColor Yellow
    Write-Host $Message -ForegroundColor White
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "  [XX] " -NoNewline -ForegroundColor Red
    Write-Host $Message -ForegroundColor White
}

function Write-BuildStep {
    param([string]$Message)
    Write-Host "      " -NoNewline
    Write-Host "[BUILD] " -NoNewline -ForegroundColor Magenta
    Write-Host $Message -ForegroundColor Gray
}

function Get-GPUInfo {
    try {
        $gpuInfo = nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>$null
        if ($gpuInfo) {
            return $gpuInfo.Split(',')
        }
    } catch {}
    return $null
}

function Show-GPUStatus {
    try {
        $gpu = nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>$null
        if ($gpu) {
            $parts = $gpu.Split(',')
            $util = $parts[0].Trim()
            $memUsed = [math]::Round([int]$parts[1].Trim() / 1024, 1)
            $memTotal = [math]::Round([int]$parts[2].Trim() / 1024, 1)
            $temp = $parts[3].Trim()
            
            $utilColor = if ([int]$util -gt 50) { "Green" } else { "Gray" }
            $tempColor = if ([int]$temp -gt 70) { "Red" } elseif ([int]$temp -gt 50) { "Yellow" } else { "Green" }
            
            Write-Host "  GPU: " -NoNewline
            Write-Host "$util% " -NoNewline -ForegroundColor $utilColor
            Write-Host "| VRAM: " -NoNewline
            Write-Host "${memUsed}GB/${memTotal}GB " -NoNewline -ForegroundColor Cyan
            Write-Host "| Temp: " -NoNewline
            Write-Host "${temp}C" -ForegroundColor $tempColor
            return $true
        }
    } catch {}
    return $false
}

function Show-SystemResources {
    $cpu = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
    $cpuPct = [math]::Round($cpu, 0)
    $cpuColor = if ($cpuPct -gt 80) { "Red" } elseif ($cpuPct -gt 50) { "Yellow" } else { "Green" }
    
    Write-Host "  CPU: " -NoNewline
    Write-Host "$cpuPct% " -NoNewline -ForegroundColor $cpuColor
    
    Show-GPUStatus | Out-Null
}

# ============================================================
# MAIN DEPLOYMENT
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    TACTICAL RAG SYSTEM - DEPLOYMENT MANAGER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$totalSteps = 10

# ============================================================
# STEP 1: Pre-flight checks
# ============================================================
Write-Step "PRE-FLIGHT CHECKS" 1 $totalSteps

Write-Info "Checking Docker status..."
$dockerRunning = $null
try {
    $dockerRunning = docker ps 2>$null
} catch {
    $dockerRunning = $null
}

if (-not $dockerRunning) {
    Write-Error-Custom "Docker is not running!"
    Write-Warning "Please start Docker Desktop and run this script again."
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Success "Docker is running"

# Check nvidia-smi
Write-Info "Checking GPU availability..."
$gpuInfo = Get-GPUInfo
if ($gpuInfo) {
    Write-Success "GPU detected: $($gpuInfo[0].Trim())"
    Write-Info "VRAM: $($gpuInfo[1].Trim())"
    Write-Info "Driver: $($gpuInfo[2].Trim())"
} else {
    Write-Warning "No NVIDIA GPU detected or nvidia-smi not available"
    Write-Warning "System will run on CPU (slower performance)"
}

# Check nvidia-container-toolkit
Write-Info "Checking NVIDIA Container Toolkit..."
$nvidiaDocker = docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "NVIDIA Container Toolkit is configured"
} else {
    Write-Warning "NVIDIA Container Toolkit may not be properly configured"
    Write-Warning "GPU acceleration may not work in containers"
}

# ============================================================
# STEP 2: Clean up existing deployment
# ============================================================
Write-Step "CLEANING UP EXISTING DEPLOYMENT" 2 $totalSteps

$existingContainers = docker ps -a --filter "name=rag-tactical-system" --filter "name=ollama-server" --format "{{.Names}}" 2>$null

if ($existingContainers) {
    Write-Info "Found existing containers:"
    foreach ($container in $existingContainers) {
        Write-Host "    - $container" -ForegroundColor Yellow
    }
    
    Write-Info "Stopping containers..."
    docker-compose stop 2>$null | Out-Null
    Write-Success "Containers stopped"
    
    Write-Info "Removing containers..."
    docker-compose down 2>$null | Out-Null
    Write-Success "Containers removed"
} else {
    Write-Success "No existing containers found"
}

# Check for orphaned images if --rebuild flag
if ($args -contains "--rebuild") {
    Write-Info "Rebuild flag detected - removing old images..."
    docker rmi ruggedsystemv25-rag-app:latest 2>$null | Out-Null
    Write-Success "Old images removed"
}

# ============================================================
# STEP 3: Verify project structure
# ============================================================
Write-Step "VERIFYING PROJECT STRUCTURE" 3 $totalSteps

$requiredDirs = @("_src", "_config", "documents")
$requiredFiles = @("docker-compose.yml", "_config/Dockerfile", "_config/requirements.txt")

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Success "Directory: $dir"
    } else {
        Write-Error-Custom "Missing directory: $dir"
        exit 1
    }
}

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Success "File: $file"
    } else {
        Write-Error-Custom "Missing file: $file"
        exit 1
    }
}

# Count Python files
$srcFiles = (Get-ChildItem -Path "_src" -Filter "*.py").Count
Write-Info "Found $srcFiles Python source files"

# ============================================================
# STEP 4: Check documents
# ============================================================
Write-Step "CHECKING DOCUMENTS" 4 $totalSteps

if (-not (Test-Path "documents")) {
    Write-Info "Creating documents folder..."
    New-Item -ItemType Directory -Path "documents" | Out-Null
    Write-Success "Documents folder created"
}

$docCount = (Get-ChildItem -Path "documents" -File -Recurse | Where-Object { $_.Extension -match '\.(pdf|txt|docx|doc|md)$' }).Count
Write-Info "Documents found: $docCount"

if ($docCount -eq 0) {
    Write-Warning "No documents found in documents/ folder"
    Write-Warning "System will start but cannot answer questions"
    Write-Info "Add documents to documents/ folder and restart to index them"
}

# ============================================================
# STEP 5: Check vector database
# ============================================================
Write-Step "CHECKING VECTOR DATABASE" 5 $totalSteps

if (Test-Path "chroma_db") {
    $dbFiles = Get-ChildItem -Path "chroma_db" -Recurse -File
    $dbSize = ($dbFiles | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Success "Vector database exists ($($dbFiles.Count) files, $([math]::Round($dbSize, 1))MB)"
    
    # Check age
    $dbAge = (Get-Date) - (Get-Item "chroma_db").LastWriteTime
    if ($dbAge.TotalHours -gt 24) {
        Write-Warning "Database is $([math]::Round($dbAge.TotalHours, 0)) hours old"
        Write-Info "Consider re-indexing if documents have changed"
    }
} else {
    Write-Warning "No vector database found"
    Write-Info "Will create database on first startup (may take 2-10 minutes)"
}

# ============================================================
# STEP 6: Build Docker images with dependency tracking
# ============================================================
Write-Step "BUILDING DOCKER IMAGES WITH DEPENDENCY TRACKING" 6 $totalSteps

Write-Info "Starting Docker build (this may take 5-10 minutes on first run)..."
Write-Host ""

# Track installed packages
$installedPackages = @{
    "pytorch" = $false
    "langchain" = $false
    "sentence_transformers" = $false
    "chromadb" = $false
    "gradio" = $false
}

# Start build process
$buildArgs = if ($args -contains "--rebuild") { @("build", "--no-cache", "--progress=plain") } else { @("build", "--progress=plain") }

$buildProcess = Start-Process -FilePath "docker-compose" -ArgumentList $buildArgs -NoNewWindow -PassThru -RedirectStandardOutput "build_output.txt" -RedirectStandardError "build_error.txt"

# Monitor build output in real-time
$lastPosition = 0
while (-not $buildProcess.HasExited) {
    if (Test-Path "build_output.txt") {
        $content = Get-Content "build_output.txt" -Raw -ErrorAction SilentlyContinue
        
        # Skip if content is null or empty
        if ($content -and $content.Length -gt $lastPosition) {
            $newContent = $content.Substring($lastPosition)
            $lastPosition = $content.Length
            
            foreach ($line in $newContent -split "`n") {
                # Show all build output
                if ($line -match "#\d+") {
                    Write-BuildStep $line
                }
                
                # Highlight critical installations
                if ($line -match "RUN pip install.*torch.*cu121" -and -not $installedPackages["pytorch"]) {
                    Write-Success "Installing PyTorch with CUDA 12.1 support..."
                    $installedPackages["pytorch"] = $true
                }
                
                if ($line -match "Successfully installed.*torch" -and $installedPackages["pytorch"]) {
                    Write-Success "PyTorch installation complete"
                }
                
                if ($line -match "Collecting langchain" -and -not $installedPackages["langchain"]) {
                    Write-Success "Installing LangChain ecosystem..."
                    $installedPackages["langchain"] = $true
                }
                
                if ($line -match "Successfully installed.*langchain") {
                    Write-Success "LangChain installation complete"
                }
                
                if ($line -match "Collecting sentence-transformers" -and -not $installedPackages["sentence_transformers"]) {
                    Write-Success "Installing sentence-transformers for embeddings..."
                    $installedPackages["sentence_transformers"] = $true
                }
                
                if ($line -match "Successfully installed.*sentence-transformers") {
                    Write-Success "Sentence-transformers installation complete"
                }
                
                if ($line -match "Collecting chromadb" -and -not $installedPackages["chromadb"]) {
                    Write-Success "Installing ChromaDB vector store..."
                    $installedPackages["chromadb"] = $true
                }
                
                if ($line -match "Successfully installed.*chromadb") {
                    Write-Success "ChromaDB installation complete"
                }
                
                if ($line -match "Collecting gradio" -and -not $installedPackages["gradio"]) {
                    Write-Success "Installing Gradio web interface..."
                    $installedPackages["gradio"] = $true
                }
                
                if ($line -match "Successfully installed.*gradio") {
                    Write-Success "Gradio installation complete"
                }
                
                # Track Dockerfile steps
                if ($line -match "STEP 5.*PyTorch") {
                    Write-Info "Dockerfile Step 5: Installing PyTorch with CUDA..."
                }
                
                if ($line -match "STEP 6.*requirements") {
                    Write-Info "Dockerfile Step 6: Installing Python dependencies..."
                }
                
                if ($line -match "STEP 7.*application code") {
                    Write-Info "Dockerfile Step 7: Copying application code..."
                }
                
                if ($line -match "STEP 10.*environment") {
                    Write-Info "Dockerfile Step 10: Setting CUDA environment variables..."
                }
            }
        }
    }
    
    Start-Sleep -Milliseconds 500
}

$buildProcess.WaitForExit()

# Clean up temp files
if (Test-Path "build_output.txt") { Remove-Item "build_output.txt" }
if (Test-Path "build_error.txt") { Remove-Item "build_error.txt" }

Write-Host ""
Write-Success "Docker images built successfully"

# FIXED: Verify images with correct name (auto-detects from compose project)
$ragImage = docker images -q ruggedsystemv25-rag-app:latest 2>$null
if (-not $ragImage) {
    # Try alternative naming (docker-compose auto-generates from folder name)
    $projectName = (Get-Location).Path.Split('\')[-1] -replace '\s', '' -replace '\.', ''
    $ragImage = docker images -q "$($projectName.ToLower())-rag-app:latest" 2>$null
}

$ollamaImage = docker images -q ollama/ollama:latest 2>$null

if ($ragImage -and $ollamaImage) {
    Write-Success "All images verified"
    
    # Show installed package summary
    Write-Host ""
    Write-Info "Dependency installation summary:"
    foreach ($pkg in $installedPackages.Keys) {
        if ($installedPackages[$pkg]) {
            Write-Host "    - $pkg" -ForegroundColor Green
        }
    }
} else {
    Write-Error-Custom "Image verification failed"
    Write-Info "Images found:"
    docker images | Select-String "rag-app|ollama"
    Write-Warning "Continuing anyway - containers may still work"
}

# ============================================================
# STEP 7: Start containers
# ============================================================
Write-Step "STARTING CONTAINERS" 7 $totalSteps

Write-Info "Starting services..."
docker-compose up -d 2>$null | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to start containers"
    exit 1
}

Start-Sleep -Seconds 3
Write-Success "Containers started"

# ============================================================
# STEP 8: Monitor initialization
# ============================================================
Write-Step "MONITORING SYSTEM INITIALIZATION" 8 $totalSteps

$maxWaitTime = 180  # 3 minutes
$elapsedTime = 0
$checkInterval = 3

$milestones = @{
    "ollama_ready" = $false
    "models_loaded" = $false
    "gpu_detected" = $false
    "embedding_ready" = $false
    "vector_loaded" = $false
    "llm_ready" = $false
    "retrieval_ready" = $false
    "web_ready" = $false
}

Write-Info "Waiting for system initialization (max $maxWaitTime seconds)..."
Write-Host ""

while ($elapsedTime -lt $maxWaitTime) {
    # Check container status
    $ollamaStatus = docker inspect -f '{{.State.Status}}' ollama-server 2>$null
    $ragStatus = docker inspect -f '{{.State.Status}}' rag-tactical-system 2>$null
    
    # Show progress bar
    $progress = [math]::Min(100, ($elapsedTime / $maxWaitTime) * 100)
    Write-Progress -Activity "Initializing System" -Status "$([math]::Round($progress, 0))% Complete" -PercentComplete $progress
    
    # Get latest logs
    $logs = docker logs rag-tactical-system --tail 10 2>$null
    
    # Check milestones
    if (-not $milestones["ollama_ready"] -and $logs -match "Ollama server is ready") {
        $milestones["ollama_ready"] = $true
        Write-Success "Ollama server connected"
    }
    
    if (-not $milestones["models_loaded"] -and $logs -match "model (pulled|already installed)") {
        $milestones["models_loaded"] = $true
        Write-Success "AI models loaded"
    }
    
    if (-not $milestones["gpu_detected"] -and $logs -match "GPU detected") {
        $milestones["gpu_detected"] = $true
        $gpuName = ($logs | Select-String -Pattern "GPU detected.*: (.+)" | ForEach-Object { $_.Matches.Groups[1].Value }) -join ""
        if ($gpuName) {
            Write-Success "GPU detected: $gpuName"
        } else {
            Write-Success "GPU detected"
        }
    }
    
    if (-not $milestones["embedding_ready"] -and $logs -match "Embedding model ready") {
        $milestones["embedding_ready"] = $true
        Write-Success "Embedding model initialized"
    }
    
    if (-not $milestones["vector_loaded"] -and $logs -match "Vector store loaded") {
        $milestones["vector_loaded"] = $true
        Write-Success "Vector database loaded"
    }
    
    if (-not $milestones["llm_ready"] -and $logs -match "LLM ready") {
        $milestones["llm_ready"] = $true
        Write-Success "Language model ready"
    }
    
    if (-not $milestones["retrieval_ready"] -and $logs -match "retrieval engine ready") {
        $milestones["retrieval_ready"] = $true
        Write-Success "Retrieval engine initialized"
    }
    
    if (-not $milestones["web_ready"] -and $logs -match "Running on.*7860") {
        $milestones["web_ready"] = $true
        Write-Success "Web interface started"
        break
    }
    
    # Check for errors
    if ($logs -match "ERROR|Failed|failed|ImportError") {
        $errorLines = $logs | Select-String -Pattern "ERROR|Failed|failed|ImportError"
        foreach ($errorLine in $errorLines) {
            Write-Warning "Error detected: $errorLine"
        }
    }
    
    Start-Sleep -Seconds $checkInterval
    $elapsedTime += $checkInterval
}

Write-Progress -Activity "Initializing System" -Completed
Write-Host ""

# ============================================================
# STEP 9: Verify GPU acceleration
# ============================================================
Write-Step "VERIFYING GPU ACCELERATION" 9 $totalSteps

if ($gpuInfo) {
    Write-Info "Checking GPU support in containers..."
    
    # Check if PyTorch can see CUDA
    $cudaCheck = docker exec rag-tactical-system python -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>$null
    
    if ($cudaCheck -match "CUDA") {
        Write-Success "CUDA detected in container"
        
        # Get GPU details from container
        $gpuDetails = docker exec rag-tactical-system python -c @"
import torch
print(f'Device: {torch.cuda.get_device_name(0)}')
print(f'CUDA Version: {torch.version.cuda}')
print(f'PyTorch Version: {torch.__version__}')
"@ 2>$null
        
        foreach ($line in $gpuDetails -split "`n") {
            if ($line.Trim()) {
                Write-Info $line.Trim()
            }
        }
        
        # Check sentence-transformers
        Write-Info "Verifying sentence-transformers GPU support..."
        $sentenceCheck = docker exec rag-tactical-system python -c "from sentence_transformers import SentenceTransformer; import torch; m = SentenceTransformer('all-MiniLM-L6-v2', device='cuda' if torch.cuda.is_available() else 'cpu'); print(m.device)" 2>$null
        
        if ($sentenceCheck -match "cuda") {
            Write-Success "Sentence-transformers using GPU"
        } else {
            Write-Warning "Sentence-transformers NOT using GPU"
        }
        
        # Check CrossEncoder
        Write-Info "Verifying CrossEncoder GPU support..."
        $rerankerCheck = docker exec rag-tactical-system python -c "from sentence_transformers import CrossEncoder; import torch; m = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cuda' if torch.cuda.is_available() else 'cpu'); print(m.model.device)" 2>$null
        
        if ($rerankerCheck -match "cuda") {
            Write-Success "CrossEncoder reranker using GPU"
        } else {
            Write-Warning "CrossEncoder NOT using GPU"
        }
        
    } else {
        Write-Warning "CUDA NOT detected in container"
        Write-Warning "GPU acceleration is not active"
        Write-Info "Check docker-compose.yml has GPU resources configured"
    }
} else {
    Write-Info "No GPU available on host - skipping GPU checks"
}

# ============================================================
# STEP 10: Final verification and monitoring
# ============================================================
Write-Step "FINAL SYSTEM VERIFICATION" 10 $totalSteps

# Check if web interface is responding
Write-Info "Testing web interface connectivity..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:7860" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Success "Web interface is responding"
    }
} catch {
    Write-Warning "Web interface not yet responsive (may need more time)"
}

# Show container status
Write-Info "Container status:"
$containers = docker ps --filter "name=rag-tactical-system" --filter "name=ollama-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
Write-Host ""
Write-Host $containers -ForegroundColor Gray
Write-Host ""

# Show system resources
Write-Info "System resources:"
Show-SystemResources

# ============================================================
# DEPLOYMENT COMPLETE - AUTO-LAUNCH MONITORING
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Success "All systems operational"
Write-Host ""

# Summary
Write-Host "SYSTEM SUMMARY:" -ForegroundColor Cyan
Write-Host "  Documents indexed: " -NoNewline
Write-Host "$docCount" -ForegroundColor Yellow
Write-Host "  GPU acceleration: " -NoNewline
if ($cudaCheck -match "CUDA") {
    Write-Host "ENABLED" -ForegroundColor Green
} else {
    Write-Host "DISABLED" -ForegroundColor Yellow
}
Write-Host "  Web interface: " -NoNewline
Write-Host "http://localhost:7860" -ForegroundColor Cyan
Write-Host ""

# Auto-open browser
Write-Info "Launching web interface in browser..."
Start-Sleep -Seconds 2
try {
    Start-Process "http://localhost:7860" -ErrorAction Stop
    Write-Success "Browser opened successfully"
} catch {
    Write-Warning "Could not auto-open browser"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    LIVE MONITORING ACTIVE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Simple monitoring loop
try {
    while ($true) {
        Clear-Host
        Write-Host "TACTICAL RAG SYSTEM - LIVE MONITOR" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to exit" -ForegroundColor Gray
        Write-Host ""
        
        Show-SystemResources
        
        Write-Host ""
        Write-Host "RECENT LOGS:" -ForegroundColor Cyan
        $recentLogs = docker logs rag-tactical-system --tail 5 2>$null
        if ($recentLogs) {
            foreach ($log in $recentLogs) {
                if ($log.Trim()) {
                    Write-Host "  $log" -ForegroundColor Gray
                }
            }
        }
        
        Write-Host ""
        Write-Host "Web Interface: http://localhost:7860" -ForegroundColor Cyan
        
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host ""
    Write-Host "Monitoring stopped. System still running." -ForegroundColor Yellow
    Write-Host 'To stop system: .\stop.ps1' -ForegroundColor Cyan
    Write-Host ""
}