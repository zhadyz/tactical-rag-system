##
***********************************************************************
                         WARNING NOTICE

You are accessing a U.S. Government (USG) Information System (IS) that
is provided for USG-authorized use only.

By using this IS (which includes any device attached to this IS), you
consent to the following conditions:

- The USG routinely intercepts and monitors communications on this IS
  for purposes including, but not limited to, penetration testing, 
  COMSEC monitoring, network operations and defense, personnel 
  misconduct (PM), law enforcement (LE), and counterintelligence (CI)
  investigations.

- At any time, the USG may inspect and seize data stored on this IS.

- Communications using, or data stored on, this IS are not private,
  are subject to routine monitoring, interception, and search, and may
  be disclosed or used for any USG-authorized purpose.

- This IS includes security measures (e.g., authentication and access
  controls) to protect USG interests--not for your personal benefit or
  privacy.

- Notwithstanding the above, using this IS does not constitute consent
  to PM, LE or CI investigative searching or monitoring of the content
  of privileged communications, or work product, related to personal
  representation or services by attorneys, psychotherapists, or clergy,
  and their assistants. Such communications and work product are
  private and confidential.

***********************************************************************
##


# TACTICAL RAG DOCUMENT INTELLIGENCE SYSTEM
## MAINTAINER GUIDE

---

## SYSTEM OVERVIEW

This is a Docker-based RAG (Retrieval-Augmented Generation) system that enables semantic search and question-answering over document collections using LangChain, ChromaDB, and Ollama.

### Architecture:
```
┌─────────────────┐      ┌──────────────────┐
│  Gradio Web UI  │─────▶│  RAG Application │
│  (Port 7860)    │      │  (Python/Flask)  │
└─────────────────┘      └────────┬─────────┘
                                  │
                         ┌────────┴─────────┐
                         ▼                  ▼
                  ┌─────────────┐    ┌──────────┐
                  │  ChromaDB   │    │  Ollama  │
                  │  (Vector DB)│    │  (LLM)   │
                  └─────────────┘    └──────────┘
```

### Components:
- **Ollama Container**: Runs llama3.1:8b (LLM) and nomic-embed-text (embeddings)
- **RAG App Container**: Python application with LangChain, Gradio UI, OCR capabilities
- **ChromaDB**: Vector database for document embeddings
- **Docker Volumes**: Persistent storage for models and data

---

## TECHNICAL SPECIFICATIONS

### System Requirements:
- Docker Desktop 4.0+
- Windows 10/11 (PowerShell 5.1+)
- 16 GB RAM minimum (8 GB absolute minimum)
- 20 GB free disk space
- No GPU required (CPU inference mode)

### Docker Images:
- **ollama/ollama:latest** (~5 GB) - Ollama server
- **ollama-rag-app:latest** (~3 GB) - Custom built application

### AI Models:
- **llama3.1:8b** (~4.7 GB) - Main LLM for generation
- **nomic-embed-text** (~274 MB) - Embedding model
- Both stored in Docker volume `ollama_ollama-data`

### Python Dependencies (Key):
```
langchain==0.3.0
langchain-ollama==0.2.0
chromadb==0.5.23
gradio==5.5.0
pypdf==5.1.0
pytesseract==0.3.13
pdf2image==1.17.0
```

### Document Processing:
- **Supported formats**: .txt, .pdf, .docx, .doc, .md
- **OCR**: Tesseract 4.x for scanned PDFs
- **Chunking**: 1000 chars with 200 char overlap
- **Embedding dimension**: 768

---

## FILE STRUCTURE

```
deployment-package/
├── rag-app-image.tar          # Saved Docker image (RAG app)
├── ollama-image.tar           # Saved Docker image (Ollama)
├── ollama-models.tar.gz       # AI models volume export
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Build instructions
├── requirements.txt           # Python dependencies
├── app.py                     # Main application (Gradio UI)
├── index_documents.py         # Document indexing script
├── startup.sh                 # Container entrypoint
├── deploy.ps1                 # Deployment automation
├── deploy.bat                 # Windows wrapper
├── swap-mission.ps1           # Mission change script
├── swap-mission.bat           # Windows wrapper
├── stop.ps1                   # Shutdown script
├── stop.bat                   # Windows wrapper
├── README-OPERATOR.md         # User guide
├── README-MAINTAINER.md       # This file
├── documents/                 # Document storage (volume mount)
└── chroma_db/                 # Vector database (volume mount)
```

---

## DEPLOYMENT WORKFLOW

### Initial Build (Development):
```bash
# 1. Build images
docker-compose up --build -d

# 2. Verify functionality
docker ps
docker-compose logs -f rag-app

# 3. Test with sample documents
# Add files to documents/, access http://localhost:7860

# 4. Save for offline deployment
docker save ollama-rag-app:latest -o rag-app-image.tar
docker save ollama/ollama:latest -o ollama-image.tar
docker run --rm -v ollama_ollama-data:/data -v ${PWD}:/backup alpine tar czf /backup/ollama-models.tar.gz -C /data .
```

