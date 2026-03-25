"""
Forge - Hotswappable Model Manager

Adapted from _src/model_manager.py with minimal changes.
The hotswap logic is solid; this just cleans the interface and uses
Forge imports.
"""

import logging
import asyncio
import gc
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """Model configuration profile."""
    id: str
    name: str
    backend: str  # "llamacpp" or "ollama"
    description: str
    model_path: Optional[str] = None
    n_gpu_layers: Optional[int] = None
    n_ctx: Optional[int] = None
    n_batch: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    ollama_model: Optional[str] = None
    expected_vram_gb: float = 0.0
    expected_tokens_per_sec: float = 0.0


class ModelManager:
    """
    Manages hotswappable LLM models with runtime switching,
    VRAM cleanup, and automatic fallback.
    """

    PROFILES: Dict[str, ModelProfile] = {
        "qwen-14b-q8": ModelProfile(
            id="qwen-14b-q8",
            name="Qwen 2.5 14B (Q8)",
            backend="llamacpp",
            description="High-quality reasoning, ~14GB VRAM",
            model_path="/models/qwen2.5-14b-instruct-q8_0.gguf",
            n_gpu_layers=40,
            n_ctx=8192,
            n_batch=512,
            expected_vram_gb=14.0,
            expected_tokens_per_sec=25.0,
        ),
        "llama-8b-q5": ModelProfile(
            id="llama-8b-q5",
            name="Llama 3.1 8B (Q5)",
            backend="llamacpp",
            description="Fast inference, ~6GB VRAM",
            model_path="/models/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf",
            n_gpu_layers=40,
            n_ctx=8192,
            n_batch=512,
            expected_vram_gb=6.0,
            expected_tokens_per_sec=90.0,
        ),
        "ollama": ModelProfile(
            id="ollama",
            name="Ollama (Flexible)",
            backend="ollama",
            description="HTTP-based, any Ollama model",
            ollama_model="qwen2.5:14b-instruct-q4_K_M",
            expected_vram_gb=9.0,
            expected_tokens_per_sec=10.0,
        ),
    }

    def __init__(self, config):
        self.config = config
        self.current_model_id: Optional[str] = None
        self.current_llm = None
        self.current_engine = None
        self.switching = False
        self.initialized = False

    async def initialize(self, default_model_id: str = "llama-8b-q5") -> bool:
        logger.info(f"ModelManager initializing with default: {default_model_id}")
        ok = await self.switch_model(default_model_id)
        if ok:
            self.initialized = True
        return ok

    async def switch_model(self, model_id: str) -> bool:
        if self.switching:
            logger.warning("Switch already in progress")
            return False
        if model_id not in self.PROFILES:
            logger.error(f"Unknown model: {model_id}")
            return False
        if self.current_model_id == model_id:
            return True

        profile = self.PROFILES[model_id]
        self.switching = True

        try:
            if self.current_llm or self.current_engine:
                await self._unload()
            await self._cleanup_vram()

            if profile.backend == "llamacpp":
                ok = await self._load_llamacpp(profile)
            elif profile.backend == "ollama":
                ok = await self._load_ollama(profile)
            else:
                ok = False

            if ok:
                self.current_model_id = model_id
                logger.info(f"Model switched to {profile.name}")
            return ok
        except Exception as e:
            logger.error(f"Switch error: {e}", exc_info=True)
            return False
        finally:
            self.switching = False

    async def _load_llamacpp(self, profile: ModelProfile) -> bool:
        try:
            from forge.infrastructure.llm import LlamaCppEngine, LlamaCppLangChainAdapter

            path = Path(profile.model_path)
            if not path.exists():
                logger.error(f"Model not found: {path}")
                return False

            # Build a minimal config-like object
            @dataclass
            class _Cfg:
                model_path: str = str(path)
                n_gpu_layers: int = profile.n_gpu_layers or 33
                n_ctx: int = profile.n_ctx or 8192
                n_batch: int = profile.n_batch or 512
                n_threads: int = 8
                use_mlock: bool = True
                use_mmap: bool = True
                temperature: float = profile.temperature
                top_p: float = 0.9
                top_k: int = 40
                repeat_penalty: float = 1.1
                max_tokens: int = profile.max_tokens
                verbose: bool = False
                draft_model_path: Optional[str] = None
                enable_speculative_decoding: bool = False
                n_gpu_layers_draft: int = 33
                num_draft: int = 5

            cfg = _Cfg()
            self.current_engine = LlamaCppEngine(cfg)
            ok = await self.current_engine.initialize()
            if not ok:
                return False
            self.current_llm = LlamaCppLangChainAdapter(self.current_engine, cfg)
            return True
        except Exception as e:
            logger.error(f"llama.cpp load failed: {e}", exc_info=True)
            return False

    async def _load_ollama(self, profile: ModelProfile) -> bool:
        try:
            from langchain_ollama import OllamaLLM
            self.current_llm = OllamaLLM(
                model=profile.ollama_model,
                base_url=self.config.ollama_host,
                temperature=profile.temperature,
                num_ctx=profile.n_ctx or 8192,
                timeout=120,
            )
            await asyncio.to_thread(self.current_llm.invoke, "Hello")
            return True
        except Exception as e:
            logger.error(f"Ollama load failed: {e}", exc_info=True)
            return False

    async def _unload(self):
        if self.current_engine and hasattr(self.current_engine, "cleanup"):
            await self.current_engine.cleanup()
        self.current_engine = None
        self.current_llm = None

    async def _cleanup_vram(self):
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        await asyncio.sleep(0.3)

    def get_llm(self):
        return self.current_llm

    def get_current_model(self) -> Optional[Dict]:
        if not self.current_model_id:
            return None
        p = self.PROFILES[self.current_model_id]
        return {"id": p.id, "name": p.name, "backend": p.backend, "description": p.description}

    def get_available_models(self) -> List[Dict]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "backend": p.backend,
                "description": p.description,
                "active": p.id == self.current_model_id,
            }
            for p in self.PROFILES.values()
        ]

    def is_switching(self) -> bool:
        return self.switching
