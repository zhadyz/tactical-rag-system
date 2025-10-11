"""
Enterprise RAG System - Main Application
Production-ready with dynamic settings UI and GPU acceleration
"""

import asyncio
import gradio as gr
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from datetime import datetime
import os
import torch  # ADDED: For CUDA verification

from langchain_chroma import Chroma
from langchain_community.llms import Ollama as OllamaLLM
from langchain_community.embeddings import OllamaEmbeddings
from langchain.docstore.document import Document
from langchain_community.retrievers import BM25Retriever

from config import SystemConfig, load_config
from adaptive_retrieval import AdaptiveRetriever, AdaptiveAnswerGenerator, RetrievalResult
from document_processor import DocumentProcessor, ProcessingResult
from cache_and_monitoring import CacheManager, PerformanceMonitor, Timer
from example_generator import ExampleGenerator
from conversation_memory import ConversationMemory

os.makedirs('logs', exist_ok=True)
os.makedirs('.cache', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rag_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnterpriseRAGSystem:
    """Complete enterprise RAG system with dynamic settings and GPU acceleration"""
    
    # Default settings as class constants for safety
    DEFAULT_SETTINGS = {
        'simple_k': 5,
        'hybrid_k': 20,
        'advanced_k': 15,
        'rerank_weight': 0.7,
        'simple_threshold': 1,
        'moderate_threshold': 3,
        'rrf_constant': 60
    }
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.vectorstore: Optional[Chroma] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.retrieval_engine: Optional[AdaptiveRetriever] = None
        self.answer_generator: Optional[AdaptiveAnswerGenerator] = None
        self.llm: Optional[OllamaLLM] = None
        self.cache_manager: Optional[CacheManager] = None
        self.monitor: Optional[PerformanceMonitor] = None
        self.conversation_memory: Optional[ConversationMemory] = None
        self.initialized = False

        # Runtime settings that can be changed via UI
        self.runtime_settings = self.DEFAULT_SETTINGS.copy()
        
        # Example questions (will be generated dynamically)
        self.example_questions = [
            "What are the main requirements?",
            "Can you summarize the key policies?",
            "What procedures should I follow?",
            "What are the standards mentioned?"
        ]
        
        # ADDED: Track GPU availability
        self.gpu_available = torch.cuda.is_available()
        if self.gpu_available:
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("No GPU detected - will use CPU (slower performance)")
        
        logger.info("Enterprise RAG System created")
    
    def update_settings(self, **kwargs):
        """Update runtime settings with validation"""
        for key, value in kwargs.items():
            if key in self.DEFAULT_SETTINGS:
                # Validate ranges
                if key.endswith('_k'):
                    value = max(1, min(50, int(value)))  # K between 1-50
                elif key.endswith('_weight'):
                    value = max(0.0, min(1.0, float(value)))  # Weight 0-1
                elif key.endswith('_threshold'):
                    value = max(0, min(10, int(value)))  # Threshold 0-10
                elif key == 'rrf_constant':
                    value = max(1, min(100, int(value)))  # RRF 1-100
                
                self.runtime_settings[key] = value
                logger.info(f"Setting updated: {key} = {value}")
        
        # Update retrieval engine if it exists
        if self.retrieval_engine:
            self.retrieval_engine.runtime_settings = self.runtime_settings
    
    def reset_settings(self):
        """Reset to default settings"""
        self.runtime_settings = self.DEFAULT_SETTINGS.copy()
        if self.retrieval_engine:
            self.retrieval_engine.runtime_settings = self.runtime_settings
        logger.info("Settings reset to defaults")
        return self.runtime_settings
    
    async def initialize(self) -> Tuple[bool, str]:
        """Initialize the RAG system with GPU acceleration"""
        
        try:
            logger.info("=" * 60)
            logger.info("INITIALIZING ENTERPRISE RAG SYSTEM")
            logger.info("=" * 60)
            
            # ADDED: Log GPU status at initialization
            if self.gpu_available:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"\n🎮 GPU Configuration:")
                logger.info(f"  Device: {gpu_name}")
                logger.info(f"  VRAM: {gpu_mem:.1f}GB")
                logger.info(f"  CUDA Version: {torch.version.cuda}")
            else:
                logger.warning("\n⚠️  No GPU available - using CPU")
            
            logger.info("\n1. Initializing infrastructure...")
            self.cache_manager = CacheManager(self.config)
            self.monitor = PerformanceMonitor(self.config, self.cache_manager)
            
            logger.info("\n2. Connecting to embedding model...")
            embeddings = OllamaEmbeddings(
                model=self.config.embedding.model_name,
                base_url=self.config.ollama_host
            )
            
            test_embed = await asyncio.to_thread(embeddings.embed_query, "test")
            logger.info(f"✓ Embedding model ready (dim: {len(test_embed)})")
            
            logger.info("\n3. Loading vector database...")
            if not self.config.vector_db_dir.exists():
                return False, "Vector database not found. Please run indexing first."
            
            self.vectorstore = Chroma(
                persist_directory=str(self.config.vector_db_dir),
                embedding_function=embeddings
            )
            logger.info("✓ Vector store loaded")
            
            logger.info("\n4. Loading BM25 retriever...")
            metadata_file = self.config.vector_db_dir / "chunk_metadata.json"
            
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    texts = data['texts']
                    metadata = data['metadata']
                
                bm25_docs = [
                    Document(page_content=text, metadata=meta)
                    for text, meta in zip(texts, metadata)
                ]
                self.bm25_retriever = BM25Retriever.from_documents(bm25_docs)
                self.bm25_retriever.k = self.config.retrieval.initial_k
                logger.info(f"✓ BM25 retriever ready ({len(texts)} chunks)")
            else:
                logger.warning("⚠  BM25 metadata not found")
                self.bm25_retriever = BM25Retriever.from_documents([
                    Document(page_content="dummy")
                ])
            
            logger.info("\n5. Connecting to LLM...")
            
            # ADDED: Configure Ollama with GPU settings
            llm_params = {
                'model': self.config.llm.model_name,
                'temperature': self.config.llm.temperature,
                'top_p': self.config.llm.top_p,
                'top_k': self.config.llm.top_k,
                'num_ctx': self.config.llm.num_ctx,
                'repeat_penalty': self.config.llm.repeat_penalty,
                'base_url': self.config.ollama_host
            }
            
            # ADDED: Enable GPU for Ollama if available
            if self.gpu_available:
                llm_params['num_gpu'] = 1  # Use 1 GPU
                logger.info("  Enabling GPU acceleration for Ollama")
            
            self.llm = OllamaLLM(**llm_params)

            await asyncio.to_thread(self.llm.invoke, "Hello")
            logger.info("✓ LLM ready")

            logger.info("\n6. Initializing conversation memory...")
            self.conversation_memory = ConversationMemory(
                llm=self.llm,
                max_exchanges=10,
                summarization_threshold=5,
                enable_summarization=True
            )
            logger.info("✓ Conversation memory ready")

            logger.info("\n7. Initializing adaptive retrieval engine...")
            self.retrieval_engine = AdaptiveRetriever(
                vectorstore=self.vectorstore,
                bm25_retriever=self.bm25_retriever,
                llm=self.llm,
                config=self.config,
                runtime_settings=self.runtime_settings
            )
            self.answer_generator = AdaptiveAnswerGenerator(self.llm)
            logger.info("✓ Adaptive retrieval engine ready")

            logger.info("\n8. Generating example questions...")
            example_gen = ExampleGenerator(self.config, self.llm)
            self.example_questions = await example_gen.generate_examples(
                self.vectorstore,
                num_examples=4
            )
            logger.info(f"✓ Generated {len(self.example_questions)} examples")
            
            self.initialized = True
            
            logger.info("\n" + "=" * 60)
            logger.info("SYSTEM READY")
            logger.info("=" * 60)
            
            # ADDED: Final GPU status
            if self.gpu_available:
                gpu_mem_used = torch.cuda.memory_allocated(0) / 1024**2
                logger.info(f"GPU Memory in use: {gpu_mem_used:.1f}MB")
            
            return True, "System initialized successfully"
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False, f"Initialization failed: {str(e)}"
    
    async def query(self, question: str, use_context: bool = True) -> Dict:
        """Process query with multi-turn conversation memory"""

        if not self.initialized:
            return {
                "answer": "System not initialized",
                "sources": [],
                "error": True
            }

        start_time = asyncio.get_event_loop().time()

        try:
            # Use conversation memory for context-aware query enhancement
            enhanced_query = question
            if use_context and self.conversation_memory:
                enhanced_query, _ = self.conversation_memory.get_relevant_context_for_query(
                    question,
                    max_exchanges=3
                )

            cached_result = self.cache_manager.get_query_result(
                enhanced_query,
                {"model": self.config.llm.model_name}
            )

            if cached_result:
                logger.info(f"Cache hit for query: {question[:50]}...")
                self.monitor.metrics.increment_counter("cache_hits")
                return cached_result

            with Timer(self.monitor.metrics, "retrieval_total"):
                retrieval_result = await self.retrieval_engine.retrieve(enhanced_query)

            if not retrieval_result.documents:
                return {
                    "answer": "I couldn't find any relevant documents to answer your question.",
                    "sources": [],
                    "metadata": {
                        "strategy_used": retrieval_result.strategy_used,
                        "query_type": retrieval_result.query_type
                    }
                }

            with Timer(self.monitor.metrics, "generation"):
                answer = await self.answer_generator.generate(
                    question,
                    retrieval_result
                )

            result = {
                "answer": answer,
                "sources": self._format_sources(retrieval_result),
                "metadata": {
                    "strategy_used": retrieval_result.strategy_used,
                    "query_type": retrieval_result.query_type
                },
                "error": False
            }

            # Store exchange in conversation memory
            if self.conversation_memory:
                self.conversation_memory.add(
                    query=question,
                    response=answer,
                    retrieved_docs=retrieval_result.documents,
                    query_type=retrieval_result.query_type,
                    strategy_used=retrieval_result.strategy_used
                )

            self.cache_manager.put_query_result(
                enhanced_query,
                {"model": self.config.llm.model_name},
                result
            )

            elapsed = asyncio.get_event_loop().time() - start_time
            self.monitor.metrics.record_query(elapsed, success=True)

            return result

        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)

            elapsed = asyncio.get_event_loop().time() - start_time
            self.monitor.metrics.record_query(elapsed, success=False)

            return {
                "answer": f"An error occurred: {str(e)}",
                "sources": [],
                "error": True
            }
    
    def _format_sources(self, retrieval_result: RetrievalResult) -> List[Dict]:
        """Format source information"""
        
        sources = []
        seen_files = set()
        
        for doc, score in zip(
            retrieval_result.documents,
            retrieval_result.scores
        ):
            file_name = doc.metadata.get('file_name', 'Unknown')
            
            if file_name in seen_files:
                continue
            
            seen_files.add(file_name)
            
            sources.append({
                "file_name": file_name,
                "file_type": doc.metadata.get('file_type', 'unknown'),
                "relevance_score": float(score),
                "excerpt": doc.page_content[:250] + "...",
                "metadata": {
                    k: v for k, v in doc.metadata.items()
                    if k in ['page_number', 'chunk_index']
                }
            })
        
        return sources
    
    def get_system_status(self) -> Dict:
        """Get current system status including GPU info"""
        
        if not self.initialized:
            return {
                "status": "offline",
                "message": "System not initialized"
            }
        
        stats = self.monitor.get_system_stats()
        
        doc_count = 0
        chunk_count = 0
        
        if self.config.documents_dir.exists():
            supported_ext = ['.txt', '.pdf', '.docx', '.doc', '.md']
            doc_count = sum(
                1 for f in self.config.documents_dir.rglob('*')
                if f.suffix.lower() in supported_ext
            )
        
        metadata_file = self.config.vector_db_dir / "chunk_metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                chunk_count = len(data.get('texts', []))
        
        # ADDED: GPU status
        gpu_status = "Disabled"
        gpu_memory = 0
        if self.gpu_available:
            gpu_status = f"Enabled ({torch.cuda.get_device_name(0)})"
            gpu_memory = torch.cuda.memory_allocated(0) / 1024**2  # MB

        # Conversation memory stats
        conversation_stats = {}
        if self.conversation_memory:
            conversation_stats = self.conversation_memory.get_stats()

        return {
            "status": "operational",
            "documents": doc_count,
            "chunks": chunk_count,
            "uptime": stats['uptime_formatted'],
            "queries_processed": stats['metrics']['query_count'],
            "avg_latency": stats['metrics']['avg_latency'],
            "cache_hit_rate": stats['cache'].get('query_cache', {}).get('hit_rate', 0),
            "conversation": conversation_stats,
            "config": {
                "model": self.config.llm.model_name,
                "embedding": self.config.embedding.model_name,
                "gpu": gpu_status,  # ADDED
                "gpu_memory_mb": int(gpu_memory)  # ADDED
            }
        }

    def clear_conversation(self) -> None:
        """Clear conversation memory"""
        if self.conversation_memory:
            self.conversation_memory.clear()
            logger.info("Conversation memory cleared")


