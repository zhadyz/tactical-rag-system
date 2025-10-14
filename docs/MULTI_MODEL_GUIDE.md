# Multi-Model LLM System - User Guide

This system supports **multiple LLM models** that you can switch between based on your needs. Each model has different characteristics in terms of speed, quality, and hardware requirements.

## Available Models

### 1. Llama 3.1 8B (Ollama) - **DEFAULT FALLBACK**
- **Speed**: ⚡⚡ (2/5) - Slower (~16 seconds)
- **Quality**: ⭐⭐⭐⭐⭐ (5/5) - Excellent
- **VRAM Required**: 0GB (uses system RAM)
- **Best For**: High-quality responses, fallback when GPU unavailable
- **Status**: ✅ Always available

**Pros:**
- Excellent response quality
- Works without GPU
- Reliable and stable

**Cons:**
- Slower responses (16s per query)
- Uses CPU which may be slower

---

### 2. Phi-3 Mini - **RECOMMENDED FOR 8GB GPU**
- **Speed**: ⚡⚡⚡⚡ (4/5) - Fast (~1-2 seconds)
- **Quality**: ⭐⭐⭐⭐ (4/5) - Good
- **VRAM Required**: 6-8GB
- **Best For**: Quick responses, Q&A, summarization
- **Status**: ✅ Available on 8GB+ GPUs

**Pros:**
- Excellent balance of speed and quality
- Fits on 8GB VRAM
- 10-20x faster than Ollama

**Cons:**
- Slightly lower quality than larger models
- Requires GPU

---

### 3. TinyLlama 1.1B - **FASTEST**
- **Speed**: ⚡⚡⚡⚡⚡ (5/5) - Ultra-fast (<1 second)
- **Quality**: ⭐⭐ (2/5) - Basic
- **VRAM Required**: 3-4GB
- **Best For**: Speed priority, simple questions, testing
- **Status**: ✅ Available on 4GB+ GPUs

**Pros:**
- Blazing fast responses
- Very low VRAM usage
- Great for simple queries

**Cons:**
- Basic quality
- Not suitable for complex reasoning

---

### 4. Qwen 2.5 7B - **BEST QUALITY FOR 8GB**
- **Speed**: ⚡⚡⚡⚡ (4/5) - Fast (~1-2 seconds)
- **Quality**: ⭐⭐⭐⭐⭐ (5/5) - Excellent
- **VRAM Required**: 7-10GB
- **Best For**: Best quality on 8GB GPUs, complex reasoning
- **Status**: ✅ Available on 8GB+ GPUs

**Pros:**
- Best quality for 8GB hardware
- Strong reasoning capabilities
- Fast inference

**Cons:**
- Requires 8GB minimum
- Slightly higher VRAM usage

---

### 5. Mistral 7B Instruct - **FUTURE UPGRADE**
- **Speed**: ⚡⚡⚡⚡ (4/5) - Fast (~1-2 seconds)
- **Quality**: ⭐⭐⭐⭐⭐ (5/5) - Excellent
- **VRAM Required**: 12-16GB
- **Best For**: Production use, best overall quality
- **Status**: ❌ Disabled (requires 16GB+ GPU)

**Pros:**
- Industry-leading quality
- Fast inference with vLLM
- Excellent instruction-following

**Cons:**
- Requires GPU upgrade (RTX 4060 Ti 16GB or better)
- Not available on 8GB cards

---

## Quick Start

### Using Docker Compose

#### Start Phi-3 Mini (Recommended for 8GB GPU):
```bash
# Stop current containers
docker-compose down

# Start with Phi-3
docker-compose -f docker-compose.multi-model.yml --profile phi3 up -d
docker-compose up -d backend frontend
```

#### Start TinyLlama (Fastest):
```bash
docker-compose -f docker-compose.multi-model.yml --profile tinyllama up -d
docker-compose up -d backend frontend
```

#### Start Qwen 2.5 (Best quality for 8GB):
```bash
docker-compose -f docker-compose.multi-model.yml --profile qwen up -d
docker-compose up -d backend frontend
```

#### Start Ollama Only (No GPU needed):
```bash
docker-compose up -d ollama redis backend frontend
```

### Using the UI

1. Open the web interface at `http://localhost:3000`
2. Click on the **Model Selector** dropdown (top right)
3. Choose your preferred model
4. Click **Select Model**
5. New queries will use the selected model

### Using the API

#### List Available Models:
```bash
curl http://localhost:8000/api/models/
```

#### Get Model Info:
```bash
curl http://localhost:8000/api/models/phi3-mini
```

#### Select a Model:
```bash
curl -X POST http://localhost:8000/api/models/select \
  -H "Content-Type: application/json" \
  -d '{"model_id": "phi3-mini"}'
```

#### Get Recommendation:
```bash
curl -X POST http://localhost:8000/api/models/recommend \
  -H "Content-Type: application/json" \
  -d '{"vram_gb": 8, "priority": "balanced"}'
```

