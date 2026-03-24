"""
Forge - LLM Factory

Adapted from _src/llm_factory.py + _src/llm_engine_llamacpp.py into a single
clean module.  Keeps the LlamaCppLangChainAdapter for async compatibility and
Ollama as fallback.

Public API:
    create_llm(config: ForgeConfig) -> LLM adapter (invoke / stream / ainvoke / astream)
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Check optional dependency
# ---------------------------------------------------------------------------

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not installed — llama.cpp backend unavailable")


# ---------------------------------------------------------------------------
# Engine (thin wrapper around llama-cpp-python)
# ---------------------------------------------------------------------------

class LlamaCppEngine:
    """Low-level llama.cpp engine with single-thread executor for safety."""

    def __init__(self, config):
        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError("llama-cpp-python is not installed")

        self.config = config
        self.llm: Optional[Llama] = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="llamacpp")
        self._semaphore = asyncio.Semaphore(1)

        # Performance tracking
        self.total_tokens = 0
        self.total_time_ms = 0.0
        self.num_requests = 0

    async def initialize(self) -> bool:
        try:
            def _load():
                params = {
                    "model_path": self.config.model_path,
                    "n_gpu_layers": self.config.n_gpu_layers,
                    "n_ctx": self.config.n_ctx,
                    "n_batch": self.config.n_batch,
                    "n_threads": self.config.n_threads,
                    "use_mlock": self.config.use_mlock,
                    "use_mmap": self.config.use_mmap,
                    "verbose": self.config.verbose,
                    "logits_all": False,
                }
                if self.config.enable_speculative_decoding and self.config.draft_model_path:
                    draft_path = Path(self.config.draft_model_path)
                    if draft_path.exists():
                        params["draft_model"] = Llama(
                            model_path=self.config.draft_model_path,
                            n_gpu_layers=self.config.n_gpu_layers_draft,
                            n_ctx=self.config.n_ctx,
                            verbose=self.config.verbose,
                        )
                        params["num_draft"] = self.config.num_draft
                return Llama(**params)

            loop = asyncio.get_event_loop()
            self.llm = await loop.run_in_executor(self._executor, _load)
            logger.info(f"llama.cpp model loaded: {self.config.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load llama.cpp model: {e}", exc_info=True)
            return False

    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.llm:
            raise RuntimeError("Model not initialized")
        import time

        async with self._semaphore:
            start = time.perf_counter()
            temp = kwargs.get("temperature", self.config.temperature)
            max_tok = kwargs.get("max_tokens", self.config.max_tokens)
            stop = kwargs.get("stop", [])

            def _gen():
                resp = self.llm(
                    prompt,
                    temperature=temp,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repeat_penalty=self.config.repeat_penalty,
                    max_tokens=max_tok,
                    stop=stop,
                    echo=False,
                )
                return resp["choices"][0]["text"]

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, _gen)

            elapsed = (time.perf_counter() - start) * 1000
            tokens = len(result.split())
            self.total_tokens += tokens
            self.total_time_ms += elapsed
            self.num_requests += 1
            return result

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        if not self.llm:
            raise RuntimeError("Model not initialized")

        async with self._semaphore:
            temp = kwargs.get("temperature", self.config.temperature)
            max_tok = kwargs.get("max_tokens", self.config.max_tokens)
            stop = kwargs.get("stop", [])

            def _create_stream():
                return self.llm(
                    prompt,
                    temperature=temp,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repeat_penalty=self.config.repeat_penalty,
                    max_tokens=max_tok,
                    stop=stop,
                    echo=False,
                    stream=True,
                )

            loop = asyncio.get_event_loop()
            stream_iter = await loop.run_in_executor(self._executor, _create_stream)

            for chunk in stream_iter:
                token = chunk["choices"][0]["text"]
                if token:
                    yield token

    async def hot_swap(self, new_model_path: str) -> bool:
        old_llm = self.llm
        old_path = self.config.model_path
        try:
            self.config.model_path = new_model_path
            ok = await self.initialize()
            if ok:
                del old_llm
                return True
            self.config.model_path = old_path
            self.llm = old_llm
            return False
        except Exception:
            self.config.model_path = old_path
            self.llm = old_llm
            return False

    def get_stats(self) -> Dict:
        avg = (self.total_tokens / self.total_time_ms * 1000) if self.total_time_ms else 0
        return {
            "requests": self.num_requests,
            "tokens": self.total_tokens,
            "avg_tok_per_sec": round(avg, 1),
            "model": self.config.model_path,
        }


# ---------------------------------------------------------------------------
# LangChain-compatible adapter (keeps invoke / stream / ainvoke / astream)
# ---------------------------------------------------------------------------

class LlamaCppLangChainAdapter:
    """Wraps LlamaCppEngine with sync+async LangChain interface."""

    def __init__(self, engine: LlamaCppEngine, config):
        self.engine = engine
        self.config = config
        self.temperature = config.temperature
        self.model = f"llama.cpp:{Path(config.model_path).stem}"

    def invoke(self, prompt: str, **kwargs) -> str:
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        return asyncio.run(self.engine.generate(
            prompt, max_tokens=max_tokens, temperature=temperature,
        ))

    def stream(self, prompt: str, **kwargs):
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        loop = asyncio.new_event_loop()
        try:
            async_gen = self.engine.stream(
                prompt, max_tokens=max_tokens, temperature=temperature,
            )
            while True:
                try:
                    token = loop.run_until_complete(async_gen.__anext__())
                    yield token
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    async def generate(self, prompt: str, **kwargs) -> str:
        return await self.engine.generate(prompt, **kwargs)

    async def ainvoke(self, prompt: str, **kwargs) -> str:
        return await self.engine.generate(prompt, **kwargs)

    async def astream(self, prompt: str, **kwargs):
        async for token in self.engine.stream(prompt, **kwargs):
            yield token

    def __repr__(self):
        return f"LlamaCppAdapter(model={self.model})"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_llm(config, test_connection: bool = False):
    """
    Create LLM instance based on ForgeConfig.

    Returns LlamaCppLangChainAdapter or OllamaLLM.
    """
    backend = config.llm_backend.lower()

    if backend == "llamacpp":
        return _create_llamacpp(config, test_connection)
    elif backend == "ollama":
        return _create_ollama(config, test_connection)
    else:
        logger.warning(f"Unknown backend '{backend}', falling back to Ollama")
        return _create_ollama(config, test_connection)


def _create_llamacpp(config, test_connection: bool):
    try:
        engine = LlamaCppEngine(config.llamacpp)
        ok = asyncio.run(engine.initialize())
        if not ok:
            raise RuntimeError("llama.cpp init failed")
        if test_connection:
            asyncio.run(engine.generate("Hello", max_tokens=10))
        return LlamaCppLangChainAdapter(engine, config.llamacpp)
    except Exception as e:
        logger.error(f"llama.cpp failed: {e}, falling back to Ollama")
        return _create_ollama(config, test_connection)


def _create_ollama(config, test_connection: bool):
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
            timeout=config.llm.timeout,
        )
        if test_connection:
            llm.invoke("Hello")
        return llm
    except Exception as e:
        logger.error(f"Ollama failed: {e}")
        raise RuntimeError("No LLM backend available") from e
