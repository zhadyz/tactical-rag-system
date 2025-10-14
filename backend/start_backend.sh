#!/bin/bash

# Tactical RAG Backend - Quick Start Script
# This script starts the backend API server locally (not in Docker)

set -e  # Exit on error

echo "========================================================================"
echo "  TACTICAL RAG BACKEND - QUICK START"
echo "========================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "Error: Must run from backend/ directory"
    echo "Usage: cd backend && bash start_backend.sh"
    exit 1
fi

# Check Python version
echo "1. Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "2. Creating virtual environment..."
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo ""
    echo "2. Using existing virtual environment"
fi

# Activate virtual environment
echo ""
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "   ✓ Virtual environment activated"

# Install dependencies
echo ""
echo "4. Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "   ✓ Dependencies installed"

# Check environment variables
echo ""
echo "5. Checking environment configuration..."

# Set defaults if not already set
export OLLAMA_HOST=${OLLAMA_HOST:-"http://localhost:11434"}
export RAG_VECTOR_DB_DIR=${RAG_VECTOR_DB_DIR:-"../chroma_db"}
export RAG_DOCUMENTS_DIR=${RAG_DOCUMENTS_DIR:-"../documents"}
export RAG_CACHE__USE_REDIS=${RAG_CACHE__USE_REDIS:-"true"}
export RAG_CACHE__REDIS_HOST=${RAG_CACHE__REDIS_HOST:-"localhost"}
export RAG_CACHE__REDIS_PORT=${RAG_CACHE__REDIS_PORT:-"6379"}

echo "   OLLAMA_HOST:          $OLLAMA_HOST"
echo "   RAG_VECTOR_DB_DIR:    $RAG_VECTOR_DB_DIR"
echo "   RAG_DOCUMENTS_DIR:    $RAG_DOCUMENTS_DIR"
echo "   RAG_CACHE__USE_REDIS: $RAG_CACHE__USE_REDIS"
echo "   RAG_CACHE__REDIS_HOST: $RAG_CACHE__REDIS_HOST"

# Check if Ollama is running
echo ""
echo "6. Checking Ollama connection..."
if curl -s "$OLLAMA_HOST/api/version" > /dev/null 2>&1; then
    echo "   ✓ Ollama is running at $OLLAMA_HOST"
else
    echo "   ✗ WARNING: Cannot connect to Ollama at $OLLAMA_HOST"
    echo "   Make sure Ollama is running: ollama serve"
fi

# Check if Redis is running
echo ""
echo "7. Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli -h "$RAG_CACHE__REDIS_HOST" -p "$RAG_CACHE__REDIS_PORT" ping > /dev/null 2>&1; then
        echo "   ✓ Redis is running at $RAG_CACHE__REDIS_HOST:$RAG_CACHE__REDIS_PORT"
    else
        echo "   ✗ WARNING: Cannot connect to Redis"
        echo "   Start Redis: redis-server"
    fi
else
    echo "   ⚠ redis-cli not found, skipping Redis check"
fi

# Check if vector database exists
echo ""
echo "8. Checking vector database..."
if [ -d "$RAG_VECTOR_DB_DIR" ] && [ "$(ls -A $RAG_VECTOR_DB_DIR)" ]; then
    echo "   ✓ Vector database found at $RAG_VECTOR_DB_DIR"
else
    echo "   ✗ ERROR: Vector database not found or empty"
    echo "   Please run indexing first: python _src/index_documents.py"
    exit 1
fi

# Start the server
echo ""
echo "========================================================================"
echo "  STARTING BACKEND SERVER"
echo "========================================================================"
echo ""
echo "Server will be available at:"
echo "  - API:     http://localhost:8000"
echo "  - Docs:    http://localhost:8000/docs"
echo "  - Health:  http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start uvicorn
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