---

## Hardware Recommendations

| Your GPU | Recommended Model | Alternatives |
|----------|------------------|--------------|
| **No GPU / CPU only** | Llama 3.1 8B (Ollama) | N/A |
| **4GB VRAM** | TinyLlama | Ollama fallback |
| **6GB VRAM** | Phi-3 Mini | TinyLlama, Ollama |
| **8GB VRAM** | Qwen 2.5 7B | Phi-3, TinyLlama, Ollama |
| **12GB+ VRAM** | Qwen 2.5 7B | Phi-3, TinyLlama, Ollama |
| **16GB+ VRAM** | Mistral 7B | Qwen, Phi-3, Ollama |

---

## Performance Comparison

### Query: "What are the Air Force beard grooming standards?"

| Model | Cold Query | Cached Query | Quality | Notes |
|-------|------------|--------------|---------|-------|
| **Ollama Llama 3.1** | ~16s | <1ms | Excellent | CPU/RAM, no GPU needed |
| **Phi-3 Mini** | ~1-2s | <100ms | Good | Best for 8GB, balanced |
| **TinyLlama** | ~0.5s | <50ms | Basic | Ultra-fast, simple queries |
| **Qwen 2.5 7B** | ~1-2s | <100ms | Excellent | Best quality for 8GB |
| **Mistral 7B** | ~1-2s | <100ms | Excellent | Requires 16GB+ VRAM |

*Cached queries use Redis and are near-instant for all models*

---

## Troubleshooting

### Model Won't Start

**Symptom**: vLLM container crashes or shows errors

**Cause**: Insufficient VRAM

**Solution**:
1. Check your GPU VRAM: `nvidia-smi`
2. Use a smaller model (see Hardware Recommendations)
3. Fall back to Ollama (always works)

### Model Selection Not Working

**Symptom**: UI shows model selected but queries still use old model

**Solution**:
1. Refresh the page
2. Clear browser cache
3. Restart backend: `docker-compose restart backend`

### Slow Responses

**Symptom**: Queries taking too long

**Possible Causes**:
1. Using Ollama (expected 16s)
2. Cold start (first query always slower)
3. Cache disabled
4. GPU under load

**Solutions**:
1. Switch to faster model (Phi-3, TinyLlama)
2. Enable caching (should be default)
3. Check GPU usage: `nvidia-smi`

---

## Advanced Configuration

### Custom Model Addition

To add a new model:

1. **Edit `_src/model_registry.py`**:
```python
"my-model": ModelSpec(
    id="my-model",
    name="My Custom Model",
    backend=ModelBackend.VLLM,
    model_path="organization/model-name",
    size=ModelSize.MEDIUM,
    parameters="7B",
    min_vram_gb=8,
    recommended_vram_gb=12,
    speed_rating=4,
    quality_rating=5,
    host="http://vllm-mymodel:8000",
    port=8005,
    description="My custom model description",
    use_cases=["Use case 1", "Use case 2"],
    available=True
)
```

2. **Add to `docker-compose.multi-model.yml`**:
```yaml
vllm-mymodel:
  image: vllm/vllm-openai:v0.5.4
  container_name: rag-vllm-mymodel
  ports:
    - "8005:8000"
  command: >
    --model organization/model-name
    --max-model-len 2048
    --gpu-memory-utilization 0.85
  # ... (rest of config)
  profiles:
    - mymodel
```

3. **Start your model**:
```bash
docker-compose -f docker-compose.multi-model.yml --profile mymodel up -d
```

---

## Future Roadmap

- [ ] **Automatic Model Switching**: Intelligently select model based on query complexity
- [ ] **Model Ensemble**: Use multiple models for different parts of the pipeline
- [ ] **Fine-tuned Models**: Domain-specific models trained on Air Force documents
- [ ] **Quantization**: 4-bit/8-bit quantized models for lower VRAM usage
- [ ] **Cloud GPU Support**: AWS/Azure GPU instances for larger models

---

## FAQs

**Q: Which model should I use?**
A: For 8GB GPU: Qwen 2.5 7B for best quality, Phi-3 Mini for balanced, TinyLlama for speed. No GPU: Ollama Llama 3.1.

**Q: Can I run multiple models at once?**
A: Not recommended on 8GB VRAM. Models share GPU memory. Run one at a time.

**Q: How do I upgrade to use Mistral 7B?**
A: You need a GPU with 16GB+ VRAM (RTX 4060 Ti 16GB, RTX 4080, RTX 4090, etc.)

**Q: Will switching models lose my conversation history?**
A: No, conversation history persists across model switches.

**Q: Can I use models from other providers (OpenAI, Anthropic)?**
A: Not yet, but it's on the roadmap. Currently supports Ollama and vLLM only.

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs backend`
2. Check GPU: `nvidia-smi`
3. Test API: `curl http://localhost:8000/api/models/health`
4. Check model status: `curl http://localhost:8000/api/models/`

