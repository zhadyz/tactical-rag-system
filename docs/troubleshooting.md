# Troubleshooting Guide

Common issues and solutions for Apollo deployment and operation.

## Services Won't Start

### Symptom

```bash
docker compose ps
# Shows "Restarting" or "Exited" state
```

### Solutions

**1. Check Logs**:
```bash
docker compose -f backend/docker-compose.atlas.yml logs apollo-backend
```

**2. Port Conflicts**:
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :6333
netstat -ano | findstr :6379

# Linux/macOS
lsof -i :8000
lsof -i :6333
lsof -i :6379
```

Kill conflicting processes or change ports in `docker-compose.atlas.yml`

**3. GPU Not Accessible**:
```bash
# Test GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

If fails, reinstall NVIDIA Container Toolkit:
```bash
# Linux
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**4. Disk Space**:
```bash
# Check available space (need 60GB+)
df -h

# Clean Docker images if needed
docker system prune -a
```

---

## GPU Not Detected

### Symptom

API reports `"gpu_available": false` or logs show:
```
GPU offload support: False
Using CPU for inference
```

### Solutions

**1. Verify NVIDIA Driver**:
```bash
nvidia-smi
```
Should show driver version 571.86+ for RTX 50 series, 551.23+ for RTX 40 series

**2. Check Docker GPU Access**:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**3. Verify CUDA Libraries in Container**:
```bash
docker exec apollo-backend bash -c 'echo $LD_LIBRARY_PATH'
```
Should include: `/usr/lib/wsl/drivers:/usr/local/cuda/lib64`

**4. Rebuild Image with CUDA Support**:
```bash
docker build --no-cache -f backend/Dockerfile.atlas -t apollo-backend:v4.1-cuda .
```

**5. Check docker-compose.yml GPU Config**:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu, compute, utility]
```

---

## CUDA Out of Memory

### Symptom

```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

### Solutions

**1. Reduce GPU Layers**:
```yaml
# backend/config.yml
llamacpp:
  n_gpu_layers: 25  # Reduce from 35
```

**2. Reduce Embedding Batch Size**:
```yaml
embedding:
  batch_size: 32  # Reduce from 64
```

**3. Close GPU Applications**:
```bash
nvidia-smi
# Kill unnecessary processes using GPU
```

**4. Reduce Context Window**:
```yaml
llamacpp:
  n_ctx: 4096  # Reduce from 8192
```

**5. Switch to Smaller Model**:
```yaml
llamacpp:
  model_path: "/models/llama-3.1-8b-instruct.Q5_K_M.gguf"  # Instead of Qwen 14B
```

---

## Slow Query Performance (>5s)

### Symptom

Queries consistently taking >5 seconds

### Solutions

**1. Check Cache Hit Rate**:
```bash
curl http://localhost:8000/api/cache/metrics
```
If <50%, investigate query variations

**2. Reduce Retrieval Candidates**:
```yaml
retrieval:
  initial_k: 50   # Reduce from 100
  rerank_k: 15    # Reduce from 30
  final_k: 5      # Reduce from 8
```

**3. Check GPU Utilization**:
```bash
nvidia-smi
```
Should be 50-90% during query. If low, increase `n_gpu_layers`

**4. Optimize Qdrant Index**:
```yaml
qdrant:
  hnsw_m: 8              # Reduce from 16
  hnsw_ef_construct: 64  # Reduce from 128
```

**5. Clear Cache and Restart**:
```bash
curl -X POST http://localhost:8000/api/cache/clear
docker restart apollo-backend
```

---

## Document Upload Fails

### Symptom

500 error when uploading documents

### Solutions

**1. Check File Size** (max 50MB):
```bash
ls -lh /path/to/document.pdf
```

**2. Verify Supported Formats**: PDF, DOCX, TXT only

**3. Check Disk Space**:
```bash
df -h
```

**4. Review Backend Logs**:
```bash
docker logs apollo-backend | grep -i error
```

**5. Test with Small File**:
```bash
echo "Test content" > test.txt
curl -X POST http://localhost:8000/api/documents/upload -F "file=@test.txt"
```

---

## Embedding Model Download Fails

### Symptom

```
Failed to download BAAI/bge-large-en-v1.5
ConnectionError: HTTPSConnectionPool
```

### Solutions

**1. Manual Download**:
```python
from transformers import AutoModel
AutoModel.from_pretrained('BAAI/bge-large-en-v1.5')
```

**2. Check HuggingFace Cache**:
```bash
ls -lh ~/.cache/huggingface/hub/
```

**3. Set Proxy** (if behind corporate firewall):
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

**4. Increase Timeout** in `backend/config.yml`:
```yaml
embedding:
  download_timeout: 600  # 10 minutes
