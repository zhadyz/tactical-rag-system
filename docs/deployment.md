# Production Deployment

Guide for deploying Apollo in production environments.

## Docker Deployment (Recommended)

### Prerequisites

- Docker Desktop 24.0+ with Docker Compose V2
- NVIDIA Driver 571.86+ (RTX 50 series) or 551.23+ (RTX 40 series)
- NVIDIA Container Toolkit 1.14.0+
- 100GB+ available disk space

### Production Stack

The `backend/docker-compose.atlas.yml` file defines the complete production stack:

```yaml
services:
  apollo-backend:
    image: apollo-backend:v4.1-cuda
    container_name: apollo-backend
    ports:
      - "8000:8000"
    volumes:
      - ./documents:/app/documents
      - ./models:/models
      - ./logs:/app/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu, compute, utility]
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - LD_LIBRARY_PATH=/usr/lib/wsl/drivers:/usr/local/cuda/lib64
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  apollo-qdrant:
    image: qdrant/qdrant:v1.8.0
    container_name: apollo-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage
    restart: unless-stopped

  apollo-redis:
    image: redis:7.2-alpine
    container_name: apollo-redis
    command: redis-server --maxmemory 8gb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    restart: unless-stopped
```

### Deployment Steps

1. **Build Production Image**:
   ```bash
   docker build -f backend/Dockerfile.atlas -t apollo-backend:v4.1-cuda .
   ```

2. **Start Services**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml up -d
   ```

3. **Verify Health**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml ps
   curl http://localhost:8000/api/health
   ```

4. **Monitor Logs**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml logs -f
   ```

---

## Security Hardening

### 1. Network Security

**Firewall Configuration** (Linux):
```bash
# Allow API port
sudo ufw allow 8000/tcp comment 'Apollo API'

# Block internal services
sudo ufw deny 6379/tcp comment 'Redis - Internal Only'
sudo ufw deny 6333/tcp comment 'Qdrant - Internal Only'
sudo ufw deny 6334/tcp comment 'Qdrant gRPC - Internal Only'

# Enable firewall
sudo ufw enable
```

**Docker Network Isolation**:
```yaml
services:
  apollo-backend:
    networks:
      - backend
      - frontend

  apollo-qdrant:
    networks:
      - backend  # Not exposed to frontend

  apollo-redis:
    networks:
      - backend  # Not exposed to frontend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### 2. API Authentication

**Enable API Key** (Recommended for production):

1. **Generate API Key**:
   ```bash
   openssl rand -hex 32
   ```

2. **Set Environment Variable**:
   ```bash
   echo "API_KEY=your-generated-key-here" >> backend/.env
   ```

3. **Configure Backend** (already implemented in code)

4. **Use with Requests**:
   ```bash
   curl -H "X-API-Key: your-generated-key-here" \
     http://localhost:8000/api/health
   ```

### 3. HTTPS with Nginx

**Nginx Reverse Proxy**:

```nginx
# /etc/nginx/sites-available/apollo
upstream apollo {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name apollo.yourdomain.com;

    ssl_certificate /etc/ssl/certs/apollo.crt;
    ssl_certificate_key /etc/ssl/private/apollo.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://apollo;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long queries
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Streaming endpoint
    location /api/query/stream {
        proxy_pass http://apollo;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
}
```

---

## Backup & Recovery

### Automated Backup Script

**`scripts/backup.sh`**:
```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting Apollo backup..."

# Backup Qdrant vector database
echo "Backing up Qdrant..."
docker exec apollo-qdrant \
  sh -c "cd /qdrant && tar czf - storage" > "$BACKUP_DIR/qdrant.tar.gz"

# Backup Redis cache (optional - can be regenerated)
echo "Backing up Redis..."
docker exec apollo-redis redis-cli SAVE
cp data/redis/dump.rdb "$BACKUP_DIR/" 2>/dev/null || echo "Redis backup skipped"

# Backup configuration
echo "Backing up config..."
cp backend/config.yml "$BACKUP_DIR/"
cp docker-compose.atlas.yml "$BACKUP_DIR/"

# Backup documents
echo "Backing up documents..."
tar czf "$BACKUP_DIR/documents.tar.gz" ./documents/

# Backup models (optional - large files)
# tar czf "$BACKUP_DIR/models.tar.gz" ./models/

echo "Backup complete: $BACKUP_DIR"
echo "Total size: $(du -sh $BACKUP_DIR | cut -f1)"
```