rag_system: Optional[EnterpriseRAGSystem] = None


async def initialize_system():
    global rag_system
    config = load_config()
    rag_system = EnterpriseRAGSystem(config)
    success, message = await rag_system.initialize()
    return success, message


async def process_query(message: str, history: List) -> str:
    global rag_system
    
    if not rag_system or not rag_system.initialized:
        return "System not initialized. Please restart."
    
    if not message.strip():
        return "Please enter a question."
    
    result = await rag_system.query(message)
    
    if result.get("error"):
        return f"Error: {result['answer']}"
    
    response = f"{result['answer']}\n\n"
    
    if result.get("sources"):
        response += "---\n\n**Sources:**\n\n"
        
        for i, source in enumerate(result['sources'], 1):
            relevance_pct = source['relevance_score'] * 100
            response += f"{i}. **{source['file_name']}** ({relevance_pct:.0f}% relevant)\n"
            
            if source.get('metadata'):
                meta_parts = [f"{k}: {v}" for k, v in source['metadata'].items()]
                if meta_parts:
                    response += f"   *{' | '.join(meta_parts)}*\n"
            
            response += f"   \"{source['excerpt']}\"\n\n"
    
    if result.get("metadata"):
        response += f"\n*Query Type: {result['metadata'].get('query_type', 'unknown').title()} | "
        response += f"Strategy: {result['metadata'].get('strategy_used', 'unknown')}*"
    
    return response