### Field Deployment (Offline):
```bash
# 1. Copy deployment package to target machine
# 2. Ensure Docker Desktop is running
# 3. Load saved images
docker load -i rag-app-image.tar
docker load -i ollama-image.tar

# 4. Restore models
docker run --rm -v ollama_ollama-data:/data -v ${PWD}:/backup alpine sh -c "cd /data && tar xzf /backup/ollama-models.tar.gz"

# 5. Start system
docker-compose up -d
```

### MAINTENANCE
```bash
docker-compose down
docker-compose build --no-cache
Remove-Item -Recurse -Force chroma_db
docker-compose up -d
docker-compose logs -f rag-app
```

---

## TROUBLESHOOTING

### Container Won't Start

**Symptom**: `rag-tactical-system` shows as unhealthy or exits immediately

**Check**:
```bash
docker-compose logs rag-app
docker-compose logs ollama
```

**Common Causes**:
1. Ollama not responding
   - Check: `curl http://localhost:11434/api/tags`
   - Fix: Restart Ollama container
2. Port conflict
   - Check: `netstat -ano | findstr :7860`
   - Fix: Kill process or change port in docker-compose.yml
3. Volume mount issue
   - Check: `docker volume ls`
   - Fix: `docker volume rm ollama_ollama-data && docker-compose up -d`

### Database Issues

**Symptom**: System answers "I don't know" for everything

**Check**:
```bash
# Verify documents are indexed
docker exec rag-tactical-system python -c "from langchain_chroma import Chroma; from langchain_ollama import OllamaEmbeddings; import os; embeddings = OllamaEmbeddings(model='nomic-embed-text', base_url=os.getenv('OLLAMA_HOST')); vectorstore = Chroma(persist_directory='./chroma_db', embedding_function=embeddings); print(f'Chunks: {vectorstore._collection.count()}')"
```

**Fix**:
```bash
docker-compose down
Remove-Item -Recurse -Force chroma_db
docker-compose up -d
```

### OCR Failures

**Symptom**: PDFs fail to index or show "no text content"

**Causes**:
1. Scanned PDF (expected - uses OCR, takes longer)
2. Corrupted PDF
3. Password-protected PDF (not supported)

**Debug**:
```bash
docker exec -it rag-tactical-system python index_documents.py
```

### Memory Issues

**Symptom**: Container crashes, system becomes unresponsive

**Check**:
```bash
docker stats
```

**Fix**:
- Increase Docker Desktop memory allocation (Settings → Resources)
- Reduce chunk size in `index_documents.py`
- Process fewer documents per batch

---

## CUSTOMIZATION

### Change LLM Model:
Edit `app.py`:
```python
llm = OllamaLLM(
    model="llama3.1:8b",  # Change to different model
    temperature=0,
    num_ctx=4096
)
```

Download new model:
```bash
docker exec -it ollama-server ollama pull <model-name>
```

### Adjust Chunking:
Edit `index_documents.py`:
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Increase for more context
    chunk_overlap=200,    # Increase for better continuity
    length_function=len
)
```

### Change Retrieval Count:
Edit `app.py`:
```python
retriever=vectorstore.as_retriever(search_kwargs={"k": 3})  # Change k value
```

### Modify UI Theme:
Edit `app.py` CSS section (search for `custom_css`).

---

## MAINTENANCE TASKS

### Update Dependencies:
```bash
# 1. Update requirements.txt
# 2. Rebuild
docker-compose build --no-cache
docker-compose up -d

# 3. Test thoroughly
# 4. Re-save images
docker save ollama-rag-app:latest -o rag-app-image-v2.tar
```

### Clear Everything (Reset):
```bash
docker-compose down -v
docker rmi ollama-rag-app:latest ollama/ollama:latest
Remove-Item -Recurse -Force chroma_db
# Rebuild from scratch
```

### Backup Strategy:
```bash
# Backup documents
tar czf documents-backup-$(date +%Y%m%d).tar.gz documents/

# Backup database
tar czf chroma_db-backup-$(date +%Y%m%d).tar.gz chroma_db/

# Backup configuration
tar czf config-backup-$(date +%Y%m%d).tar.gz docker-compose.yml requirements.txt Dockerfile
```

### Monitor Disk Usage:
```bash
docker system df
docker volume ls
docker images
```

---

## PERFORMANCE TUNING

### Embedding Generation:
- First index: ~30 seconds per 1000 chunks
- OCR: ~30-60 seconds per page
- Query response: 2-5 seconds

### Optimization:
1. **Reduce chunk size** - Faster indexing, less context
2. **Increase retrieval k** - Better answers, slower queries
3. **Use GPU** - 10x faster (requires NVIDIA GPU + CUDA)
4. **Batch processing** - Index documents in smaller batches

### Resource Allocation:
```yaml
# In docker-compose.yml, add:
services:
  rag-app:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

---

