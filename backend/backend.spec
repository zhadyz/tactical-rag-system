# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Tactical RAG Backend
Bundles FastAPI + RAG Engine + Dependencies into standalone executable

Target: Tauri v4.0 sidecar integration
Size: ~300MB (CPU-only PyTorch, no CUDA)
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# ============================================================================
# Build Configuration
# ============================================================================
block_cipher = None
BACKEND_DIR = Path(os.path.dirname(os.path.abspath(SPEC)))
ROOT_DIR = BACKEND_DIR.parent
SRC_DIR = ROOT_DIR / "_src"

# ============================================================================
# Hidden Imports - CRITICAL FOR BUNDLE SUCCESS
# ============================================================================
# These imports are dynamically loaded and PyInstaller can't detect them

hidden_imports = [
    # FastAPI & Uvicorn
    'uvicorn',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.routing',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'pydantic',
    'pydantic_core',
    'pydantic_settings',
    'python_multipart',
    'slowapi',

    # LangChain Ecosystem (Core)
    'langchain',
    'langchain_core',
    'langchain_core.prompts',
    'langchain_core.output_parsers',
    'langchain_core.runnables',
    'langchain_core.messages',
    'langchain_core.chat_history',
    'langchain_core.documents',
    'langchain_core.vectorstores',
    'langchain_core.embeddings',
    'langchain_core.language_models',
    'langchain_core.retrievers',
    'langchain_core.callbacks',

    # LangChain Community & Integrations
    'langchain_community',
    'langchain_community.vectorstores',
    'langchain_community.vectorstores.chroma',
    'langchain_community.embeddings',
    'langchain_community.embeddings.huggingface',
    'langchain_community.retrievers',
    'langchain_ollama',
    'langchain_ollama.llms',
    'langchain_ollama.embeddings',
    'langchain_text_splitters',
    'langchain_text_splitters.character',
    'langchain_text_splitters.recursive',

    # ChromaDB (Embedded Mode)
    'chromadb',
    'chromadb.api',
    'chromadb.api.types',
    'chromadb.config',
    'chromadb.db',
    'chromadb.db.impl',
    'chromadb.db.impl.sqlite',
    'chromadb.utils',
    'chromadb.utils.embedding_functions',
    'chromadb.server',
    'chromadb.server.fastapi',

    # Sentence Transformers & HuggingFace
    'sentence_transformers',
    'transformers',
    'transformers.models',
    'transformers.models.bert',
    'transformers.models.xlm_roberta',
    'transformers.models.auto',
    'transformers.tokenization_utils',
    'transformers.tokenization_utils_base',
    'tokenizers',
    'tokenizers.implementations',
    'tokenizers.models',
    'tokenizers.pre_tokenizers',
    'tokenizers.decoders',
    'tokenizers.processors',
    'huggingface_hub',
    'huggingface_hub.file_download',
    'huggingface_hub.hf_api',

    # PyTorch (CPU-only)
    'torch',
    'torch._C',
    'torch._inductor',
    'torch.nn',
    'torch.nn.functional',
    'torch.optim',
    'torch.utils',
    'torch.utils.data',

    # Document Processing
    'pypdf',
    'pypdf._reader',
    'pypdf._writer',
    'docx2txt',
    'docx',
    'docx.document',
    'docx.oxml',
    'docx.parts',
    'docx.text',
    'unstructured',
    'markdown',
    'markdown.extensions',

    # OCR (if used)
    'pdf2image',
    'pytesseract',
    'PIL',
    'PIL.Image',

    # BM25 & Retrieval
    'rank_bm25',
    'sklearn',
    'sklearn.feature_extraction',
    'sklearn.feature_extraction.text',
    'sklearn.metrics',
    'sklearn.metrics.pairwise',

    # Scientific Computing
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'numpy.random',

    # Redis (optional - can be disabled for desktop)
    'redis',
    'redis.asyncio',

    # Utilities
    'psutil',
    'yaml',
    'yaml.loader',
    'yaml.dumper',
    'python_json_logger',
    'logging',
    'logging.handlers',
    'asyncio',
    'concurrent',
    'concurrent.futures',

    # HTTP Clients
    'httpx',
    'httpx._transports',
    'httpx._transports.default',
    'requests',
    'urllib3',

    # Custom Modules (_src)
    'config',
    'document_processor',
    'conversation_memory',
    'cache_next_gen',
    'collection_metadata',
    'embedding_cache',
    'llm_factory_v2',
    'model_registry',
    'adaptive_retrieval',
    'rank_fusion',
    'query_expansion',
]

