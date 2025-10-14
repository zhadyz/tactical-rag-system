"""
LLM Factory V2 - Multi-model support with dynamic selection
Integrates with model_registry for centralized model management
"""

import logging
from typing import Union, Optional
from langchain_ollama import OllamaLLM
from vllm_client import VLLMClient, VLLMConfig
from model_registry import (
    ModelSpec, ModelBackend, get_model, get_default_model,
    get_available_models, recommend_model_for_vram
)

logger = logging.getLogger(__name__)


def create_llm_from_model_id(
    model_id: str,
    config=None,
    test_connection: bool = False
) -> Union[OllamaLLM, VLLMClient]:
    """
    Create LLM client from model ID (new multi-model API)

    Args:
        model_id: Model identifier from model_registry (e.g., "phi3-mini", "llama3.1-8b")
        config: Optional SystemConfig for defaults
        test_connection: Test connection before returning client

    Returns:
        Configured LLM client (OllamaLLM or VLLMClient)

    Example:
        # Create Phi-3 client
        llm = create_llm_from_model_id("phi3-mini")

        # Create with config
        llm = create_llm_from_model_id("qwen2.5-7b", config)

        # Use it
        response = llm.invoke("What is RAG?")
    """

    # Get model spec from registry
    model_spec = get_model(model_id)
    if not model_spec:
        logger.error(f"Model '{model_id}' not found in registry")
        logger.info("Falling back to default model")
        model_spec = get_default_model()

    if not model_spec.available:
        logger.warning(f"Model '{model_id}' is not available (may require GPU upgrade)")
        logger.info("Falling back to default model")
        model_spec = get_default_model()

    logger.info("=" * 70)
    logger.info(f"CREATING LLM: {model_spec.name}")
    logger.info(f"  ID: {model_spec.id}")
    logger.info(f"  Backend: {model_spec.backend.value}")
    logger.info(f"  Model: {model_spec.model_path}")
    logger.info(f"  Size: {model_spec.parameters}")
    logger.info(f"  Speed: {'⚡' * model_spec.speed_rating}/5")
    logger.info(f"  Quality: {'⭐' * model_spec.quality_rating}/5")
    logger.info("=" * 70)

    # Route to appropriate backend
    if model_spec.backend == ModelBackend.OLLAMA:
        return _create_ollama_from_spec(model_spec, config, test_connection)
    elif model_spec.backend == ModelBackend.VLLM:
        return _create_vllm_from_spec(model_spec, config, test_connection)
    else:
        raise ValueError(f"Unknown backend: {model_spec.backend}")


def _create_ollama_from_spec(
    model_spec: ModelSpec,
    config=None,
    test_connection: bool = False
) -> OllamaLLM:
    """Create OllamaLLM from ModelSpec"""
    import torch

    # Build Ollama params
    llm_params = {
        'model': model_spec.model_path,
        'base_url': model_spec.host or (config.ollama_host if config else "http://ollama:11434"),
        'num_predict': model_spec.max_tokens or 512,
    }

    # Add generation params from config if available
    if config and hasattr(config, 'llm'):
        llm_params.update({
            'temperature': config.llm.temperature,
            'top_p': config.llm.top_p,
            'top_k': config.llm.top_k,
            'repeat_penalty': config.llm.repeat_penalty,
        })

    # Add GPU support if available
    if torch.cuda.is_available():
        llm_params['num_gpu'] = 1
        logger.info("  GPU available - Ollama will use GPU if model supports it")

    ollama_client = OllamaLLM(**llm_params)

    # Test if requested
    if test_connection:
        try:
            logger.info("  Testing Ollama connection...")
            ollama_client.invoke("Hello")
            logger.info("  ✓ Ollama connection test passed")
        except Exception as e:
            logger.warning(f"  ⚠ Ollama connection test failed: {e}")

    logger.info("=" * 70)
    logger.info("✓ OLLAMA LLM READY")
    logger.info("=" * 70)

    return ollama_client


def _create_vllm_from_spec(
    model_spec: ModelSpec,
    config=None,
    test_connection: bool = False
) -> VLLMClient:
    """Create VLLMClient from ModelSpec"""

    # Get generation params from config or use defaults
    temperature = config.llm.temperature if (config and hasattr(config, 'llm')) else 0.0
    top_p = config.llm.top_p if (config and hasattr(config, 'llm')) else 0.9
    top_k = config.llm.top_k if (config and hasattr(config, 'llm')) else 40

    # Create vLLM client
    vllm_client = VLLMClient(
        host=model_spec.host,
        model=model_spec.model_path,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_tokens=model_spec.max_tokens or 512,
        timeout=model_spec.timeout or 180,
        test_connection=test_connection
    )

    logger.info("=" * 70)
    logger.info("✓ vLLM CLIENT READY - 10-20x speedup active")
    logger.info("=" * 70)

    return vllm_client


