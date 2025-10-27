# Model Management

Apollo supports hotswapping between different LLM models without restarting services.

## Available Models

### Llama 3.1 8B Instruct (Default)

**Size**: 5.4GB (Q5_K_M quantization)

**Performance**:
- Inference Speed: 63.8 tok/s (GPU)
- VRAM Usage: 6-8GB
- Context Window: 8192 tokens
- Quality: Good for most use cases

**Best For**: Speed, general queries, resource-constrained systems

**Download**:
```bash
wget -P ./models https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q5_K_M.gguf
```

### Qwen 2.5 14B Instruct (Premium)

**Size**: 8.9GB (Q5_K_M quantization)

**Performance**:
- Inference Speed: 45-50 tok/s (GPU)
- VRAM Usage: 10-12GB
- Context Window: 32768 tokens
- Quality: Excellent, better reasoning

**Best For**: Complex queries, high-quality answers, coding tasks

**Download**:
```bash
wget -P ./models https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q5_k_m.gguf
```

---

## Model Comparison

| Aspect | Llama 3.1 8B | Qwen 2.5 14B |
|--------|--------------|--------------|
| Size | 5.4GB | 8.9GB |
| Speed (GPU) | 63.8 tok/s | 45-50 tok/s |
| VRAM Required | 8GB | 12GB |
| Context Window | 8192 | 32768 |
| Answer Quality | Good | Excellent |
| Reasoning | Good | Superior |
| Code Generation | Good | Excellent |
| Multilingual | Limited | Strong |

---

## Switching Models

### Method 1: Configuration File

1. **Edit config.yml**:
   ```bash
   nano backend/config.yml
   ```

2. **Update model path**:
   ```yaml
   llamacpp:
     model_path: "/models/qwen2.5-14b-instruct-q5_k_m.gguf"
     n_gpu_layers: 40  # Adjust for your VRAM
   ```

3. **Restart backend**:
   ```bash
   docker restart apollo-backend
   ```

4. **Verify**:
   ```bash
   curl http://localhost:8000/api/settings | jq '.model_name'
   ```

### Method 2: API Endpoint

```bash
curl -X POST http://localhost:8000/api/settings/model \
  -H "Content-Type: application/json" \
  -d '{
    "model_path": "/models/qwen2.5-14b-instruct-q5_k_m.gguf",
    "n_gpu_layers": 40
  }'
```

---

## GPU Layer Optimization

### Calculating Optimal Layers

**Rule of Thumb**: Each layer uses ~200-300MB VRAM (varies by model size)

**Llama 3.1 8B** (35 total layers):
- 12GB VRAM: 25 layers (~60% offload)
- 16GB VRAM: 35 layers (100% offload)
- 24GB VRAM: 35 layers + extra headroom

**Qwen 2.5 14B** (48 total layers):
- 12GB VRAM: 20-25 layers (~50% offload)
- 16GB VRAM: 30-35 layers (~70% offload)
- 24GB VRAM: 48 layers (100% offload)

### Finding Your Limit

```bash
# Start with conservative value
n_gpu_layers: 20

# Monitor VRAM usage
nvidia-smi

# Increase gradually until VRAM ~80% full
n_gpu_layers: 25, 30, 35, ...
```

---

## Model Quality Comparison

### Test Query: "Explain quantum entanglement"

**Llama 3.1 8B**:
```
Quantum entanglement is a phenomenon where two particles become
correlated in such a way that the state of one particle depends
on the state of the other, even when separated by large distances.
This is a key principle in quantum mechanics.
```
**Quality**: Good, accurate, concise

**Qwen 2.5 14B**:
```
Quantum entanglement is a fundamental phenomenon in quantum mechanics
where pairs or groups of particles become interconnected such that
the quantum state of one particle cannot be described independently
of the others, even when separated by vast distances. When a measurement
is made on one entangled particle, it instantaneously affects the
state of its partner(s), regardless of the distance between them.
This "spooky action at a distance," as Einstein called it, has been
experimentally verified and forms the basis for emerging technologies
like quantum computing and quantum cryptography.
```
**Quality**: Excellent, detailed, contextual

---

## Advanced: Custom Models

### Adding a New Model

1. **Download GGUF model** from HuggingFace
2. **Place in `/models` directory**
3. **Update config.yml**:
   ```yaml
   llamacpp:
     model_path: "/models/your-custom-model.gguf"
     n_gpu_layers: 30  # Adjust based on size
   ```
4. **Restart backend**

### Supported Model Formats

- **GGUF** (llama.cpp native format)
- **Q4_K_M, Q5_K_M, Q8_0** quantizations (recommended)

**Not Supported**:
- PyTorch (.pt, .pth)
- SafeTensors (.safetensors)
- ONNX (.onnx)

Convert using [llama.cpp quantization tools](https://github.com/ggerganov/llama.cpp)

---

## Troubleshooting

### Model Won't Load

**Symptom**: 500 error on startup

**Solutions**:
1. Check file exists: `ls -lh /models/`
2. Verify file integrity: Check file size matches expected
3. Check logs: `docker logs apollo-backend`
4. Reduce GPU layers if VRAM insufficient

### Slow Inference After Model Switch

**Symptom**: Speed drops significantly

**Solutions**:
1. Increase `n_gpu_layers`
2. Reduce `n_ctx` (context window)
3. Verify GPU usage: `nvidia-smi`

### CUDA Out of Memory

**Symptom**: `RuntimeError: CUDA out of memory`

**Solutions**:
1. Reduce `n_gpu_layers` by 5-10
2. Reduce `n_ctx` from 8192 to 4096
3. Close other GPU applications

---

## Model Recommendations

### Home Lab / Enthusiast

**Hardware**: RTX 3060-4060 (12GB VRAM)

**Model**: Llama 3.1 8B with 25 GPU layers

**Expected**: 50-55 tok/s

### Professional Workstation

**Hardware**: RTX 4080/5080 (16GB VRAM)

**Model**: Llama 3.1 8B with 35 layers (full offload)

**Expected**: 63-70 tok/s

### Enterprise / Research

**Hardware**: RTX A6000/6000 Ada (48GB VRAM)

**Models**:
- Qwen 2.5 14B (full offload)
- Or Qwen 2.5 32B (partial offload)

**Expected**: 50-60 tok/s (14B), 30-40 tok/s (32B)

---

[← Back to Performance](performance.md) | [Next: Deployment →](deployment.md)