def get_status_html() -> str:
    global rag_system
    
    if not rag_system:
        return "<div style='padding:20px;background:#2d3748;color:#fc8181;border-radius:8px;'>System not initialized</div>"
    
    status = rag_system.get_system_status()
    
    if status['status'] == 'offline':
        badge = "background:#f56565"
        text = "OFFLINE"
    else:
        badge = "background:#48bb78"
        text = "ONLINE"
    
    # ADDED: GPU badge
    gpu_badge = ""
    if status['config'].get('gpu', 'Disabled') != 'Disabled':
        gpu_badge = f"<span style='background:#805ad5;padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;color:white;margin-left:8px;'>GPU</span>"
    
    return f"""
    <div style="background:#1a202c;padding:20px;border-radius:8px;color:#e2e8f0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h3 style="margin:0;font-size:18px;font-weight:600;">Enterprise RAG System</h3>
            <div>
                <span style="{badge};padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;color:white;">{text}</span>
                {gpu_badge}
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px;">
            <div style="background:#2d3748;padding:12px;border-radius:6px;">
                <div style="font-size:10px;color:#a0aec0;text-transform:uppercase;margin-bottom:4px;">Documents</div>
                <div style="font-size:24px;font-weight:700;color:#63b3ed;">{status['documents']}</div>
            </div>
            <div style="background:#2d3748;padding:12px;border-radius:6px;">
                <div style="font-size:10px;color:#a0aec0;text-transform:uppercase;margin-bottom:4px;">Chunks</div>
                <div style="font-size:24px;font-weight:700;color:#48bb78;">{status['chunks']}</div>
            </div>
            <div style="background:#2d3748;padding:12px;border-radius:6px;">
                <div style="font-size:10px;color:#a0aec0;text-transform:uppercase;margin-bottom:4px;">Queries</div>
                <div style="font-size:24px;font-weight:700;color:#ed8936;">{status['queries_processed']}</div>
            </div>
        </div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid #4a5568;font-size:11px;color:#a0aec0;">
            Latency: {status['avg_latency']:.2f}s | Cache: {status['cache_hit_rate']:.0%} | {status['config']['model']} | {status['config']['gpu']}
        </div>
    </div>
    """