# Collect all submodules for critical packages
hidden_imports += collect_submodules('uvicorn')
hidden_imports += collect_submodules('fastapi')
hidden_imports += collect_submodules('langchain_core')
hidden_imports += collect_submodules('langchain_community')
hidden_imports += collect_submodules('chromadb')
hidden_imports += collect_submodules('sentence_transformers')
hidden_imports += collect_submodules('transformers')

# ============================================================================
# Data Files - Bundle Non-Python Assets
# ============================================================================
datas = []

# Config file (CRITICAL - RAG engine needs this)
datas.append((str(ROOT_DIR / 'config.yml'), '.'))

# ChromaDB data files (if pre-indexed)
# Note: For desktop, we'll use embedded mode and create DB on first run
# datas.append((str(ROOT_DIR / 'chroma_db'), 'chroma_db'))

# HuggingFace model cache (optional - models will download on first run)
# To bundle pre-downloaded models, uncomment:
# datas.append((os.path.expanduser('~/.cache/huggingface'), '.cache/huggingface'))

# Sentence Transformers data
datas += collect_data_files('sentence_transformers')
datas += collect_data_files('transformers')
datas += collect_data_files('tokenizers')
datas += collect_data_files('chromadb')

# ============================================================================
# Binary Dependencies
# ============================================================================
binaries = []

# SQLite3 (required by ChromaDB)
# PyInstaller should auto-detect, but we can add explicitly if needed

# ============================================================================
# Analysis - Scan for Dependencies
# ============================================================================
a = Analysis(
    [str(BACKEND_DIR / 'app' / 'main.py')],  # Entry point
    pathex=[
        str(BACKEND_DIR),
        str(BACKEND_DIR / 'app'),
        str(SRC_DIR),  # Add _src to path
        str(ROOT_DIR),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude GUI libraries we don't need
        'tkinter',
        'matplotlib',
        'PIL.ImageQt',
        'PyQt5',
        'PySide2',

        # Exclude CUDA/GPU libraries (CPU-only build)
        'torch.cuda',
        'torch.backends.cuda',
        'torch.distributed',
        'torch.utils.tensorboard',

        # Exclude test frameworks
        'pytest',
        'unittest',
        'nose',

        # Exclude development tools
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# PYZ - Python Archive
# ============================================================================
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ============================================================================
# EXE - Executable Bundle
# ============================================================================
exe = EXE(
    pyz,
    a.scripts,
    [],  # Empty - we're using COLLECT for one-folder mode
    exclude_binaries=True,
    name='tactical-rag-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Don't strip symbols (helps with debugging)
    upx=False,  # Don't use UPX compression (can cause issues)
    console=True,  # Console app (for logging)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add icon later
)

# ============================================================================
# COLLECT - Bundle All Files into Directory
# ============================================================================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='tactical-rag-backend',
)

# ============================================================================
# Build Instructions
# ============================================================================
"""
To build this spec file:

1. Install PyInstaller:
   pip install pyinstaller

2. Run the build:
   cd V3.5/backend
   pyinstaller backend.spec

3. Output location:
   V3.5/backend/dist/tactical-rag-backend/

4. Test the binary:
   cd dist/tactical-rag-backend
   ./tactical-rag-backend.exe

5. Expected size: ~300MB (CPU-only PyTorch)

6. For Tauri integration:
   - Copy dist/tactical-rag-backend/ to V4.0-Tauri/src-tauri/binaries/
   - Update tauri.conf.json with sidecar configuration
   - Tauri will auto-start/stop this binary

Common Issues:
--------------
1. ModuleNotFoundError: Add missing module to hidden_imports
2. File not found errors: Add missing data files to datas
3. Large size (>500MB): Check for CUDA libraries in excludes
4. Slow startup: Normal for first run (model downloads)

Production Optimization:
------------------------
1. Bundle pre-downloaded HuggingFace models (saves ~2GB download)
2. Use CPU-optimized PyTorch build (smaller size)
3. Enable UPX compression (saves ~30% size, may trigger antivirus)
4. Strip debug symbols (saves ~10% size)
"""
