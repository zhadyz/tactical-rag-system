# Tactical RAG FastAPI Backend - Dockerfile
# This builds a containerized backend that wraps the existing RAG engine

# ============================================================
# STAGE 1: Base Python image
# ============================================================
FROM python:3.11-slim

# ============================================================
# STEP 2: Set metadata
# ============================================================
LABEL maintainer="Abdul.baril@us.af.mil"
LABEL description="Tactical RAG FastAPI Backend"
LABEL version="1.0.0"

# ============================================================
# STEP 3: Install system dependencies
# ============================================================
# Required for document processing (OCR, PDF parsing)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# STEP 4: Set working directory
# ============================================================
WORKDIR /app

# ============================================================
# STEP 5: Install PyTorch with CUDA 12.1 (OPTIONAL)
# ============================================================
# If you want GPU support in the backend, uncomment this:
# RUN pip install --no-cache-dir \
#     torch==2.5.1+cu121 \
#     torchvision==0.20.1+cu121 \
#     torchaudio==2.5.1+cu121 \
#     --index-url https://download.pytorch.org/whl/cu121

# For CPU-only (faster build, smaller image):
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# ============================================================
# STEP 6: Copy and install Python dependencies
# ============================================================
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# STEP 7: Copy application code
# ============================================================
# Copy the FastAPI backend
COPY backend/app /app/app

# CRITICAL: Copy the _src directory (existing RAG code)
# The RAG engine imports from here
COPY _src /app/_src

# ============================================================
# STEP 8: Create necessary directories
# ============================================================
RUN mkdir -p /app/documents /app/chroma_db /app/logs /app/.cache

# ============================================================
# STEP 9: Expose the port
# ============================================================
EXPOSE 8000

# ============================================================
# STEP 10: Set environment variables
# ============================================================
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH

# RAG configuration (override these in docker-compose or at runtime)
ENV OLLAMA_HOST=http://ollama:11434
ENV RAG_DOCUMENTS_DIR=/app/documents
ENV RAG_VECTOR_DB_DIR=/app/chroma_db
ENV RAG_CACHE__USE_REDIS=true
ENV RAG_CACHE__REDIS_HOST=redis
ENV RAG_CACHE__REDIS_PORT=6379

# Optional: GPU support
# ENV CUDA_VISIBLE_DEVICES=0
# ENV DEVICE_TYPE=cuda

# ============================================================
# STEP 11: Health check
# ============================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# ============================================================
# STEP 12: Start command
# ============================================================
# Run uvicorn with the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