## SECURITY CONSIDERATIONS

### Current Security Posture:
- ✅ Runs locally (no external network calls after setup)
- ✅ No data exfiltration
- ✅ Isolated Docker containers
- ⚠️ No authentication (local access only)
- ⚠️ HTTP only (no HTTPS)

### Hardening (if needed):
1. **Add authentication**: Integrate basic auth in Gradio
2. **Enable HTTPS**: Use nginx reverse proxy with SSL
3. **Network isolation**: Use Docker networks strictly
4. **File permissions**: Restrict document folder access
5. **Audit logging**: Add logging for all queries/access

---

## KNOWN ISSUES

### Issue: Volume Mount Busy Error
**When**: Re-indexing with existing chroma_db
**Workaround**: Delete chroma_db from host before indexing
**Status**: Fixed in index_documents.py (clears contents instead of deleting folder)

### Issue: Container Network Resolution
**When**: Containers can't communicate
**Workaround**: Ensure both services on same network in docker-compose.yml
**Status**: Fixed

### Issue: First Startup Slow
**When**: Initial deployment (no cached models)
**Expected**: 15-30 minutes to download models
**Status**: Normal behavior

---

## DEVELOPMENT NOTES

### Adding New Document Types:
1. Add loader in `index_documents.py`:
```python
def load_<format>(self, file_path: str):
    # Implementation
    return documents
```
2. Add to supported_formats dict
3. Update README supported formats list
4. Test with sample files

### Modifying RAG Chain:
Located in `app.py`, function `initialize_rag()`:
- Change retrieval strategy
- Modify prompt template
- Adjust LLM parameters
- Add conversation memory

### UI Modifications:
All UI code in `app.py`:
- Gradio Blocks for layout
- Custom CSS for styling
- HTML components for cards/status

---

## SUPPORT ESCALATION

### Level 1 (Operator):
- System won't start → Check Docker Desktop
- No answers → Re-index documents
- Slow performance → Normal for large files

### Level 2 (Maintainer):
- Container crashes → Check logs and memory
- Indexing fails → Verify file formats and OCR
- Network issues → Verify docker-compose.yml network config

### Level 3 (Developer):
- Code modifications needed
- New feature requests
- Integration with other systems
- Performance optimization beyond configuration

---

## TESTING CHECKLIST

### Pre-Deployment:
- [ ] All document types load correctly
- [ ] OCR processes scanned PDFs
- [ ] Answers cite correct sources
- [ ] System runs offline (disconnect network)
- [ ] Scripts execute without errors
- [ ] Browser opens automatically
- [ ] Database persists across restarts

### Post-Deployment:
- [ ] Images load successfully
- [ ] Models restore correctly
- [ ] Documents index properly
- [ ] UI accessible at localhost:7860
- [ ] Swap-mission workflow functions
- [ ] Stop/start cycle works

---

## VERSION CONTROL

### Current Version: 1.0
**Build Date**: 2025-10-01
**Python**: 3.11
**Docker**: 24.x+
**Ollama**: 0.12.3

### Change Log:
- **v1.0** (2025-10-01): Initial release
  - Multi-format document support
  - OCR for scanned PDFs
  - Docker containerization
  - Offline deployment capability
  - PowerShell automation scripts

### Upgrade Path:
When updating Python dependencies:
1. Test in development first
2. Lock versions in requirements.txt
3. Rebuild and test thoroughly
4. Create new .tar files
5. Version deployment package (v1.1, etc.)
6. Keep old version as backup

---

## CONTACT & RESOURCES

### Documentation:
- LangChain: https://docs.langchain.com
- Ollama: https://github.com/ollama/ollama
- ChromaDB: https://docs.trychroma.com
- Gradio: https://gradio.app/docs

### Debug Commands:
```bash
# View all logs
docker-compose logs

# Follow live logs
docker-compose logs -f rag-app

# Enter container shell
docker exec -it rag-tactical-system bash

# Check Ollama models
docker exec ollama-server ollama list

# Test embedding generation
docker exec rag-tactical-system python -c "from langchain_ollama import OllamaEmbeddings; import os; e = OllamaEmbeddings(model='nomic-embed-text', base_url=os.getenv('OLLAMA_HOST')); print(len(e.embed_query('test')))"

# Check database status
docker exec rag-tactical-system ls -lh chroma_db/
```

---

## APPENDIX: COMMAND REFERENCE

### Docker Commands:
```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# Rebuild application
docker-compose up --build -d

# View container status
docker ps

# Remove everything
docker-compose down -v

# Save images
docker save <image>:latest -o <name>.tar

# Load images
docker load -i <name>.tar
```

### Maintenance Commands:
```bash
# Re-index documents
docker exec rag-tactical-system python index_documents.py

# Check document count
docker exec rag-tactical-system ls documents/ | wc -l

# Clear database
Remove-Item -Recurse -Force chroma_db

# Check system resources
docker stats

# Prune unused data
docker system prune -a
```