def get_current_settings() -> str:
    """Display current settings"""
    global rag_system
    
    if not rag_system:
        return "System not initialized"
    
    settings = rag_system.runtime_settings
    
    return f"""**Current Settings:**
- Simple K: {settings['simple_k']}
- Hybrid K: {settings['hybrid_k']}
- Advanced K: {settings['advanced_k']}
- Rerank Weight: {settings['rerank_weight']:.1f}
- RRF Constant: {settings['rrf_constant']}
- Simple Threshold: {settings['simple_threshold']}
- Moderate Threshold: {settings['moderate_threshold']}"""


def update_all_settings(simple_k, hybrid_k, advanced_k, rerank_weight, 
                        rrf_constant, simple_thresh, moderate_thresh):
    """Update all settings from sliders"""
    global rag_system
    
    if not rag_system:
        return "System not initialized", get_current_settings()
    
    rag_system.update_settings(
        simple_k=simple_k,
        hybrid_k=hybrid_k,
        advanced_k=advanced_k,
        rerank_weight=rerank_weight,
        rrf_constant=rrf_constant,
        simple_threshold=simple_thresh,
        moderate_threshold=moderate_thresh
    )
    
    return "✓ Settings updated successfully", get_current_settings()


def reset_to_defaults():
    """Reset all settings to defaults"""
    global rag_system
    
    if not rag_system:
        return "System not initialized", get_current_settings(), *[None]*7
    
    defaults = rag_system.reset_settings()
    
    return (
        "✓ Settings reset to defaults",
        get_current_settings(),
        defaults['simple_k'],
        defaults['hybrid_k'],
        defaults['advanced_k'],
        defaults['rerank_weight'],
        defaults['rrf_constant'],
        defaults['simple_threshold'],
        defaults['moderate_threshold']
    )


