# Gradio Deprecation Notice

**Date**: 2025-10-13
**Status**: ⚠️ **DEPRECATED**
**Removal Target**: v4.0

---

## Summary

The Gradio UI has been **fully replaced** by a modern **React + FastAPI** architecture. All Gradio-related files are now deprecated and marked for removal.

---

## What Changed

### Old Architecture (Deprecated)
```
┌─────────────────┐
│  Gradio UI      │  Port 7860
│  (_src/app.py)  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │   RAG    │
    │  Engine  │
    └──────────┘
```

### New Architecture (Production)
```
┌──────────────────┐         ┌──────────────────┐
│   React Frontend │  :3000  │  FastAPI Backend │  :8000
│   (TypeScript)   │◄────────┤   (REST API)     │
└──────────────────┘         └────────┬─────────┘
                                      │
                                 ┌────▼─────┐
                                 │   RAG    │
                                 │  Engine  │
                                 └──────────┘
```

---

## Deprecated Files

The following files are **no longer used** in production:

### Legacy Gradio Files (Marked for Removal)
```
_src/
  ├── app.py              ⚠️ DEPRECATED - 1,255 lines of Gradio UI
  ├── web_interface.py    ⚠️ DEPRECATED - Alternative Gradio interface
  └── app_v1_backup.py    ⚠️ DEPRECATED - Old backup

_config/
  ├── Dockerfile          ⚠️ DEPRECATED - Gradio container build
  ├── deploy.ps1          ⚠️ DEPRECATED - Gradio deployment script
  └── requirements.txt    ⚠️ DEPRECATED - Includes Gradio dependency
```

### Docker Service Removed
```yaml
# docker-compose.yml
# SERVICE 5: Legacy Gradio Interface - REMOVED
# Was: rag-app service on port 7860
```

---

## Migration Path

### If You're Using Gradio (Old Stack)

**Stop using:**
```bash
# OLD - Don't use this anymore
docker-compose up rag-app    # Port 7860
python _src/app.py           # Direct Gradio launch
```

**Start using:**
```bash
# NEW - Production stack
docker-compose up backend frontend

# Or start services individually:
docker-compose up backend    # Port 8000
docker-compose up frontend   # Port 3000
```

### Access URLs

| Service | Old (Deprecated) | New (Production) |
|---------|------------------|------------------|
| **UI** | http://localhost:7860 (Gradio) | http://localhost:3000 (React) |
| **API** | N/A (Gradio only) | http://localhost:8000/api (FastAPI) |
| **Docs** | N/A | http://localhost:8000/docs (Swagger) |

---

## Production Stack Details

### Frontend (React + TypeScript)
```
frontend/
  ├── src/
  │   ├── components/
  │   │   ├── Chat/ChatWindow.tsx        # Main chat interface
  │   │   ├── Documents/                  # Document management
  │   │   └── Performance/                # Performance metrics
  │   ├── services/api.ts                 # API client
  │   └── App.tsx                          # Root component
  └── package.json
```

### Backend (FastAPI)
```
backend/
  ├── app/
  │   ├── api/
  │   │   ├── query.py           # Query endpoints (Gradio-free)
  │   │   ├── documents.py       # Document management
  │   │   └── settings.py        # Configuration
  │   ├── core/
  │   │   └── rag_engine.py      # Core RAG logic (no UI dependencies)
  │   └── main.py                # FastAPI app
  └── requirements.txt           # No Gradio dependency
```

---

## Benefits of New Architecture

| Feature | Gradio (Old) | React + FastAPI (New) |
|---------|--------------|------------------------|
| **UI Framework** | Python-based | Modern React + TypeScript |
| **API** | Coupled to UI | RESTful, decoupled |
| **Mobile Support** | Poor | Responsive design |
| **Customization** | Limited | Full control |
| **Performance** | Single-threaded | Async, scalable |
| **Documentation** | None | Swagger/OpenAPI |
| **Testing** | Difficult | Unit + integration tests |
| **Deployment** | Monolithic | Microservices-ready |

---

## Timeline

- **v3.5-v3.8** (Current): Gradio marked deprecated, production uses React + FastAPI
- **v3.9** (Next): Remove Gradio files from repository
- **v4.0** (Future): Complete Gradio removal

---

## FAQs

### Q: Can I still use Gradio?

**A:** Technically yes (files still exist), but it's **strongly discouraged**:
- Not maintained
- Not tested
- Missing new features (Qdrant, vLLM)
- Will be removed in v4.0

### Q: How do I access the new UI?

**A:**
```bash
# Start production stack
docker-compose up backend frontend

# Access at:
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### Q: What if I encounter issues with the new stack?

**A:**
1. Check logs: `docker-compose logs backend frontend`
2. See: `docs/DEVELOPMENT.md`
3. Report issues: GitHub Issues

### Q: Will my data (documents, ChromaDB) work with the new stack?

**A:** Yes! The backend RAG engine is the same. Your:
- Documents folder (`./documents`)
- Vector database (`./chroma_db`)
- Configuration (`.env`)

...all work with the new stack without changes.

### Q: Can I run both UIs simultaneously?

**A:** Technically yes, but not recommended:
- Gradio would be on port 7860 (if you manually start it)
- React on port 3000
- Both would share the same backend data

However, **only the React UI receives updates and support**.

---

## Testing Changes

The test suite has been updated to skip Gradio tests:

```python
# tests/manual_validation.py
def test_app_integration(results: TestResults):
    """Test 6: App Integration Points (DEPRECATED - Gradio app removed)"""
    results.add_skip(
        "VectorStoreAdapter class",
        "Legacy Gradio app - Use FastAPI backend instead"
    )
```

**Previous test results:**
- With Gradio tests: 14/17 passed (82.4%) - 2 failures from missing Gradio
- With Gradio skipped: 14/15 passed (93.3%) - Only 1 real issue (VLLMClient attribute)

---

## Additional Resources

- **Architecture**: `docs/ARCHITECTURE.md`
- **Development**: `docs/DEVELOPMENT.md`
- **API Docs**: http://localhost:8000/docs (when running)
- **Project Structure**: `docs/PROJECT_STRUCTURE.md`

---

## Migration Support

If you need help migrating from Gradio to React + FastAPI:

1. Check the docs folder
2. Review `frontend/src/` for React examples
3. Review `backend/app/api/` for API examples
4. Open a GitHub issue if you encounter problems

---

**Last Updated**: 2025-10-13
**Effective**: Immediately
**Complete Removal**: v4.0
