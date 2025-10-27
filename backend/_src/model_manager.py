"""
ATLAS Protocol - Hotswappable Model Manager

Allows runtime switching between different LLM backends without restart.
Handles VRAM cleanup, model loading/unloading, and state management.

Supported Backends:
- llama.cpp (Qwen 2.5 14B Q8, Llama 3.1 8B Q5, etc.)
- Ollama (any model via HTTP)

Usage:
    manager = ModelManager(config)
    await manager.initialize()
    await manager.switch_model("qwen-14b-q8")
    current = manager.get_current_model()
"""

import logging
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path
import gc

logger = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """Model configuration profile"""
    id: str
    name: str
    backend: str  # "llamacpp" or "ollama"
    description: str

    # llama.cpp specific
    model_path: Optional[str] = None
    n_gpu_layers: Optional[int] = None
    n_ctx: Optional[int] = None
    n_batch: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 512  # TEMPORARY: Reduced from 2048 to test deadlock fix

    # Ollama specific
    ollama_model: Optional[str] = None

    # Performance estimates
    expected_vram_gb: float = 0.0
    expected_tokens_per_sec: float = 0.0


class ModelManager:
    """
    Manages hotswappable LLM models with runtime switching.

    Features:
    - Load/unload models dynamically
    - VRAM cleanup between switches
    - State preservation during transitions
    - Automatic fallback on errors
    """

    # Predefined model profiles
    PROFILES = {
        "qwen-14b-q8": ModelProfile(
            id="qwen-14b-q8",
            name="Qwen 2.5 14B (Q8)",
            backend="llamacpp",
            description="High-quality reasoning, Q8 quantization, ~14GB VRAM",
            model_path="/models/qwen2.5-14b-instruct-q8_0.gguf",
            n_gpu_layers=40,  # Full offload for 14B model
            n_ctx=8192,
            n_batch=512,
            temperature=0.7,
            # max_tokens uses dataclass default (512)
            expected_vram_gb=14.0,
            expected_tokens_per_sec=25.0  # Slower than 8B but still fast with llama.cpp
        ),
        "llama-8b-q5": ModelProfile(
            id="llama-8b-q5",
            name="Llama 3.1 8B (Q5)",
            backend="llamacpp",
            description="Fast inference, Q5 quantization, ~6GB VRAM",
            model_path="/models/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf",
            n_gpu_layers=40,  # QUICK WIN #2: Full GPU offload (35→40 for 10-15% speedup)
            n_ctx=8192,
            n_batch=512,
            temperature=0.7,
            # max_tokens uses dataclass default (512)
            expected_vram_gb=6.0,
            expected_tokens_per_sec=90.0
        ),
        "ollama": ModelProfile(
            id="ollama",
            name="Ollama (Flexible)",
            backend="ollama",
            description="HTTP-based, any Ollama model, ~variable VRAM",
            ollama_model="qwen2.5:14b-instruct-q4_K_M",  # Default
            temperature=0.7,
            # max_tokens uses dataclass default (512)
            expected_vram_gb=9.0,
            expected_tokens_per_sec=10.0
        )
    }

    def __init__(self, config):
        """
        Initialize model manager.

        Args:
            config: SystemConfig instance
        """
        self.config = config
        self.current_model_id: Optional[str] = None
        self.current_llm = None
        self.current_engine = None  # For llama.cpp engine
        self.switching = False
        self.initialized = False

        logger.info("ModelManager initialized")

    async def initialize(self, default_model_id: str = "llama-8b-q5"):
        """
        Initialize with default model.

        Args:
            default_model_id: ID of model to load initially
        """
        logger.info(f"Initializing ModelManager with default: {default_model_id}")

        # Load default model
        success = await self.switch_model(default_model_id)
        if success:
            self.initialized = True
            logger.info(f"✓ ModelManager ready with {default_model_id}")
        else:
            logger.error("Failed to initialize ModelManager")
            raise RuntimeError("ModelManager initialization failed")

        return success

    async def switch_model(self, model_id: str) -> bool:
        """
        Switch to a different model at runtime.

        Args:
            model_id: ID of model profile to switch to

        Returns:
            True if switch successful, False otherwise
        """
        if self.switching:
            logger.warning("Model switch already in progress")
            return False

        if model_id not in self.PROFILES:
            logger.error(f"Unknown model ID: {model_id}")
            return False

        profile = self.PROFILES[model_id]

        # Don't reload if already active
        if self.current_model_id == model_id:
            logger.info(f"Model {model_id} already loaded")
            return True

        self.switching = True

        try:
            logger.info("=" * 60)
            logger.info(f"SWITCHING MODEL: {self.current_model_id} → {model_id}")
            logger.info("=" * 60)

            # Step 1: Unload current model
            if self.current_llm or self.current_engine:
                logger.info("Unloading current model...")
                await self._unload_current_model()
                logger.info("✓ Current model unloaded")

            # Step 2: Force garbage collection and VRAM cleanup
            logger.info("Cleaning up VRAM...")
            await self._cleanup_vram()
            logger.info("✓ VRAM cleanup complete")

            # Step 3: Load new model
            logger.info(f"Loading {profile.name} ({profile.backend})...")

            if profile.backend == "llamacpp":
                success = await self._load_llamacpp_model(profile)
            elif profile.backend == "ollama":
                success = await self._load_ollama_model(profile)
            else:
                logger.error(f"Unknown backend: {profile.backend}")
                success = False

            if success:
                self.current_model_id = model_id
                logger.info("=" * 60)
                logger.info(f"✓ MODEL SWITCH COMPLETE: {profile.name}")
                logger.info(f"  Backend: {profile.backend}")
                logger.info(f"  VRAM: ~{profile.expected_vram_gb}GB")
                logger.info(f"  Expected Speed: ~{profile.expected_tokens_per_sec} tok/s")
                logger.info("=" * 60)
                return True
            else:
                logger.error(f"Failed to load model: {model_id}")
                return False

        except Exception as e:
            logger.error(f"Error during model switch: {e}", exc_info=True)
            return False

        finally:
            self.switching = False

    async def _load_llamacpp_model(self, profile: ModelProfile) -> bool:
        """Load llama.cpp model"""
        try:
            from llm_engine_llamacpp import create_llamacpp_engine, LlamaCppConfig

            # Check model file exists
            model_path = Path(profile.model_path)
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return False

            logger.info(f"  Model file: {model_path}")
            logger.info(f"  Size: {model_path.stat().st_size / 1024**3:.2f} GB")
            logger.info(f"  GPU layers: {profile.n_gpu_layers}")

            # Create engine configuration
            engine_config = LlamaCppConfig(
                model_path=str(model_path),
                n_gpu_layers=profile.n_gpu_layers,
                n_ctx=profile.n_ctx,
                n_batch=profile.n_batch,
                temperature=profile.temperature,
                max_tokens=profile.max_tokens,
                verbose=False
            )

            # Create engine instance
            self.current_engine = create_llamacpp_engine(
                model_path=str(model_path),
                n_gpu_layers=profile.n_gpu_layers,
                n_ctx=profile.n_ctx,
                n_batch=profile.n_batch,
                temperature=profile.temperature,
                max_tokens=profile.max_tokens
            )

            # Initialize engine
            logger.info("  Initializing llama.cpp engine...")
            init_success = await self.current_engine.initialize()

            if not init_success:
                raise RuntimeError("Engine initialization failed")

            # Test generation
            logger.info("  Testing model generation...")
            test_response = await self.current_engine.generate("Hello", max_tokens=5)
            logger.info(f"  Test response: {test_response[:50]}...")

            # Wrap in LangChain adapter
            from llm_factory import LlamaCppLangChainAdapter
            self.current_llm = LlamaCppLangChainAdapter(self.current_engine, engine_config)

            logger.info("✓ llama.cpp model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load llama.cpp model: {e}", exc_info=True)
            return False

    async def _load_ollama_model(self, profile: ModelProfile) -> bool:
        """Load Ollama model"""
        try:
            from langchain_ollama import OllamaLLM

            logger.info(f"  Ollama model: {profile.ollama_model}")
            logger.info(f"  Ollama host: {self.config.ollama_host}")

            self.current_llm = OllamaLLM(
                model=profile.ollama_model,
                base_url=self.config.ollama_host,
                temperature=profile.temperature,
                num_ctx=profile.n_ctx or 8192,
                timeout=120
            )

            # Test connection
            logger.info("  Testing Ollama connection...")
            test_response = await asyncio.to_thread(
                self.current_llm.invoke, "Hello"
            )
            logger.info(f"  Test response: {test_response[:50]}...")

            logger.info("✓ Ollama model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load Ollama model: {e}", exc_info=True)
            return False

    async def _unload_current_model(self):
        """Unload currently loaded model"""
        try:
            # Cleanup llama.cpp engine
            if self.current_engine:
                if hasattr(self.current_engine, 'cleanup'):
                    await self.current_engine.cleanup()
                self.current_engine = None

            # Clear LLM reference
            self.current_llm = None

            logger.info("Model unloaded")

        except Exception as e:
            logger.error(f"Error unloading model: {e}")

    async def _cleanup_vram(self):
        """Force VRAM cleanup"""
        try:
            # Python garbage collection
            gc.collect()

            # CUDA cache cleanup
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    logger.info("  CUDA cache cleared")
            except ImportError:
                pass

            # Brief pause to allow cleanup
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error during VRAM cleanup: {e}")

    def get_current_model(self) -> Optional[Dict]:
        """Get current model info"""
        if not self.current_model_id:
            return None

        profile = self.PROFILES[self.current_model_id]
        return {
            "id": profile.id,
            "name": profile.name,
            "backend": profile.backend,
            "description": profile.description,
            "expected_vram_gb": profile.expected_vram_gb,
            "expected_tokens_per_sec": profile.expected_tokens_per_sec
        }

    def get_available_models(self) -> List[Dict]:
        """Get list of available model profiles"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "backend": p.backend,
                "description": p.description,
                "expected_vram_gb": p.expected_vram_gb,
                "expected_tokens_per_sec": p.expected_tokens_per_sec,
                "active": p.id == self.current_model_id
            }
            for p in self.PROFILES.values()
        ]

    def get_llm(self):
        """Get current LLM instance (for RAG engine)"""
        return self.current_llm

    def is_switching(self) -> bool:
        """Check if model switch is in progress"""
        return self.switching
