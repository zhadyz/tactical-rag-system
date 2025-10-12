$startupScript = @'
#!/bin/bash
set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "============================================================"
echo "    TACTICAL RAG SYSTEM - CONTAINER STARTUP"
echo "============================================================"

mkdir -p /app/documents /app/chroma_db /app/logs /app/.cache
log_success "Directories created"

log_info "Waiting for Ollama server..."
max_attempts=30
attempt=0
while ! curl -sf http://ollama:11434/api/tags > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        log_error "Ollama server failed to start"
        exit 1
    fi
    sleep 1
done
log_success "Ollama ready"

models=$(curl -sf http://ollama:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

for model in "llama3.1:8b-instruct-q4_K_M" "nomic-embed-text"; do
    if echo "$models" | grep -q "^${model}$"; then
        log_success "$model already installed"
    else
        log_info "Pulling $model..."
        curl -sf -X POST http://ollama:11434/api/pull -d "{\"name\":\"$model\"}" > /dev/null 2>&1
        log_success "$model pulled"
    fi
done

cd /app
exec python app.py
'@

$bytes = [System.Text.Encoding]::UTF8.GetBytes($startupScript)
$cleanBytes = $bytes | Where-Object { $_ -ne 0x0D }
[System.IO.File]::WriteAllBytes("$PWD\_config\startup.sh", $cleanBytes)

docker-compose down
docker-compose build --no-cache rag-app
docker-compose up -d