```

---

## Rate Limit Exceeded

### Symptom

HTTP 429 "Too Many Requests"

### Solutions

**1. Wait 60 Seconds** (rate limit window resets)

**2. Increase Limit** (`backend/app/api/query.py`):
```python
RATE_LIMIT_REQUESTS = 60  # Increase from 30
RATE_LIMIT_WINDOW = 60    # Time window in seconds
```

**3. Use Caching** to reduce API calls:
- Send similar queries to benefit from cache
- Check cache metrics: `curl http://localhost:8000/api/cache/metrics`

---

## Connection Refused

### Symptom

```bash
curl: (7) Failed to connect to localhost port 8000
```

### Solutions

**1. Check Service Status**:
```bash
docker compose -f backend/docker-compose.atlas.yml ps
```

**2. Verify Port Binding**:
```bash
docker port apollo-backend
```

**3. Check Firewall**:
```bash
# Linux
sudo ufw status

# Windows
netsh advfirewall firewall show rule name=all | findstr 8000
```

**4. Restart Services**:
```bash
docker compose -f backend/docker-compose.atlas.yml restart
```

---

## High Memory Usage

### Symptom

System running out of RAM (>90% usage)

### Solutions

**1. Check Redis Memory**:
```bash
docker exec apollo-redis redis-cli INFO memory
```

**2. Check Qdrant Memory**:
```bash
docker stats apollo-qdrant
```

**3. Reduce Cache Size**:
```yaml
cache:
  max_cache_size: 5000  # Reduce from 10000
```

**4. Enable Redis Eviction**:
```yaml
# docker-compose.atlas.yml
apollo-redis:
  command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru
```

**5. Restart Services**:
```bash
docker compose -f backend/docker-compose.atlas.yml restart
```

---

## Qdrant Connection Errors

### Symptom

```
Failed to connect to Qdrant: Connection refused
```

### Solutions

**1. Check Qdrant Status**:
```bash
docker logs apollo-qdrant
curl http://localhost:6333/health
```

**2. Verify Network**:
```bash
docker network inspect apollo_default
```

**3. Restart Qdrant**:
```bash
docker restart apollo-qdrant
```

**4. Check Storage Permissions** (Linux):
```bash
sudo chown -R 1000:1000 data/qdrant
chmod -R 755 data/qdrant
```

---

## Model Loading Errors

### Symptom

```
Error loading model: File not found
```

### Solutions

**1. Verify Model File**:
```bash
ls -lh ./models/
```

**2. Check File Integrity**:
```bash
# Compare file size with expected
du -sh ./models/llama-3.1-8b-instruct.Q5_K_M.gguf
# Expected: 5.4GB
```

**3. Verify Path in Config**:
```yaml
llamacpp:
  model_path: "/models/llama-3.1-8b-instruct.Q5_K_M.gguf"
  # Path must start with /models/ (Docker volume mount)
```

**4. Re-download Model**:
```bash
rm ./models/llama-3.1-8b-instruct.Q5_K_M.gguf
wget -P ./models https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q5_K_M.gguf
```

---

## Desktop App Won't Launch

### Symptom

Double-click `launch-desktop.bat` - nothing happens

### Solutions

**1. Check Backend is Running**:
```bash
curl http://localhost:8000/api/health
```

**2. Run from Terminal**:
```bash
cd /path/to/apollo
npm run tauri:dev
```

**3. Check Dependencies**:
```bash
npm install
```

**4. View Logs**:
Check console output for errors

**5. Rebuild Desktop App**:
```bash
npm run tauri:build
```

---

## Getting Help

### Collect Diagnostic Information

```bash
# System info
uname -a  # Linux
systeminfo  # Windows

# Docker version
docker --version
docker compose version

# NVIDIA info
nvidia-smi

# Service status
docker compose -f backend/docker-compose.atlas.yml ps

# Logs
docker compose -f backend/docker-compose.atlas.yml logs --tail 100

# Config
cat backend/config.yml

# API health
curl http://localhost:8000/api/health
```

### Support Channels

- **GitHub Issues**: [Report bugs](https://github.com/yourusername/apollo/issues)
- **Discussions**: [Ask questions](https://github.com/yourusername/apollo/discussions)
- **Documentation**: [apollo.onyxlab.ai](https://apollo.onyxlab.ai)

---

[← Back to Deployment](deployment.md) | [Back to Home](index.md)