def load_preset(preset_name):
    """Load preset configurations"""
    global rag_system
    
    presets = {
        "⚡ Fast & Simple": {
            'simple_k': 3,
            'hybrid_k': 10,
            'advanced_k': 8,
            'rerank_weight': 0.5,
            'rrf_constant': 60,
            'simple_threshold': 2,
            'moderate_threshold': 4
        },
        "🎯 Balanced (Default)": {
            'simple_k': 5,
            'hybrid_k': 20,
            'advanced_k': 15,
            'rerank_weight': 0.7,
            'rrf_constant': 60,
            'simple_threshold': 1,
            'moderate_threshold': 3
        },
        "🔬 Deep Research": {
            'simple_k': 7,
            'hybrid_k': 30,
            'advanced_k': 20,
            'rerank_weight': 0.8,
            'rrf_constant': 60,
            'simple_threshold': 0,
            'moderate_threshold': 2
        }
    }
    
    if not rag_system or preset_name not in presets:
        return "Invalid preset", get_current_settings(), *[None]*7
    
    preset = presets[preset_name]
    rag_system.update_settings(**preset)
    
    return (
        f"✓ Loaded preset: {preset_name}",
        get_current_settings(),
        preset['simple_k'],
        preset['hybrid_k'],
        preset['advanced_k'],
        preset['rerank_weight'],
        preset['rrf_constant'],
        preset['simple_threshold'],
        preset['moderate_threshold']
    )


