"""
Model Registry - Centralized configuration for all available LLM models
Supports both Ollama and vLLM backends with automatic model selection
"""

from dataclasses import dataclass
from typing import Literal, Optional
from enum import Enum


class ModelBackend(str, Enum):
    """LLM backend types"""
    OLLAMA = "ollama"
    VLLM = "vllm"


class ModelSize(str, Enum):
    """Model size categories"""
    TINY = "tiny"      # < 2B parameters
    SMALL = "small"    # 2-4B parameters
    MEDIUM = "medium"  # 5-8B parameters
    LARGE = "large"    # 9-15B parameters
    XLARGE = "xlarge"  # 16B+ parameters


@dataclass
class ModelSpec:
    """Specification for a single LLM model"""
    # Identity
    id: str                    # Unique identifier (e.g., "phi3-mini")
    name: str                  # Display name (e.g., "Phi-3 Mini")
    backend: ModelBackend      # ollama or vllm

    # Model details
    model_path: str           # HuggingFace ID or Ollama model name
    size: ModelSize           # Size category
    parameters: str           # Human-readable (e.g., "3.8B")

    # Requirements
    min_vram_gb: int          # Minimum VRAM needed
    recommended_vram_gb: int  # Recommended VRAM

    # Performance characteristics
    speed_rating: int         # 1-5 (1=slowest, 5=fastest)
    quality_rating: int       # 1-5 (1=basic, 5=excellent)

    # Connection details
    host: Optional[str] = None           # Override default host
    port: Optional[int] = None           # Override default port
    max_tokens: Optional[int] = 512      # Max output tokens
    timeout: Optional[int] = 180         # Request timeout

    # Metadata
    description: str = ""               # User-facing description
    use_cases: list[str] = None        # Recommended use cases
    available: bool = True             # Currently available
    default: bool = False              # Default selection

    def __post_init__(self):
        if self.use_cases is None:
            self.use_cases = []


# ============================================================
# Model Registry - All Available Models
# ============================================================

AVAILABLE_MODELS = {

    # ============================================================
    # OLLAMA MODELS (CPU/System RAM fallback)
    # ============================================================

    "llama3.1-8b": ModelSpec(
        id="llama3.1-8b",
        name="Llama 3.1 8B (Ollama)",
        backend=ModelBackend.OLLAMA,
        model_path="llama3.1:8b",
        size=ModelSize.MEDIUM,
        parameters="8B",
        min_vram_gb=0,  # Uses system RAM
        recommended_vram_gb=0,
        speed_rating=2,  # Slower (16s)
        quality_rating=5,  # Excellent quality
        host="http://ollama:11434",
        max_tokens=512,
        timeout=120,
        description="Meta's Llama 3.1 via Ollama. Excellent quality, slower speed. Uses CPU/RAM instead of GPU.",
        use_cases=["High-quality responses", "Complex reasoning", "Fallback when GPU unavailable"],
        available=True,
        default=True  # Default fallback
    ),

    # ============================================================
    # vLLM MODELS (GPU-accelerated, 10-20x faster)
    # ============================================================

    "phi3-mini": ModelSpec(
        id="phi3-mini",
        name="Phi-3 Mini",
        backend=ModelBackend.VLLM,
        model_path="microsoft/Phi-3-mini-4k-instruct",
        size=ModelSize.SMALL,
        parameters="3.8B",
        min_vram_gb=6,
        recommended_vram_gb=8,
        speed_rating=4,  # Fast (1-2s)
        quality_rating=4,  # Good quality
        host="http://vllm-phi3:8000",
        port=8001,
        max_tokens=512,
        timeout=180,
        description="Microsoft's Phi-3 Mini. Excellent balance of speed and quality for 8GB GPUs.",
        use_cases=["Quick responses", "Q&A", "Summarization", "Best for 8GB VRAM"],
        available=True,
        default=False
    ),

    "tinyllama": ModelSpec(
        id="tinyllama",
        name="TinyLlama 1.1B",
        backend=ModelBackend.VLLM,
        model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        size=ModelSize.TINY,
        parameters="1.1B",
        min_vram_gb=3,
        recommended_vram_gb=4,
        speed_rating=5,  # Very fast (<1s)
        quality_rating=2,  # Basic quality
        host="http://vllm-tinyllama:8000",
        port=8002,
        max_tokens=512,
        timeout=180,
        description="Ultra-fast tiny model. Basic quality but blazing speed. Perfect for simple queries.",
        use_cases=["Speed priority", "Simple questions", "Testing", "Low VRAM"],
        available=True,
        default=False
    ),

    "qwen2.5-7b": ModelSpec(
        id="qwen2.5-7b",
        name="Qwen 2.5 7B",
        backend=ModelBackend.VLLM,
        model_path="Qwen/Qwen2.5-7B-Instruct",
        size=ModelSize.MEDIUM,
        parameters="7B",
        min_vram_gb=7,
        recommended_vram_gb=10,
        speed_rating=4,  # Fast (1-2s)
        quality_rating=5,  # Excellent quality
        host="http://vllm-qwen:8000",
        port=8003,
        max_tokens=512,
        timeout=180,
        description="Alibaba's Qwen 2.5. Best quality for 8GB GPUs. Strong reasoning and instruction-following.",
        use_cases=["Best quality on 8GB", "Complex reasoning", "Instruction-following"],
        available=True,
        default=False
    ),

    "mistral-7b": ModelSpec(
        id="mistral-7b",
        name="Mistral 7B Instruct",
        backend=ModelBackend.VLLM,
        model_path="mistralai/Mistral-7B-Instruct-v0.3",
        size=ModelSize.MEDIUM,
        parameters="7B",
        min_vram_gb=12,
        recommended_vram_gb=16,
        speed_rating=4,  # Fast (1-2s)
        quality_rating=5,  # Excellent quality
        host="http://vllm-mistral:8000",
        port=8004,
        max_tokens=512,
        timeout=180,
        description="Mistral AI's flagship 7B model. Requires 16GB+ VRAM. Excellent quality and speed.",
        use_cases=["Best overall quality", "For 16GB+ GPUs", "Production use"],
        available=False,  # Disabled by default (requires GPU upgrade)
        default=False
    ),
}


