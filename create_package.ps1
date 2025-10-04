# Create Complete Offline Deployment Package
# Run this AFTER your system is working and models are loaded

$PackageDir = ".\DEPLOYMENT_PACKAGE"
$Date = Get-Date -Format "yyyy-MM-dd_HHmm"

Write-Host "Creating deployment package..." -ForegroundColor Cyan
Write-Host "This will take 10-20 minutes due to large model files" -ForegroundColor Yellow
Write-Host ""

# Create package directory
New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

# Get actual image names
$ragImage = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String "rag-app"
$ragImageName = $ragImage -replace ":", "_"

Write-Host "[1/9] Saving RAG application image..." -ForegroundColor Yellow
docker save $ragImage -o "$PackageDir\rag-app-$Date.tar"

Write-Host "[2/9] Saving Ollama image..." -ForegroundColor Yellow
docker save ollama/ollama:latest -o "$PackageDir\ollama-$Date.tar"

# Get Ollama container ID
$ollamaContainer = docker-compose ps -q ollama-server 2>$null

Write-Host "[3/9] Exporting Ollama models (~8GB, this takes time)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$PackageDir\ollama_models" -Force | Out-Null

# Copy entire Ollama model directory from container
docker cp "${ollamaContainer}:/root/.ollama/models" "$PackageDir\ollama_models\"
Write-Host "  Model data exported" -ForegroundColor Green

Write-Host "[4/9] Copying source code..." -ForegroundColor Yellow
Copy-Item "_src" "$PackageDir\_src" -Recurse -Force

Write-Host "[5/9] Copying configuration files..." -ForegroundColor Yellow
Copy-Item "docker-compose.yml" "$PackageDir\"
Copy-Item "config.yml" "$PackageDir\" -ErrorAction SilentlyContinue
Copy-Item "_config" "$PackageDir\_config" -Recurse -Force

Write-Host "[6/9] Copying documents..." -ForegroundColor Yellow
Copy-Item "documents" "$PackageDir\documents" -Recurse -Force

Write-Host "[7/9] Copying vector database..." -ForegroundColor Yellow
Copy-Item "chroma_db" "$PackageDir\chroma_db" -Recurse -Force

Write-Host "[8/9] Creating deployment scripts..." -ForegroundColor Yellow

# Windows deployment script
$DeployScriptPS = @"
# FIELD DEPLOYMENT SCRIPT - Windows
# Requires: Docker Desktop with WSL2

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "    RAG SYSTEM OFFLINE DEPLOYMENT" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Load Docker images
Write-Host "[1/4] Loading Docker images (5-10 min)..." -ForegroundColor Yellow
docker load -i rag-app-$Date.tar
docker load -i ollama-$Date.tar

# Start Ollama first to create volume
Write-Host ""
Write-Host "[2/4] Starting Ollama and restoring models..." -ForegroundColor Yellow
docker-compose up -d ollama-server
Start-Sleep -Seconds 10

# Get Ollama container ID
`$ollamaContainer = docker-compose ps -q ollama-server

# Restore Ollama models
Write-Host "  Restoring model data (~8GB)..." -ForegroundColor Gray
docker cp "ollama_models\models" "`${ollamaContainer}:/root/.ollama/"
Write-Host "  Models restored" -ForegroundColor Green

# Start RAG application
Write-Host ""
Write-Host "[3/4] Starting RAG application..." -ForegroundColor Yellow
docker-compose up -d rag-tactical-system
Start-Sleep -Seconds 15

# Verify
Write-Host ""
Write-Host "[4/4] Verifying deployment..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "    DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access: http://localhost:7860" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  Logs:     docker-compose logs -f rag-tactical-system" -ForegroundColor White
Write-Host "  Stop:     docker-compose down" -ForegroundColor White
Write-Host "  Restart:  docker-compose restart" -ForegroundColor White
Write-Host ""
"@

$DeployScriptPS | Out-File -FilePath "$PackageDir\deploy.ps1" -Encoding UTF8

# Linux deployment script
$DeployScriptSH = @"
#!/bin/bash
# FIELD DEPLOYMENT SCRIPT - Linux

echo "======================================================"
echo "    RAG SYSTEM OFFLINE DEPLOYMENT"
echo "======================================================"
echo ""

# Load images
echo "[1/4] Loading Docker images (5-10 min)..."
docker load -i rag-app-$Date.tar
docker load -i ollama-$Date.tar

# Start Ollama
echo ""
echo "[2/4] Starting Ollama and restoring models..."
docker-compose up -d ollama-server
sleep 10

