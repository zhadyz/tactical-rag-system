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

# Create directories
log_info "Creating required directories..."
mkdir -p /app/documents /app/chroma_db /app/logs /app/.cache
log_success "Directories created"

# Wait for Ollama
log_info "Waiting for Ollama server..."
max_attempts=30
attempt=0
while ! curl -sf http://ollama:11434/api/tags > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        log_error "Ollama server failed to start after ${max_attempts} attempts"
        exit 1
    fi
    sleep 1
done
log_success "Ollama server is ready! (took $attempt attempts, ~${attempt}s)"

# Check models
log_info "Checking Ollama models..."
models=$(curl -sf http://ollama:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")
model_count=$(echo "$models" | grep -c . || echo 0)
log_info "Found $model_count models installed"

# Pull required models
for model in "llama3.1:8b" "nomic-embed-text"; do
    if echo "$models" | grep -q "^${model}$"; then
        log_success "$model model already installed"
    else
        log_info "Pulling $model model..."
        if curl -sf -X POST http://ollama:11434/api/pull -d "{\"name\":\"$model\"}" > /dev/null 2>&1; then
            log_success "$model model pulled"
        else
            log_error "Failed to pull $model"
            exit 1
        fi
    fi
done

# Check documents
log_info "Checking document index..."
doc_count=$(find /app/documents -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.docx" -o -name "*.doc" -o -name "*.md" \) 2>/dev/null | wc -l)
log_info "Found $doc_count documents in /app/documents"

# Check vector DB
if [ -d "/app/chroma_db" ] && [ "$(ls -A /app/chroma_db 2>/dev/null)" ]; then
    file_count=$(find /app/chroma_db -type f | wc -l)
    log_success "Vector database exists ($file_count files)"
else
    log_warning "No vector database found - will create on startup"
fi

# GPU verification
echo "============================================================"
echo "    CUDA/GPU VERIFICATION"
echo "============================================================"
log_info "Checking CUDA/GPU configuration..."

python3 << 'PYTHON_EOF'
import sys
try:
    import torch
    if torch.cuda.is_available():
        print(f"\033[0;32m[SUCCESS]\033[0m GPU detected - {torch.cuda.get_device_name(0)}")
        print(f"\033[0;34m[INFO]\033[0m PyTorch Version: {torch.__version__}")
        print(f"\033[0;34m[INFO]\033[0m CUDA Version: {torch.version.cuda}")
        print(f"\033[0;34m[INFO]\033[0m Total VRAM: {torch.cuda.get_device_properties(0).total_memory // 1024**2}MB")
        
        # Test sentence-transformers
        print(f"\033[0;34m[INFO]\033[0m Testing sentence-transformers GPU support...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda' if torch.cuda.is_available() else 'cpu')
        if 'cuda' in str(model.device):
            print(f"\033[0;32m[SUCCESS]\033[0m Sentence-transformers using GPU ({model.device})")
        else:
            print(f"\033[0;33m[WARNING]\033[0m Sentence-transformers on CPU")
            
        # Test CrossEncoder
        print(f"\033[0;34m[INFO]\033[0m Testing CrossEncoder GPU support...")
        from sentence_transformers import CrossEncoder
        reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cuda' if torch.cuda.is_available() else 'cpu')
        if 'cuda' in str(reranker.model.device):
            print(f"\033[0;32m[SUCCESS]\033[0m CrossEncoder using GPU ({reranker.model.device})")
        else:
            print(f"\033[0;33m[WARNING]\033[0m CrossEncoder on CPU")
    else:
        print(f"\033[0;33m[WARNING]\033[0m No GPU detected - running on CPU (queries will be slower)")
        print(f"\033[0;34m[INFO]\033[0m Check: docker run --gpus all to enable GPU in container")
except Exception as e:
    print(f"\033[0;31m[ERROR]\033[0m GPU check failed: {e}")
    sys.exit(1)
PYTHON_EOF

# Final checks
log_info "Performing final system checks..."
log_info "System configuration:"
log_info "  - Documents: $doc_count files"
log_info "  - Database: $([ -d /app/chroma_db ] && echo "Ready" || echo "Will be created")"
log_info "  - Models: llama3.1:8b + nomic-embed-text"
log_info "  - Web interface will be at: http://localhost:7860"

echo "============================================================"
echo "🚀 STARTING RAG APPLICATION"
echo "============================================================"
log_info "Starting Python application..."

# Start the application
cd /app
exec python app.py