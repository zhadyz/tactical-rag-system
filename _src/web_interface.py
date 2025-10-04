
import gradio as gr
import asyncio
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RAGWebInterface:
    """Gradio web interface without memory leaks"""
    
    def __init__(self, rag_system, performance_monitor):
        self.rag_system = rag_system
        self.monitor = performance_monitor
    
    def create_interface(self):
        """Create interface with proper event handling"""
        
        custom_css = """
        .gradio-container {
            max-width: 1600px !important;
            margin: 0 auto !important;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 12px;
            text-align: center;
        }
        .monitor-panel {
            background: #1a1a2e;
            padding: 20px;
            border-radius: 12px;
            margin-top: 10px;
        }
        .chatbot {
            overflow-y: auto !important;
        }
        """
        
        example_questions = self.rag_system.example_questions if self.rag_system else [
            "What are the main requirements?",
            "Can you summarize the key policies?"
        ]
        
        with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="Enterprise RAG") as demo:
            
            gr.Markdown("# Enterprise RAG System\n### AI-Powered Document Intelligence with Real-Time Performance Monitoring")
            
            with gr.Row():
                # Left column - System Status & Monitoring
                with gr.Column(scale=2):
                    status_display = gr.HTML(self._get_status_html())
                    
                    gr.Markdown("### Real-Time Performance")
                    
                    with gr.Row():
                        gpu_gauge = gr.HTML(self._create_gauge("GPU", 0, "gpu"))
                        cpu_gauge = gr.HTML(self._create_gauge("CPU", 0, "cpu"))
                        mem_gauge = gr.HTML(self._create_gauge("VRAM", 0, "mem"))
                    
                    with gr.Row():
                        gpu_util_text = gr.Textbox(
                            value="GPU: 0%",
                            label="GPU Utilization",
                            interactive=False,
                            elem_classes="metric-card"
                        )
                        vram_text = gr.Textbox(
                            value="VRAM: 0 MB",
                            label="VRAM Usage",
                            interactive=False,
                            elem_classes="metric-card"
                        )
                    
                    activity_log = gr.Textbox(
                        value="System idle...",
                        label="Activity Monitor",
                        lines=4,
                        interactive=False,
                        elem_classes="monitor-panel"
                    )
                    
                    # Refresh button for manual updates
                    refresh_btn = gr.Button("Refresh Metrics", size="sm", variant="secondary")
                
                # Right column - Chat Interface
                with gr.Column(scale=3):
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
            
            # Settings Panel
            with gr.Accordion("Advanced Settings", open=False):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**Retrieval Settings**")
                        simple_k = gr.Slider(1, 10, value=5, step=1, label="Simple K")
                        hybrid_k = gr.Slider(5, 40, value=20, step=5, label="Hybrid K")
                        advanced_k = gr.Slider(5, 30, value=15, step=5, label="Advanced K")
                    
                    with gr.Column():
                        gr.Markdown("**Scoring Weights**")
                        rerank_weight = gr.Slider(0, 1, value=0.7, step=0.1, label="Rerank Weight")
                        rrf_constant = gr.Slider(10, 100, value=60, step=10, label="RRF Constant")
                    
                    with gr.Column():
                        gr.Markdown("**Query Classification**")
                        simple_thresh = gr.Slider(0, 5, value=1, step=1, label="Simple Threshold")
                        moderate_thresh = gr.Slider(1, 8, value=3, step=1, label="Moderate Threshold")
                
                with gr.Row():
                    apply_settings_btn = gr.Button("Apply Settings", variant="primary")
                    reset_settings_btn = gr.Button("Reset to Defaults", variant="secondary")
                
                settings_status = gr.Markdown("Ready")
            
            # Event Handlers
            
            async def respond_with_monitoring(message, history):
                """Process query and update monitoring"""
                if not message.strip():
                    return history, "", "No query to process", "GPU: 0%", "VRAM: 0 MB"
                
                activity_msg = f"Processing: {message[:50]}..."
                
                # Process query
                bot_message = await self._process_query(message, history)
                
                # Update history
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": bot_message})
                
                # Get metrics
                metrics = self.monitor.get_current_metrics()
                gpu_text = f"GPU: {metrics['gpu_util']}%"
                vram_text = f"VRAM: {metrics['gpu_mem_used']} MB"
                activity_msg = f"Completed | GPU: {metrics['gpu_util']}% | VRAM: {metrics['gpu_mem_used']}MB"
                
                return history, "", activity_msg, gpu_text, vram_text
            
            def update_metrics_once():
                """Single metric update"""
                metrics = self.monitor.get_current_metrics()
                
                gpu_gauge_html = self._create_gauge("GPU", metrics['gpu_util'], "gpu")
                cpu_gauge_html = self._create_gauge("CPU", int(metrics['cpu_util']), "cpu")
                
                vram_pct = 0
                if metrics['gpu_mem_total'] > 0:
                    vram_pct = int((metrics['gpu_mem_used'] / metrics['gpu_mem_total']) * 100)
                mem_gauge_html = self._create_gauge("VRAM", vram_pct, "mem")
                
                gpu_text = f"GPU: {metrics['gpu_util']}%"
                vram_text = f"VRAM: {metrics['gpu_mem_used']} MB"
                
                return (
                    gpu_gauge_html,
                    cpu_gauge_html,
                    mem_gauge_html,
                    gpu_text,
                    vram_text
                )
            
            # Chat interactions
            msg.submit(
                respond_with_monitoring,
                [msg, chatbot],
                [chatbot, msg, activity_log, gpu_util_text, vram_text]
            )
            submit.click(
                respond_with_monitoring,
                [msg, chatbot],
                [chatbot, msg, activity_log, gpu_util_text, vram_text]
            )
            clear.click(lambda: None, None, chatbot, queue=False)
            
            # Settings interactions
            apply_settings_btn.click(
                self._update_settings,
                inputs=[simple_k, hybrid_k, advanced_k, rerank_weight, rrf_constant, simple_thresh, moderate_thresh],
                outputs=[settings_status]
            )
            
            reset_settings_btn.click(
                self._reset_settings,
                outputs=[settings_status, simple_k, hybrid_k, advanced_k, rerank_weight, rrf_constant, simple_thresh, moderate_thresh]
            )
            
            # Manual refresh button
            refresh_btn.click(
                update_metrics_once,
                outputs=[gpu_gauge, cpu_gauge, mem_gauge, gpu_util_text, vram_text]
            )
            
            # Initial load - metrics update on page load
            demo.load(
                update_metrics_once,
                outputs=[gpu_gauge, cpu_gauge, mem_gauge, gpu_util_text, vram_text]
            )
            
            # Status update on page load
            demo.load(
                self._get_status_html,
                outputs=status_display
            )
        
        return demo
    
    def _create_gauge(self, label: str, value: int, gauge_type: str) -> str:
        """Create circular gauge HTML"""
        
        if gauge_type == "gpu":
            color = "#f5576c" if value > 50 else "#667eea"
        elif gauge_type == "cpu":
            color = "#00f2fe" if value > 50 else "#4facfe"
        else:  # mem
            color = "#f093fb" if value > 70 else "#667eea"
        
        return f"""
        <div style="text-align: center; padding: 10px;">
            <div style="position: relative; width: 120px; height: 120px; margin: 0 auto;">
                <svg width="120" height="120" style="transform: rotate(-90deg);">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#e0e0e0" stroke-width="10"/>
                    <circle cx="60" cy="60" r="50" fill="none" stroke="{color}" stroke-width="10"
                            stroke-dasharray="{int(314 * value / 100)} 314"
                            style="transition: stroke-dasharray 0.3s ease;"/>
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                            font-size: 24px; font-weight: bold; color: {color};">
                    {value}%
                </div>
            </div>
            <div style="margin-top: 8px; font-size: 14px; color: #666; font-weight: 500;">
                {label}
            </div>
        </div>
        """
    
    def _get_status_html(self) -> str:
        """Get system status HTML"""
        if not self.rag_system:
            return "<div style='padding:20px;background:#2d3748;color:#fc8181;border-radius:8px;'>System not initialized</div>"
        
        status = self.rag_system.get_system_status()
        
        badge_color = "#48bb78" if status['status'] == 'operational' else "#f56565"
        badge_text = "ONLINE" if status['status'] == 'operational' else "OFFLINE"
        
        return f"""
        <div style="background:#1a1a2e;padding:20px;border-radius:8px;color:#e2e8f0;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h3 style="margin:0;font-size:18px;font-weight:600;">System Status</h3>
                <span style="background:{badge_color};padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;color:white;">{badge_text}</span>
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
                Latency: {status['avg_latency']:.2f}s | Cache: {status['cache_hit_rate']:.0%} | {status['config']['model']}
            </div>
        </div>
        """
    
    async def _process_query(self, message: str, history: List) -> str:
        """Process query through RAG system"""
        if not self.rag_system or not self.rag_system.initialized:
            return "System not initialized. Please restart."
        
        if not message.strip():
            return "Please enter a question."
        
        result = await self.rag_system.query(message)
        
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
    
    def _update_settings(self, simple_k, hybrid_k, advanced_k, rerank_weight, rrf_constant, simple_thresh, moderate_thresh):
        """Update RAG settings"""
        if not self.rag_system:
            return "System not initialized"
        
        self.rag_system.update_settings(
            simple_k=simple_k,
            hybrid_k=hybrid_k,
            advanced_k=advanced_k,
            rerank_weight=rerank_weight,
            rrf_constant=rrf_constant,
            simple_threshold=simple_thresh,
            moderate_threshold=moderate_thresh
        )
        
        return "Settings updated successfully"
    
    def _reset_settings(self):
        """Reset settings to defaults"""
        if not self.rag_system:
            return ("System not initialized",) + (None,) * 7
        
        defaults = self.rag_system.reset_settings()
        
        return (
            "Settings reset to defaults",
            defaults['simple_k'],
            defaults['hybrid_k'],
            defaults['advanced_k'],
            defaults['rerank_weight'],
            defaults['rrf_constant'],
            defaults['simple_threshold'],
            defaults['moderate_threshold']
        )