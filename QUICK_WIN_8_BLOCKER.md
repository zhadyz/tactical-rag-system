# Quick Win #8: Speculative Decoding - BLOCKER DISCOVERED

## Status: BLOCKED - Tokenizer Incompatibility

### Issue Summary
Speculative decoding implementation failed due to tokenizer incompatibility between Llama 3.1-8B and Llama 3.2-1B models.

### Error Details
```
ValueError: operands could not be broadcast together with shapes (0,) (82,)
```

**Root Cause**: Llama 3.2 uses a different tokenizer than Llama 3.1, making them incompatible for speculative decoding. Speculative decoding requires the draft model and main model to share the same tokenizer.

### Test Results

**Baseline (No Speculative Decoding)**:
- Average: 22,390ms (22.4 seconds)
- Range: [19,846ms, 27,729ms]
- **CRITICAL**: This is CPU performance, not GPU!

Expected GPU performance: ~300ms (63 tok/s × ~100 tokens)

**Speculative Decoding Test**: FAILED with ValueError

### Critical Discovery: GPU Not Being Used

The baseline test showed 22+ seconds per generation, which indicates **CPU inference**, not GPU.

Expected GPU performance with RTX 5080:
- Throughput: 63.8 tokens/second (confirmed in previous tests)
- 100 token generation: ~1,500-2,000ms (including TTFT overhead)
- **Actual observed: 22,000ms (11-15x slower than expected)**

### Solution Options

#### Option 1: Fix GPU Acceleration (HIGHEST PRIORITY)
**Status**: INVESTIGATE
**Impact**: 22,000ms → 2,000ms (10x speedup)
**Risk**: Low - GPU works in production

**Actions**:
1. Verify n_gpu_layers=33 is actually offloading to GPU
2. Check CUDA availability in llama-cpp-python
3. Test with verbose=True to see GPU utilization logs

#### Option 2: Find Compatible Draft Model
**Status**: RESEARCH NEEDED
**Impact**: 2,000ms → 1,200ms (40% speedup, after GPU fix)
**Risk**: High - Limited Llama 3.1 small models available

**Candidates**:
- TinyLlama 1.1B (different architecture, may not work)
- Custom quantized Llama 3.1 8B to 1B (requires model surgery)
- Wait for Llama 3.1 1B official release (unknown ETA)

#### Option 3: Alternative Optimizations
**Status**: FALLBACK
**Impact**: Various
**Risk**: Medium

**Alternatives**:
- Reduce max_tokens from 2048 to 512 (context-appropriate)
- Implement prompt caching (reuse KV cache for repeated contexts)
- Use Flash Attention 2 (if supported by llama-cpp-python)

### Recommendation

**PIVOT TO OPTION 1 IMMEDIATELY**

The 22-second generation time indicates GPU acceleration is NOT working despite our Docker configuration. Fixing GPU acceleration will provide a 10x speedup (22,000ms → 2,000ms), which is **5x better** than speculative decoding's target improvement (500ms → 300ms).

**Next Steps**:
1. Create GPU verification test
2. Check llama-cpp-python CUDA build
3. Verify n_gpu_layers parameter is being applied
4. Test with verbose logging enabled

### Impact on Timeline

- Quick Win #8 (Speculative Decoding): **BLOCKED** until compatible draft model found
- **NEW Quick Win #8a** (GPU Acceleration Fix): **HIGH PRIORITY** - 10x improvement potential
- Overall performance impact: **MUCH LARGER** than originally scoped

### References

- Llama 3.1 8B model: `Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf` (5.7GB)
- Llama 3.2 1B draft: `Llama-3.2-1B-Instruct.Q4_K_M.gguf` (808MB) - **INCOMPATIBLE**
- llama-cpp-python version: 0.3.2
- Test date: 2025-10-27

---

**Author**: MENDICANT_BIAS
**Status**: BLOCKED - Awaiting GPU acceleration verification
**Priority**: P0 - Performance regression detected