# Restore models
OLLAMA_CONTAINER=`$(docker-compose ps -q ollama-server)
echo "  Restoring model data (~8GB)..."
docker cp ollama_models/models `$OLLAMA_CONTAINER:/root/.ollama/
echo "  Models restored"

# Start RAG
echo ""
echo "[3/4] Starting RAG application..."
docker-compose up -d rag-tactical-system
sleep 15

# Verify
echo ""
echo "[4/4] Verifying deployment..."
docker-compose ps

echo ""
echo "======================================================"
echo "    DEPLOYMENT COMPLETE"
echo "======================================================"
echo ""
echo "Access: http://localhost:7860"
echo ""
"@

$DeployScriptSH | Out-File -FilePath "$PackageDir\deploy.sh" -Encoding ASCII

Write-Host "[9/9] Creating documentation..." -ForegroundColor Yellow

$Readme = @"
# RAG SYSTEM OFFLINE DEPLOYMENT PACKAGE
Created: $Date

## CRITICAL REQUIREMENTS
- Docker Desktop installed and running
- WSL2 enabled (Windows only)
- 16GB+ RAM
- 25GB+ free disk space
- NVIDIA GPU with drivers (optional, for speed)

## Contents
- rag-app-$Date.tar         RAG application image
- ollama-$Date.tar           Ollama server image
- ollama_models/             AI models (~8GB)
  - llama3.1:8b             
  - nomic-embed-text
- documents/                 Your documents
- chroma_db/                 Vector database
- _src/                      Application source
- _config/                   Dockerfiles
- docker-compose.yml         Service config

## DEPLOYMENT (Windows)
1. Copy entire DEPLOYMENT_PACKAGE folder to target
2. Open PowerShell as Administrator in this directory
3. Ensure Docker Desktop is running
4. Run: .\deploy.ps1
5. Wait 10-15 minutes
6. Open browser: http://localhost:7860

## DEPLOYMENT (Linux)
1. Copy entire folder to target
2. cd to this directory
3. chmod +x deploy.sh
4. ./deploy.sh
5. Open browser: http://localhost:7860

## Verification
Check models loaded:
docker exec -it ollama-server ollama list

Check GPU:
docker exec rag-tactical-system python -c "import torch; print(torch.cuda.is_available())"

## Troubleshooting
Problem: "Cannot connect to Docker"
Solution: Start Docker Desktop, wait 30 seconds, retry

Problem: "Models not found"
Solution: Check ollama_models/models folder exists with files

Problem: Web interface not loading
Solution: docker-compose logs rag-tactical-system

## NO INTERNET REQUIRED
This package is completely self-contained. All dependencies frozen.
Models pre-loaded. No downloads needed.
"@

$Readme | Out-File -FilePath "$PackageDir\README.md" -Encoding UTF8

# Calculate sizes
$totalSize = [math]::Round((Get-ChildItem $PackageDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB, 2)
$modelSize = [math]::Round((Get-ChildItem "$PackageDir\ollama_models" -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB, 2)

# Summary
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "    DEPLOYMENT PACKAGE CREATED" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $PackageDir" -ForegroundColor Cyan
Write-Host "Total size: ${totalSize}GB" -ForegroundColor Cyan
Write-Host "  - Models: ${modelSize}GB" -ForegroundColor Gray
Write-Host "  - Images: $([math]::Round(($totalSize - $modelSize), 2))GB" -ForegroundColor Gray
Write-Host ""
Write-Host "Package includes:" -ForegroundColor Yellow
Write-Host "  ✓ Docker images (2)" -ForegroundColor White
Write-Host "  ✓ AI models (llama3.1:8b + embeddings)" -ForegroundColor White
Write-Host "  ✓ Source code (_src)" -ForegroundColor White
Write-Host "  ✓ Documents ($((Get-ChildItem documents -File -Recurse).Count) files)" -ForegroundColor White
Write-Host "  ✓ Vector database" -ForegroundColor White
Write-Host "  ✓ All configurations" -ForegroundColor White
Write-Host ""
Write-Host "TO DEPLOY IN FIELD:" -ForegroundColor Yellow
Write-Host "  1. Copy entire '$PackageDir' folder" -ForegroundColor White
Write-Host "  2. Run deploy.ps1 (Windows) or deploy.sh (Linux)" -ForegroundColor White
Write-Host "  3. Access: http://localhost:7860" -ForegroundColor White
Write-Host ""
Write-Host "Total deployment time: ~15 minutes" -ForegroundColor Gray
Write-Host "=====================================================" -ForegroundColor Green