def create_interface():
    custom_css = """
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
    }
    .contain {
        max-width: 1400px;
        margin: 0 auto;
    }
    .settings-box {
        background: #2d3748;
        color: #e2e8f0;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #4a5568;
    }
    /* Fix double scroller during generation */
    .chatbot {
        overflow-y: auto !important;
    }
    .chatbot > div {
        overflow: visible !important;
    }
    """
    
    # Get example questions
    global rag_system
    example_questions = rag_system.example_questions if rag_system else [
        "What are the main requirements?",
        "Can you summarize the key policies?"
    ]
    
    with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="Enterprise RAG") as demo:
        
        gr.Markdown("# Enterprise RAG System\n### AI-Powered Document Intelligence with Dynamic Settings")
        
        status_display = gr.HTML(get_status_html())
        
        with gr.Row():
            # Left column - Chat interface
            with gr.Column(scale=5):
                chatbot = gr.Chatbot(
                    height=500,
                    show_label=False,
                    type='messages',
                    container=True
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask about your documents...",
                        show_label=False,
                        scale=9,
                        container=False,
                        lines=1,
                        max_lines=10
                    )
                    submit = gr.Button("Send", scale=1, variant="primary")
                
                gr.Examples(
                    examples=example_questions,
                    inputs=msg
                )
                
                clear = gr.Button("Clear Chat", size="sm", variant="secondary")
                
                # Current settings and guide in two columns
                gr.Markdown("---")
                with gr.Row():
                    with gr.Column(scale=1):
                        current_settings_display = gr.Markdown(
                            get_current_settings(),
                            elem_classes="settings-box"
                        )
                    with gr.Column(scale=1):
                        gr.Markdown("""
### 📖 Guide

**Query Types:**
- **Simple**: Direct facts (who, when, where)
- **Moderate**: Lists, what/how questions
- **Complex**: Analysis, comparisons, why

**Tips:**
- Lower K = faster, fewer sources
- Higher rerank weight = better accuracy
- Adjust thresholds to control routing
""", elem_classes="settings-box")
            
            # Right column - Settings panel
            with gr.Column(scale=3):
                gr.Markdown("### ⚙️ Retrieval Settings")
                
                # Preset selector
                with gr.Group():
                    preset_dropdown = gr.Dropdown(
                        choices=["⚡ Fast & Simple", "🎯 Balanced (Default)", "🔬 Deep Research"],
                        label="Quick Presets",
                        value="🎯 Balanced (Default)"
                    )
                    preset_info = gr.Markdown("""
**⚡ Fast:** Quick responses, fewer sources
**🎯 Balanced:** Good mix of speed & thoroughness  
**🔬 Deep:** Comprehensive, more sources
""")
                
                gr.Markdown("---")
                
                # K values
                gr.Markdown("**📊 Number of Results (K)**")
                simple_k_slider = gr.Slider(
                    minimum=1, maximum=10, value=5, step=1,
                    label="Simple Queries",
                    info="Fast lookups for direct questions"
                )
                
                hybrid_k_slider = gr.Slider(
                    minimum=5, maximum=40, value=20, step=5,
                    label="Hybrid Queries",
                    info="Combined dense + sparse retrieval"
                )
                
                advanced_k_slider = gr.Slider(
                    minimum=5, maximum=30, value=15, step=5,
                    label="Advanced Queries",
                    info="Multi-query expansion"
                )
                
                gr.Markdown("---")
                
                # Scoring weights
                gr.Markdown("**⚖️ Scoring Weights**")
                rerank_weight_slider = gr.Slider(
                    minimum=0.0, maximum=1.0, value=0.7, step=0.1,
                    label="Reranker Weight",
                    info="Higher = trust reranker more (vs RRF)"
                )
                
                rrf_constant_slider = gr.Slider(
                    minimum=10, maximum=100, value=60, step=10,
                    label="RRF Constant",
                    info="Reciprocal Rank Fusion parameter"
                )
                
                gr.Markdown("---")
                
                # Classification thresholds
                gr.Markdown("**🎯 Query Classification**")
                simple_thresh_slider = gr.Slider(
                    minimum=0, maximum=5, value=1, step=1,
                    label="Simple Threshold",
                    info="Max score for simple queries"
                )
                
                moderate_thresh_slider = gr.Slider(
                    minimum=1, maximum=8, value=3, step=1,
                    label="Moderate Threshold",
                    info="Max score for moderate queries"
                )
                
                gr.Markdown("---")
                
                # Action buttons
                with gr.Row():
                    apply_btn = gr.Button("✓ Apply Settings", variant="primary")
                    reset_btn = gr.Button("↺ Reset Defaults", variant="secondary")
                
                # Status message (compact, stays on right)
                settings_status = gr.Markdown("Ready", elem_classes="settings-box")
        
        # Event handlers
        async def respond(message, history):
            if not message.strip():
                return history, ""
            
            bot_message = await process_query(message, history)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": bot_message})
            return history, ""
        
        # Chat interactions
        def clear_chat():
            """Clear chat and conversation memory"""
            global rag_system
            if rag_system:
                rag_system.clear_conversation()
            return None

        msg.submit(respond, [msg, chatbot], [chatbot, msg])
        submit.click(respond, [msg, chatbot], [chatbot, msg])
        clear.click(clear_chat, None, chatbot, queue=False)
        
        # Settings interactions
        all_sliders = [
            simple_k_slider, hybrid_k_slider, advanced_k_slider,
            rerank_weight_slider, rrf_constant_slider,
            simple_thresh_slider, moderate_thresh_slider
        ]
        
        apply_btn.click(
            update_all_settings,
            inputs=all_sliders,
            outputs=[settings_status, current_settings_display]
        )
        
        reset_btn.click(
            reset_to_defaults,
            inputs=[],
            outputs=[settings_status, current_settings_display] + all_sliders
        )
        
        preset_dropdown.change(
            load_preset,
            inputs=[preset_dropdown],
            outputs=[settings_status, current_settings_display] + all_sliders
        )
        
        # Auto-refresh status on load
        demo.load(get_status_html, None, status_display)
    
    return demo


async def main():
    logger.info("Starting Enterprise RAG System...")
    
    success, message = await initialize_system()
    
    if not success:
        logger.error(f"Initialization failed: {message}")
        return
    
    logger.info("System initialized successfully")
    
    demo = create_interface()
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    asyncio.run(main())