**Make executable**:
```bash
chmod +x scripts/backup.sh
```

### Automated Backups (Cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/apollo/scripts/backup.sh >> /var/log/apollo-backup.log 2>&1

# Cleanup old backups (keep last 30 days)
0 3 * * * find /path/to/apollo/backups -type d -mtime +30 -exec rm -rf {} +
```

### Recovery Procedure

1. **Stop services**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml down
   ```

2. **Restore Qdrant**:
   ```bash
   tar xzf backups/20251026_020000/qdrant.tar.gz -C ./data/qdrant/
   ```

3. **Restore Redis** (optional):
   ```bash
   cp backups/20251026_020000/dump.rdb ./data/redis/
   ```

4. **Restore config**:
   ```bash
   cp backups/20251026_020000/config.yml backend/
   ```

5. **Restart services**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml up -d
   ```

---

## Monitoring

### Health Checks

**Docker Compose Health**:
```bash
docker compose -f backend/docker-compose.atlas.yml ps
```

**API Health**:
```bash
curl http://localhost:8000/api/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "4.1.0",
  "gpu_available": true,
  "models_loaded": true,
  "cache_connected": true,
  "vector_db_connected": true
}
```

### Resource Monitoring

**GPU Usage**:
```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu \
  --format=csv -l 5
```

**Container Stats**:
```bash
docker stats apollo-backend apollo-qdrant apollo-redis
```

### Log Management

**View Logs**:
```bash
# All services
docker compose -f backend/docker-compose.atlas.yml logs -f

# Specific service
docker logs -f apollo-backend

# Last 100 lines
docker logs --tail 100 apollo-backend

# Filter errors
docker logs apollo-backend 2>&1 | grep -i error
```

**Log Rotation** (Linux):

`/etc/logrotate.d/apollo`:
```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

---

## Scaling

### Vertical Scaling

**Upgrade Resources**:

1. **More VRAM**: Larger models or more GPU layers
2. **More RAM**: Larger vector database
3. **Faster GPU**: Higher tok/s inference

**Config Adjustments**:
```yaml
# Utilize more resources
llamacpp:
  n_gpu_layers: 50  # Increase if VRAM available

performance:
  max_workers: 32  # Increase with more CPU cores

cache:
  max_cache_size: 50000  # Increase with more RAM
```

### Horizontal Scaling (Future)

**Load Balancer** + Multiple Backend Instances:

```
                  ┌─> Apollo Backend 1 (GPU 1)
Load Balancer ────┼─> Apollo Backend 2 (GPU 2)
                  └─> Apollo Backend 3 (GPU 3)
                        │
                  Shared Qdrant + Redis
```

---

## Environment Variables

**Production `.env`**:
```bash
# Environment
APOLLO_ENV=production

# API Security
API_KEY=your-secure-key-here

# Logging
LOG_LEVEL=INFO

# GPU
CUDA_VISIBLE_DEVICES=0

# Ports (if changed from defaults)
API_PORT=8000
QDRANT_PORT=6333
REDIS_PORT=6379
```

---

## Updating Apollo

### Update to New Version

1. **Pull latest code**:
   ```bash
   git pull origin main
   ```

2. **Rebuild image**:
   ```bash
   docker build -f backend/Dockerfile.atlas -t apollo-backend:v4.2-cuda .
   ```

3. **Update docker-compose.yml** with new image tag

4. **Restart services**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml up -d
   ```

### Rolling Back

1. **Stop services**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml down
   ```

2. **Restore backup** (see Recovery Procedure)

3. **Use previous image tag**:
   ```bash
   docker tag apollo-backend:v4.1-cuda apollo-backend:latest
   ```

4. **Restart**:
   ```bash
   docker compose -f backend/docker-compose.atlas.yml up -d
   ```

---

[← Back to Model Management](model-management.md) | [Next: Troubleshooting →](troubleshooting.md)
