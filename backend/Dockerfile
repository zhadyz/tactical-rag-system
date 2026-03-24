# FORGE - Production-Optimized Multi-Stage Dockerfile
# Target: <30 second startup time
# Strategy: Pre-cache models, optimize layer caching, async initialization
#
# Build time: ~10 minutes (one-time cost)
# Startup time: ~20-30 seconds (vs 78s baseline)
# Image size: ~9GB (includes pre-cached models)

# ============================================================
# STAGE 1: Base Dependencies
# ============================================================
FROM python:3.11-slim-bookworm AS base

# Install system dependencies + CUDA Toolkit for GPU-accelerated llama.cpp
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc-12 \
    g++-12 \
    cmake \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    curl \
    wget \
    gnupg2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set gcc-12/g++-12 as default compilers (CUDA 12.1 requires gcc <= 12)
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 100 \
    && update-alternatives --install /usr/bin/cc cc /usr/bin/gcc-12 100 \
    && update-alternatives --install /usr/bin/c++ c++ /usr/bin/g++-12 100

# Add NVIDIA CUDA repository and install minimal CUDA components
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/cuda-keyring_1.1-1_all.deb \
    && dpkg -i cuda-keyring_1.1-1_all.deb \
    && rm cuda-keyring_1.1-1_all.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        cuda-nvcc-12-1 \
        cuda-cudart-dev-12-1 \
        libcublas-dev-12-1 \
    && rm -rf /var/lib/apt/lists/*

# Configure CUDA stubs for Docker build linking
RUN ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1 \
    && echo "/usr/local/cuda/lib64/stubs" > /etc/ld.so.conf.d/cuda-stubs.conf \
    && ldconfig

# Verify CUDA installation
RUN echo "=== CUDA Installation Verification ===" && \
    ls -la /usr/local/cuda && \
    /usr/local/cuda/bin/nvcc --version

ENV CUDA_HOME=/usr/local/cuda
ENV PATH=/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/lib/wsl/drivers:/usr/lib/x86_64-linux-gnu:/usr/local/cuda/lib64:${LD_LIBRARY_PATH}

# ============================================================
# STAGE 2: Python Dependencies (HEAVY CACHING)
# ============================================================
FROM base AS python-deps

WORKDIR /build

# Install PyTorch FIRST (largest dependency, rarely changes)
RUN pip install --no-cache-dir \
    torch==2.5.1 \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Copy requirements BEFORE code (Docker layer cache)
COPY backend/requirements.txt /build/requirements.txt

# Build llama-cpp-python from source with CUDA support
ENV CMAKE_ARGS="-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=all-major -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc -DCUDAToolkit_ROOT=/usr/local/cuda"
ENV FORCE_CMAKE=1
RUN pip install --no-cache-dir llama-cpp-python==0.3.2 --no-binary llama-cpp-python

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# STAGE 3: Model Pre-Caching (CRITICAL FOR STARTUP SPEED)
# ============================================================
FROM python-deps AS model-cache

WORKDIR /app

ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface

# Pre-download BGE-M3 embedding model (replaces BGE-large-en-v1.5)
RUN python3 -c "\
from FlagEmbedding import BGEM3FlagModel; \
print('Downloading BGE-M3 model...'); \
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=False); \
print('BGE-M3 model cached successfully')"

# Pre-download cross-encoder reranker for CRAG
RUN python3 -c "\
from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
print('Downloading reranker model...'); \
tokenizer = AutoTokenizer.from_pretrained('cross-encoder/ms-marco-MiniLM-L-12-v2'); \
model = AutoModelForSequenceClassification.from_pretrained('cross-encoder/ms-marco-MiniLM-L-12-v2'); \
print('Reranker model cached successfully')"

# ============================================================
# STAGE 4: Application Code
# ============================================================
FROM model-cache AS app

WORKDIR /app

# Copy application code (new forge package replaces app/ + _src/)
COPY backend/forge /app/forge
COPY backend/config.yml /app/config.yml

# Create necessary directories
RUN mkdir -p /app/documents /app/logs /app/.cache /app/data /models

# Embed llama.cpp models directly (bypasses Windows Docker volume mount issues)
COPY models/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf /models/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf
COPY models/Llama-3.2-1B-Instruct.Q4_K_M.gguf /models/Llama-3.2-1B-Instruct.Q4_K_M.gguf

# ============================================================
# STAGE 5: Runtime Configuration
# ============================================================
FROM app AS runtime

WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH

# Forge configuration defaults (override in docker-compose)
ENV OLLAMA_HOST=http://ollama:11434
ENV RAG_DOCUMENTS_DIR=/app/documents
ENV RAG_CACHE__USE_REDIS=true
ENV RAG_CACHE__REDIS_HOST=redis
ENV RAG_CACHE__REDIS_PORT=6379

# Pre-compile Python bytecode
RUN python3 -m compileall /app/forge

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

# Uvicorn ASGI server (single process — GPU models can't be shared)
CMD ["uvicorn", "forge.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--timeout-keep-alive", "5"]

# BUILD INSTRUCTIONS:
# ===================
# Build: docker build -f backend/Dockerfile -t forge-backend:v5.0 .
# Run:   docker-compose -f backend/docker-compose.yml up -d
