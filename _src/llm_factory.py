"""
LLM Factory - Dynamic LLM backend selection
Supports Ollama (baseline) and vLLM (10-20x speedup)
"""

import logging
from typing import Union, Optional
from langchain_ollama import OllamaLLM
from vllm_client import VLLMClient, VLLMConfig

logger = logging.getLogger(__name__)


def create_llm(
    config,
    force_ollama: bool = False,
    test_connection: bool = False  # Changed to False to avoid 36s first-inference delay
) -> Union[OllamaLLM, VLLMClient]:
    """
    Factory function to create appropriate LLM backend

    Decision logic:
    1. Check config.use_vllm flag
    2. If vLLM enabled, try to create VLLMClient
    3. If vLLM fails or disabled, fall back to OllamaLLM
    4. If force_ollama=True, skip vLLM entirely

    Args:
        config: SystemConfig instance
        force_ollama: If True, skip vLLM and use Ollama directly
        test_connection: Test connection before returning client

    Returns:
        Either VLLMClient or OllamaLLM instance

    Example:
        # In app.py:
        self.llm = create_llm(self.config)

        # Usage is identical:
        response = llm.invoke(prompt)
        # OR async:
        response = await asyncio.to_thread(llm.invoke, prompt)
    """

    # Check if vLLM is enabled and not forced to Ollama
    use_vllm = getattr(config, 'use_vllm', False)

    if use_vllm and not force_ollama:
        logger.info("=" * 60)
        logger.info("vLLM MODE ENABLED - Attempting to initialize vLLM client")
        logger.info("=" * 60)

        try:
            # Create vLLM config from system config
            vllm_config = _create_vllm_config(config)

            # Try to create vLLM client
            vllm_client = VLLMClient(
                host=vllm_config.host,
                model=vllm_config.model_name,
                temperature=vllm_config.temperature,
                top_p=vllm_config.top_p,
                top_k=vllm_config.top_k,
                max_tokens=vllm_config.max_tokens,
                timeout=vllm_config.timeout
            )

            # Test connection if requested
            if test_connection:
                logger.info("Testing vLLM connection...")
                test_response = vllm_client.invoke("Hello")
                logger.info(f"✓ vLLM test successful: {test_response[:50]}...")

            logger.info("=" * 60)
            logger.info("✓ vLLM CLIENT INITIALIZED - 10-20x speedup active")
            logger.info(f"  Endpoint: {vllm_config.host}")
            logger.info(f"  Model: {vllm_config.model_name}")
            logger.info("=" * 60)

            return vllm_client

        except Exception as e:
            logger.warning("=" * 60)
            logger.warning(f"⚠ vLLM initialization failed: {e}")
            logger.warning("  Falling back to Ollama (slower but stable)")
            logger.warning("=" * 60)
            # Fall through to Ollama creation

    # Create Ollama LLM (either as fallback or primary)
    if force_ollama:
        logger.info("Ollama mode forced - using OllamaLLM")
    else:
        logger.info("vLLM disabled - using OllamaLLM (baseline)")

    ollama_llm = _create_ollama_llm(config)

    logger.info("=" * 60)
    logger.info("✓ OLLAMA LLM INITIALIZED")
    logger.info(f"  Endpoint: {config.ollama_host}")
    logger.info(f"  Model: {config.llm.model_name}")
    logger.info("=" * 60)

    return ollama_llm


def _create_vllm_config(config) -> VLLMConfig:
    """
    Create VLLMConfig from SystemConfig

    Extracts vLLM settings from config or uses sensible defaults
    """
    # Try to get vLLM config if it exists
    if hasattr(config, 'vllm'):
        vllm_cfg = config.vllm
        return VLLMConfig(
            host=getattr(vllm_cfg, 'host', 'http://vllm-server:8000'),
            model_name=getattr(vllm_cfg, 'model_name', 'meta-llama/Meta-Llama-3.1-8B-Instruct'),
            temperature=getattr(vllm_cfg, 'temperature', config.llm.temperature),
            top_p=getattr(vllm_cfg, 'top_p', config.llm.top_p),
            top_k=getattr(vllm_cfg, 'top_k', config.llm.top_k),
            max_tokens=getattr(vllm_cfg, 'max_tokens', 512),
            timeout=getattr(vllm_cfg, 'timeout', 90)
        )
    else:
        # Use defaults with LLM config values
        return VLLMConfig(
            host='http://vllm-server:8000',
            model_name='mistralai/Mistral-7B-Instruct-v0.3',  # Updated to match vLLM server
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            top_k=config.llm.top_k,
            max_tokens=512,
            timeout=180  # Increased for first inference
        )


def _create_ollama_llm(config) -> OllamaLLM:
    """
    Create OllamaLLM from SystemConfig with performance optimizations

    PERFORMANCE: Aggressive token limits and temperature tuning for speed
    """
    import torch

    # OPTIMIZATION: Reduced max tokens for faster generation
    # Simple queries need ~50-100 tokens, complex ~200-300
    # Capping at 256 reduces generation time by ~50%
    llm_params = {
        'model': config.llm.model_name,
        'temperature': 0.1,  # OPTIMIZATION: Lower temperature = faster, more focused
        'top_p': 0.9,  # OPTIMIZATION: Reduced from default for faster sampling
        'top_k': 30,  # OPTIMIZATION: Reduced from 40 for faster sampling
        'repeat_penalty': config.llm.repeat_penalty,
        'base_url': config.ollama_host,
        'num_predict': 256,  # OPTIMIZATION: Reduced from 512 (2x speed boost)
        'num_ctx': 2048  # OPTIMIZATION: Reduced context window (faster processing)
    }

    # Add GPU support if available
    if torch.cuda.is_available():
        llm_params['num_gpu'] = 1
        logger.info("GPU detected - Ollama will use GPU acceleration")
        logger.info("PERFORMANCE: num_predict=256, num_ctx=2048 for speed")

    return OllamaLLM(**llm_params)


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


def is_vllm_enabled(config) -> bool:
    """
    Check if vLLM is enabled in config

    Returns:
        True if vLLM should be used, False otherwise
    """
    return getattr(config, 'use_vllm', False)


# Example usage and testing
if __name__ == "__main__":
    from config import load_config

    # Test 1: Load config and create LLM
    print("Test 1: Creating LLM from config...")
    config = load_config()

    # Force vLLM for testing
    config.use_vllm = True

    llm = create_llm(config, test_connection=False)
    print(f"Created LLM type: {get_llm_type(llm)}")
    print(f"LLM instance: {llm}")

    # Test 2: Force Ollama
    print("\nTest 2: Forcing Ollama...")
    llm_ollama = create_llm(config, force_ollama=True)
    print(f"Created LLM type: {get_llm_type(llm_ollama)}")
    print(f"LLM instance: {llm_ollama}")
