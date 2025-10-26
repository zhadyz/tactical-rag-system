# Getting Started with Apollo

This guide will help you install and run Apollo in under 10 minutes.

## Prerequisites

### Hardware Requirements

**Minimum** (Development):
- GPU: NVIDIA RTX 3060 (12GB VRAM)
- RAM: 32GB DDR4
- Storage: 100GB SSD

**Recommended** (Production):
- GPU: NVIDIA RTX 4080/5080 (16GB+ VRAM)
- CPU: AMD Ryzen 9800X3D or Intel i9-14900K
- RAM: 64GB+ DDR5
- Storage: 500GB+ NVMe SSD

### Software Requirements

1. **Docker Desktop** 24.0+ with Docker Compose V2
2. **NVIDIA Driver** 571.86+ (RTX 50 series) or 551.23+ (RTX 40 series)
3. **NVIDIA Container Toolkit** 1.14.0+
4. **Node.js** 18+ (for desktop app development)
5. **Windows 11 Pro** or **Ubuntu 22.04 LTS**

## Installation Steps

### Step 1: Install Prerequisites

#### Windows

```powershell
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/

# Install NVIDIA Driver
# Download from: https://www.nvidia.com/Download/index.aspx

# Verify installations
docker --version
nvidia-smi
```

#### Linux (Ubuntu 22.04)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Step 2: Clone Repository

```bash
git clone https://github.com/yourusername/apollo.git
cd apollo
```

### Step 3: Create Directories

```bash
# Windows (PowerShell)
New-Item -ItemType Directory -Path data\qdrant,data\redis,documents,models,logs

# Linux/macOS
mkdir -p data/{qdrant,redis} documents models logs
chmod -R 755 data documents logs models
```

### Step 4: Download LLM Model

**Llama 3.1 8B Instruct** (5.4GB - Recommended for most use cases):

```bash
# Linux/macOS
wget -P ./models https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q5_K_M.gguf

# Windows (PowerShell)
Invoke-WebRequest `
  -Uri "https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q5_K_M.gguf" `
  -OutFile ".\models\llama-3.1-8b-instruct.Q5_K_M.gguf"

# Verify download
ls -lh ./models/
# Expected: llama-3.1-8b-instruct.Q5_K_M.gguf (5.4GB)
```

**Optional: Qwen 2.5 14B Instruct** (8.9GB - Higher quality, requires 12GB+ VRAM):

```bash
wget -P ./models https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q5_k_m.gguf
```

### Step 5: Build Backend Image

```bash
docker build -f backend/Dockerfile.atlas -t apollo-backend:v4.1-cuda .
```

**Expected**: ~8 minutes build time, ~9GB image size

### Step 6: Start Services

```bash
# Linux/macOS
docker compose -f backend/docker-compose.atlas.yml up -d

# Windows
docker compose -f backend/docker-compose.atlas.yml up -d

# Monitor startup logs
docker compose -f backend/docker-compose.atlas.yml logs -f
```

Wait for health checks (2-3 minutes)

### Step 7: Verify Deployment

```bash
# Check service health
docker compose -f backend/docker-compose.atlas.yml ps

# Expected output:
# NAME               STATUS          PORTS
# apollo-backend     Up (healthy)    0.0.0.0:8000->8000/tcp
# apollo-qdrant      Up (healthy)    0.0.0.0:6333-6334->6333-6334/tcp
# apollo-redis       Up (healthy)    0.0.0.0:6379->6379/tcp

# Test API health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","version":"4.1.0","gpu_available":true,"models_loaded":true}

# Test GPU acceleration
docker run --gpus all --rm apollo-backend:v4.1-cuda python3 -c \
  "import llama_cpp; print(f'GPU support: {llama_cpp.llama_cpp.llama_supports_gpu_offload()}')"

# Expected: GPU support: True
```

## Running the Desktop Application

### Development Mode

```bash
# Install dependencies
npm install

# Start desktop app in dev mode
npm run tauri:dev
```

### Production Build

```bash
# Windows
.\launch-desktop.bat

# Linux/macOS
npm run tauri:build
./src-tauri/target/release/apollo
```

## First Query

### Using the API

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the capital of France?",
    "mode": "simple",
    "use_context": true
  }'
```

**Expected Response Time**: <2 seconds

### Using the Desktop App

1. Launch the Apollo desktop application
2. Type your question in the chat interface
3. Select **Simple** mode (recommended for most queries)
4. Click **Send** or press Enter
5. View the answer with source citations

## Uploading Documents

### Via API

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@./path/to/document.pdf"
```

### Via Desktop App

1. Click the **Documents** tab
2. Drag and drop PDF, DOCX, or TXT files
3. Wait for processing confirmation
4. Documents are automatically indexed

## Next Steps

- **[Configuration Guide](configuration.md)** - Optimize settings for your hardware
- **[Model Management](model-management.md)** - Learn about hotswapping LLMs
- **[API Reference](api-reference.md)** - Explore all available endpoints
- **[Performance Tuning](performance.md)** - Maximize query speed and quality

## Common Issues

### Services Won't Start

```bash
# Check logs
docker compose -f backend/docker-compose.atlas.yml logs apollo-backend

# Check for port conflicts
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/macOS
```

### GPU Not Detected

```bash
# Verify NVIDIA driver
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

For more troubleshooting, see the **[Troubleshooting Guide](troubleshooting.md)**.

---

[← Back to Home](index.md) | [Next: Architecture →](architecture.md)
