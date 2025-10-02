#!/bin/bash
# Enhanced Startup Script with Detailed Logging

set -e  # Exit on error

# Color codes for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "============================================================"
echo "    TACTICAL RAG SYSTEM - CONTAINER STARTUP"
echo "============================================================"
echo ""

# Create required directories
log_info "Creating required directories..."
mkdir -p /app/logs /app/.cache /app/documents /app/chroma_db
log_success "Directories created"

# Wait for Ollama
echo ""
log_info "Waiting for Ollama server..."
RETRY_COUNT=0
MAX_RETRIES=60

until curl -sf http://ollama:11434/api/tags > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        log_error "Ollama server failed to start after ${MAX_RETRIES} attempts (${RETRY_COUNT}s timeout)"
        log_warning "Attempting to continue anyway..."
        break
    fi
    
    # Only log every 5 attempts to reduce spam
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        log_info "Still waiting for Ollama... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    fi
    sleep 2
done

if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
    log_success "Ollama server is ready! (took ${RETRY_COUNT} attempts, ~$((RETRY_COUNT * 2))s)"
fi

# Check Ollama models
echo ""
log_info "Checking Ollama models..."

MODEL_COUNT=$(curl -s http://ollama:11434/api/tags | grep -c "name" || echo "0")
log_info "Found $MODEL_COUNT models installed"

if ! curl -s http://ollama:11434/api/tags | grep -q "llama3.1:8b"; then
    log_warning "llama3.1:8b not found - pulling model (this will take 5-10 minutes)..."
    curl -X POST http://ollama:11434/api/pull -d '{"name": "llama3.1:8b"}' 2>&1 | grep -i "success\|error\|pulling" || true
    log_success "llama3.1:8b model pulled"
else
    log_success "llama3.1:8b model already installed"
fi

if ! curl -s http://ollama:11434/api/tags | grep -q "nomic-embed-text"; then
    log_warning "nomic-embed-text not found - pulling model..."
    curl -X POST http://ollama:11434/api/pull -d '{"name": "nomic-embed-text"}' 2>&1 | grep -i "success\|error\|pulling" || true
    log_success "nomic-embed-text model pulled"
else
    log_success "nomic-embed-text model already installed"
fi

# Check documents and indexing
echo ""
log_info "Checking document index..."

# Count documents
DOC_COUNT=$(find /app/documents -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.docx" -o -name "*.md" \) 2>/dev/null | wc -l)
log_info "Found $DOC_COUNT documents in /app/documents"

if [ ! -d "/app/chroma_db" ] || [ -z "$(ls -A /app/chroma_db 2>/dev/null)" ]; then
    log_warning "No vector database found"
    
    if [ "$DOC_COUNT" -gt 0 ]; then
        log_info "Starting document indexing for $DOC_COUNT documents..."
        log_info "This may take 2-10 minutes depending on document size..."
        
        # Run indexing with error capture
        if python index_documents.py 2>&1; then
            log_success "Indexing completed successfully!"
            
            # Verify index was created
            CHUNK_COUNT=$(ls -1 /app/chroma_db 2>/dev/null | wc -l)
            log_info "Vector database created with $CHUNK_COUNT files"
        else
            log_error "Indexing failed! Check logs above for details"
            log_error "The app will start but queries will fail"
            log_warning "To fix: Add documents to /app/documents and restart container"
        fi
    else
        log_warning "No documents found in /app/documents"
        log_warning "The app will start but cannot answer questions"
        log_info "To add documents: Copy files to /app/documents and restart"
    fi
else
    # Index exists - show details
    CHUNK_COUNT=$(ls -1 /app/chroma_db 2>/dev/null | wc -l)
    log_success "Vector database exists ($CHUNK_COUNT files)"
    
    # Check if it's stale
    DB_AGE=$(find /app/chroma_db -type f -name "chroma.sqlite3" -mmin +1440 2>/dev/null | wc -l)
    if [ "$DB_AGE" -gt 0 ]; then
        log_warning "Database is >24 hours old - consider re-indexing if documents changed"
    fi
fi

# Final system check
echo ""
log_info "Performing final system checks..."

# Check GPU
if nvidia-smi >/dev/null 2>&1; then
    GPU_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
    log_success "GPU detected - ${GPU_MEM}MB VRAM in use"
else
    log_warning "No GPU detected - running on CPU (queries will be slower)"
fi

# Check disk space
DISK_USAGE=$(df -h /app | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log_warning "Disk usage is high: ${DISK_USAGE}% - consider cleaning up"
fi

# Start application
echo ""
echo "============================================================"
echo "🚀 STARTING RAG APPLICATION"
echo "============================================================"
log_info "System configuration:"
log_info "  - Documents: $DOC_COUNT files"
log_info "  - Database: $([ -d "/app/chroma_db" ] && echo "Ready" || echo "Missing")"
log_info "  - Models: llama3.1:8b + nomic-embed-text"
log_info "  - Web interface will be at: http://localhost:7860"
echo ""
log_info "Starting Python application..."

# Start with exec to ensure proper signal handling
exec python app.py