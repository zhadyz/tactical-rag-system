"""
ATLAS Protocol - LLM Factory

Creates LLM instances based on configuration.
Supports both Ollama HTTP (legacy) and llama.cpp direct (optimized).

Performance Comparison:
- Ollama: 8-12 tok/s (HTTP overhead + abstraction layers)
- llama.cpp: 80-100 tok/s (direct GPU inference)

Architecture Decision:
- Feature flag llm_backend controls which engine to use
- Seamless fallback to Ollama if llama.cpp fails
- Both engines expose compatible stream() interface
"""

import logging
from pathlib import Path
from typing import Optional, Union
from config import SystemConfig

logger = logging.getLogger(__name__)


def create_llm(config: SystemConfig, test_connection: bool = False):
    """
    Create LLM instance based on configuration.

    Args:
        config: SystemConfig with llm_backend setting
        test_connection: Whether to test the connection

    Returns:
        LLM instance (OllamaLLM or LlamaCppEngine wrapper)
    """
    backend = config.llm_backend.lower()

    if backend == "llamacpp":
        logger.info("Creating llama.cpp LLM engine (direct inference)")
        return _create_llamacpp_llm(config, test_connection)
    elif backend == "ollama":
        logger.info("Creating Ollama LLM client (HTTP-based)")
        return _create_ollama_llm(config, test_connection)
    else:
        logger.warning(f"Unknown LLM backend '{backend}', defaulting to Ollama")
        return _create_ollama_llm(config, test_connection)


def _create_llamacpp_llm(config: SystemConfig, test_connection: bool = False):
    """
    Create llama.cpp LLM engine with LangChain-compatible interface.

    Returns:
        LlamaCppWrapper with stream() method
    """
    try:
        import asyncio
        from llm_engine_llamacpp import create_llamacpp_engine, LlamaCppEngine, LlamaCppConfig

        # Create engine configuration
        engine_config = LlamaCppConfig(
            model_path=config.llamacpp.model_path,
            n_gpu_layers=config.llamacpp.n_gpu_layers,
            n_ctx=config.llamacpp.n_ctx,
            n_batch=config.llamacpp.n_batch,
            n_threads=config.llamacpp.n_threads,
            use_mlock=config.llamacpp.use_mlock,
            use_mmap=config.llamacpp.use_mmap,
            temperature=config.llamacpp.temperature,
            top_p=config.llamacpp.top_p,
            top_k=config.llamacpp.top_k,
            repeat_penalty=config.llamacpp.repeat_penalty,
            max_tokens=config.llamacpp.max_tokens,
            verbose=config.llamacpp.verbose
        )

        # Create engine instance
        llm_engine = create_llamacpp_engine(
            model_path=config.llamacpp.model_path,
            n_gpu_layers=config.llamacpp.n_gpu_layers,
            n_ctx=config.llamacpp.n_ctx,
            temperature=config.llamacpp.temperature,
            n_batch=config.llamacpp.n_batch,
            n_threads=config.llamacpp.n_threads,
            use_mlock=config.llamacpp.use_mlock,
            use_mmap=config.llamacpp.use_mmap,
            top_p=config.llamacpp.top_p,
            top_k=config.llamacpp.top_k,
            repeat_penalty=config.llamacpp.repeat_penalty,
            max_tokens=config.llamacpp.max_tokens,
            verbose=config.llamacpp.verbose
        )

        # Initialize the engine (CRITICAL: Must be done before use)
        logger.info("Initializing llama.cpp engine...")
        init_success = asyncio.run(llm_engine.initialize())

        if not init_success:
            raise RuntimeError("Failed to initialize llama.cpp engine")

        # Test if requested
        if test_connection:
            logger.info("Testing llama.cpp engine...")
            test_response = asyncio.run(llm_engine.generate("Hello", max_tokens=10))
            logger.info(f"llama.cpp test successful: {test_response[:50]}...")

        # Wrap in LangChain-compatible adapter
        return LlamaCppLangChainAdapter(llm_engine, engine_config)

    except Exception as e:
        logger.error(f"Failed to create llama.cpp engine: {e}")
        logger.warning("Falling back to Ollama")
        return _create_ollama_llm(config, test_connection)


def _create_ollama_llm(config: SystemConfig, test_connection: bool = False):
    """
    Create Ollama LLM client (legacy HTTP-based).

    Returns:
        OllamaLLM instance
    """
    try:
        from langchain_ollama import OllamaLLM

        llm = OllamaLLM(
            model=config.llm.model_name,
            base_url=config.ollama_host,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            top_k=config.llm.top_k,
            num_ctx=config.llm.num_ctx,
            repeat_penalty=config.llm.repeat_penalty,
            timeout=config.llm.timeout
        )

        # Test if requested
        if test_connection:
            logger.info("Testing Ollama connection...")
            test_response = llm.invoke("Hello")
            logger.info(f"Ollama test successful: {test_response[:50]}...")

        return llm

    except Exception as e:
        logger.error(f"Failed to create Ollama LLM: {e}")
        raise RuntimeError("No LLM backend available") from e


class LlamaCppLangChainAdapter:
    """
    Adapter to make LlamaCppEngine compatible with LangChain interface.

    Provides:
    - invoke(prompt: str) -> str
    - stream(prompt: str) -> Iterator[str]
    """

    def __init__(self, engine, config):
        """
        Args:
            engine: LlamaCppEngine instance
            config: LlamaCppConfig
        """
        self.engine = engine
        self.config = config
        self.temperature = config.temperature
        self.model = f"llama.cpp:{Path(config.model_path).stem}"

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Synchronous generation (LangChain compatibility).

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        import asyncio
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)

        # llama.cpp engine uses async generate() - wrap for sync call
        return asyncio.run(self.engine.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature
        ))

    def stream(self, prompt: str, **kwargs):
        """
        Streaming generation (LangChain compatibility).

        IMPORTANT: This is a SYNC generator that wraps async streaming.
        For async contexts, use astream() instead.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Yields:
            Generated tokens as strings
        """
        import asyncio
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)

        # Run async stream() in event loop
        async def _async_stream():
            async for token in self.engine.stream(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            ):
                yield token

        # Convert async generator to sync generator
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = _async_stream()
            while True:
                try:
                    token = loop.run_until_complete(async_gen.__anext__())
                    yield token
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Async generation (primary method for async contexts).

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)

        # Direct async call to llama.cpp engine
        return await self.engine.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

    async def ainvoke(self, prompt: str, **kwargs) -> str:
        """
        Async generation (LangChain compatibility alias).

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        # Delegate to generate()
        return await self.generate(prompt, **kwargs)

    async def astream(self, prompt: str, **kwargs):
        """
        Async streaming (for FastAPI SSE compatibility).

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Yields:
            Generated tokens as strings
        """
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)

        # Direct async streaming from llama.cpp engine
        async for token in self.engine.stream(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature
        ):
            yield token

    def __repr__(self):
        return f"LlamaCppAdapter(model={self.model}, temp={self.temperature})"