# ============================================================
# Helper Functions
# ============================================================

def get_model(model_id: str) -> Optional[ModelSpec]:
    """Get model spec by ID"""
    return AVAILABLE_MODELS.get(model_id)


def get_available_models() -> list[ModelSpec]:
    """Get all available models"""
    return [model for model in AVAILABLE_MODELS.values() if model.available]


def get_models_by_backend(backend: ModelBackend) -> list[ModelSpec]:
    """Get all models for a specific backend"""
    return [
        model for model in AVAILABLE_MODELS.values()
        if model.backend == backend and model.available
    ]


def get_models_by_vram(max_vram_gb: int) -> list[ModelSpec]:
    """Get models that fit within VRAM budget"""
    return [
        model for model in AVAILABLE_MODELS.values()
        if model.min_vram_gb <= max_vram_gb and model.available
    ]


def get_default_model() -> ModelSpec:
    """Get the default model"""
    for model in AVAILABLE_MODELS.values():
        if model.default and model.available:
            return model
    # Fallback to first available
    return get_available_models()[0]


def get_fastest_model() -> ModelSpec:
    """Get the fastest available model"""
    available = get_available_models()
    return max(available, key=lambda m: m.speed_rating)


def get_best_quality_model() -> ModelSpec:
    """Get the highest quality available model"""
    available = get_available_models()
    return max(available, key=lambda m: m.quality_rating)


def recommend_model_for_vram(vram_gb: int) -> ModelSpec:
    """Recommend best model for given VRAM"""
    candidates = get_models_by_vram(vram_gb)
    if not candidates:
        return get_default_model()

    # Sort by quality first, then speed
    candidates.sort(key=lambda m: (m.quality_rating, m.speed_rating), reverse=True)
    return candidates[0]


def get_model_info_dict(model_id: str) -> dict:
    """Get model info as dictionary for API responses"""
    model = get_model(model_id)
    if not model:
        return None

    return {
        "id": model.id,
        "name": model.name,
        "backend": model.backend.value,
        "parameters": model.parameters,
        "size": model.size.value,
        "speed_rating": model.speed_rating,
        "quality_rating": model.quality_rating,
        "min_vram_gb": model.min_vram_gb,
        "recommended_vram_gb": model.recommended_vram_gb,
        "description": model.description,
        "use_cases": model.use_cases,
        "available": model.available,
        "default": model.default,
    }


def get_all_models_info() -> list[dict]:
    """Get info for all models as list of dicts"""
    return [get_model_info_dict(model.id) for model in AVAILABLE_MODELS.values()]


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":
    print("=== Available Models ===")
    for model in get_available_models():
        print(f"\n{model.name} ({model.id})")
        print(f"  Backend: {model.backend.value}")
        print(f"  Size: {model.parameters}")
        print(f"  VRAM: {model.min_vram_gb}-{model.recommended_vram_gb}GB")
        print(f"  Speed: {'⚡' * model.speed_rating} ({model.speed_rating}/5)")
        print(f"  Quality: {'⭐' * model.quality_rating} ({model.quality_rating}/5)")
        print(f"  {model.description}")

    print(f"\n\n=== Default Model ===")
    default = get_default_model()
    print(f"{default.name} ({default.id})")

    print(f"\n\n=== Recommended for 8GB VRAM ===")
    recommended = recommend_model_for_vram(8)
    print(f"{recommended.name} ({recommended.id})")