def create_llm(
    config,
    model_id: Optional[str] = None,
    force_ollama: bool = False,
    test_connection: bool = False
) -> Union[OllamaLLM, VLLMClient]:
    """
    Unified LLM factory (backward compatible)

    Args:
        config: SystemConfig instance
        model_id: Optional model ID to use (overrides config)
        force_ollama: Force Ollama backend (legacy)
        test_connection: Test connection before returning

    Returns:
        Configured LLM client

    Example:
        # Legacy mode (from config)
        llm = create_llm(config)

        # New mode (explicit model selection)
        llm = create_llm(config, model_id="phi3-mini")

        # Force Ollama fallback
        llm = create_llm(config, force_ollama=True)
    """

    # If model_id provided, use new API
    if model_id:
        return create_llm_from_model_id(model_id, config, test_connection)

    # Legacy mode: check config flags
    if force_ollama:
        return create_llm_from_model_id("llama3.1-8b", config, test_connection)

    # Check if vLLM is enabled in config
    use_vllm = getattr(config, 'use_vllm', False)

    if use_vllm:
        # Try to get model from config, or use default vLLM model
        vllm_model_id = getattr(config, 'vllm_model_id', None)
        if not vllm_model_id:
            # Auto-select best vLLM model for hardware
            # For now, default to phi3-mini (safest for 8GB)
            vllm_model_id = "phi3-mini"

        try:
            return create_llm_from_model_id(vllm_model_id, config, test_connection)
        except Exception as e:
            logger.warning(f"vLLM initialization failed: {e}")
            logger.warning("Falling back to Ollama")
            return create_llm_from_model_id("llama3.1-8b", config, test_connection)
    else:
        # vLLM disabled, use Ollama
        return create_llm_from_model_id("llama3.1-8b", config, test_connection)


def get_llm_type(llm) -> str:
    """
    Determine LLM type from instance

    Returns:
        "vllm" or "ollama"
    """
    if isinstance(llm, VLLMClient):
        return "vllm"
    elif isinstance(llm, OllamaLLM):
        return "ollama"
    else:
        return "unknown"


def get_model_id_from_llm(llm) -> Optional[str]:
    """
    Extract model ID from LLM instance

    Returns:
        Model ID if identifiable, None otherwise
    """
    if isinstance(llm, VLLMClient):
        # Match vLLM model path to registry
        model_path = llm.model
        for model_id, spec in get_available_models():
            if spec.model_path == model_path and spec.backend == ModelBackend.VLLM:
                return model_id
    elif isinstance(llm, OllamaLLM):
        # Match Ollama model name
        model_name = getattr(llm, 'model', None)
        for model_id, spec in get_available_models():
            if spec.model_path == model_name and spec.backend == ModelBackend.OLLAMA:
                return model_id

    return None


# ============================================================
# Testing and Examples
# ============================================================

if __name__ == "__main__":
    print("=== LLM Factory V2 - Multi-Model Support ===\n")

    # Test 1: Create specific model
    print("Test 1: Creating Phi-3 model...")
    try:
        llm_phi3 = create_llm_from_model_id("phi3-mini")
        print(f"✓ Created: {get_llm_type(llm_phi3)}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n" + "="*50 + "\n")

    # Test 2: Create TinyLlama
    print("Test 2: Creating TinyLlama model...")
    try:
        llm_tiny = create_llm_from_model_id("tinyllama")
        print(f"✓ Created: {get_llm_type(llm_tiny)}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n" + "="*50 + "\n")

    # Test 3: Create Ollama fallback
    print("Test 3: Creating Ollama fallback...")
    try:
        llm_ollama = create_llm_from_model_id("llama3.1-8b")
        print(f"✓ Created: {get_llm_type(llm_ollama)}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n" + "="*50 + "\n")

    # Test 4: List all available models
    print("Test 4: Available models:")
    for model_spec in get_available_models():
        print(f"  - {model_spec.id}: {model_spec.name} ({model_spec.parameters})")
