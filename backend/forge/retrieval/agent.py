"""
Forge - LangGraph Agentic RAG Orchestrator

The CORE of the Forge rewrite. Implements a LangGraph StateGraph that
drives retrieval decisions through a ReAct-style agent loop:

  analyze_query -> execute_retrieval -> crag_gate -> rerank -> generate -> verify -> finalize

The CRAG gate can loop back to execute_retrieval if too few documents
survive quality evaluation (up to max_iterations).

Also provides a ForgeAgent wrapper with:
  - query()        -> full QueryResponse
  - query_stream() -> AsyncGenerator of StreamEvent dicts
  - Direct mode fast path (single-shot, no agent loop)
"""

import logging
import time
import uuid
from typing import Any, AsyncGenerator, TypedDict

from langgraph.graph import END, StateGraph

from forge.config import ForgeConfig
from forge.retrieval.crag import CRAGEvaluator
from forge.retrieval.reranker import ForgeReranker
from forge.retrieval.verifier import ClaimVerifier
from forge.retrieval.tools import ALL_TOOLS, init_tools
from forge.generation.generator import ForgeGenerator
from forge.generation.confidence import ForgeConfidenceScorer
from forge.generation.streaming import ForgeStreamGenerator
from forge.schemas.query import QueryResponse, Source

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------


class ForgeAgentState(TypedDict, total=False):
    query: str
    sub_queries: list[str]
    messages: list  # LangGraph message accumulator
    retrieved_docs: list[dict]
    crag_results: list[dict]
    approved_docs: list[dict]
    answer: str
    verification: list[dict]
    confidence: float
    steps: list[dict]  # For streaming to frontend
    iteration: int
    should_continue: bool


# ---------------------------------------------------------------------------
# Graph node implementations
# ---------------------------------------------------------------------------


async def analyze_query(state: ForgeAgentState) -> dict:
    """Classify query type, decide decomposition, plan initial tools."""
    query = state["query"]
    steps = list(state.get("steps", []))

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "thinking",
        "content": f"Analyzing query: '{query[:80]}...'",
    })

    # Use LLM to classify query
    container = _agent_container
    sub_queries: list[str] = []

    if container:
        try:
            llm = await container.get_llm()

            classification_prompt = (
                "Classify this question into ONE category and decide if it needs "
                "decomposition.\n\n"
                f"Question: {query}\n\n"
                "Categories: FACTUAL, PROCEDURAL, COMPARATIVE, TEMPORAL, MULTI_HOP, COMPLEX\n\n"
                "If MULTI_HOP or COMPLEX, also list 2-3 sub-questions that would help "
                "answer it, one per line after 'SUB:'\n\n"
                "Format:\nTYPE: <category>\nSUB: <sub-question 1>\nSUB: <sub-question 2>"
            )

            response = await llm.generate(classification_prompt)

            for line in response.strip().split("\n"):
                line = line.strip()
                if line.upper().startswith("SUB:"):
                    sq = line[4:].strip()
                    if sq:
                        sub_queries.append(sq)

        except Exception as e:
            logger.warning(f"[analyze_query] classification failed: {e}")

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "decision",
        "content": (
            f"Sub-queries: {sub_queries}" if sub_queries
            else "Single-query retrieval planned"
        ),
    })

    return {
        "sub_queries": sub_queries,
        "steps": steps,
        "iteration": state.get("iteration", 0),
        "retrieved_docs": state.get("retrieved_docs", []),
        "should_continue": False,
    }


async def execute_retrieval(state: ForgeAgentState) -> dict:
    """ReAct loop: run retrieval tools for the query and sub-queries."""
    query = state["query"]
    sub_queries = state.get("sub_queries", [])
    iteration = state.get("iteration", 0)
    steps = list(state.get("steps", []))
    all_docs: list[dict] = list(state.get("retrieved_docs", []))

    queries_to_run = [query] + sub_queries

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "thinking",
        "content": f"Iteration {iteration + 1}: searching with {len(queries_to_run)} queries",
    })

    # Import tools for direct invocation
    from forge.retrieval.tools import semantic_search, keyword_search

    for q in queries_to_run:
        call_id = f"tc_{uuid.uuid4().hex[:8]}"
        start = time.perf_counter()

        steps.append({
            "id": call_id,
            "type": "tool_call",
            "content": {"tool": "semantic_search", "input": {"query": q[:100], "k": 20}},
        })

        results = await semantic_search.ainvoke({"query": q, "level": "L2", "k": 20})
        elapsed = (time.perf_counter() - start) * 1000

        top_score = max((r.get("score", 0) for r in results), default=0)

        steps.append({
            "id": f"tr_{uuid.uuid4().hex[:8]}",
            "type": "tool_result",
            "content": {
                "tool_call_id": call_id,
                "count": len(results),
                "top_score": top_score,
                "duration_ms": round(elapsed, 1),
            },
        })

        all_docs.extend(results)

        # Also do keyword search for exact-match terms
        kw_id = f"tc_{uuid.uuid4().hex[:8]}"
        kw_start = time.perf_counter()

        steps.append({
            "id": kw_id,
            "type": "tool_call",
            "content": {"tool": "keyword_search", "input": {"query": q[:100], "k": 10}},
        })

        kw_results = await keyword_search.ainvoke({"query": q, "k": 10})
        kw_elapsed = (time.perf_counter() - kw_start) * 1000

        steps.append({
            "id": f"tr_{uuid.uuid4().hex[:8]}",
            "type": "tool_result",
            "content": {
                "tool_call_id": kw_id,
                "count": len(kw_results),
                "top_score": max((r.get("score", 0) for r in kw_results), default=0),
                "duration_ms": round(kw_elapsed, 1),
            },
        })

        all_docs.extend(kw_results)

    # Deduplicate by content hash
    seen: set[str] = set()
    unique_docs: list[dict] = []
    for doc in all_docs:
        key = doc.get("id") or doc.get("content", "")[:200]
        if key not in seen:
            seen.add(key)
            unique_docs.append(doc)

    return {
        "retrieved_docs": unique_docs,
        "steps": steps,
        "iteration": iteration + 1,
    }


async def crag_gate(state: ForgeAgentState) -> dict:
    """CRAG quality gate -- evaluate and filter retrieved documents."""
    query = state["query"]
    docs = state.get("retrieved_docs", [])
    iteration = state.get("iteration", 1)
    steps = list(state.get("steps", []))

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "thinking",
        "content": f"CRAG evaluation on {len(docs)} documents",
    })

    config: ForgeConfig = getattr(_agent_container, "config", None) or ForgeConfig()
    evaluator = CRAGEvaluator(
        model_name=config.crag.reranker_model,
        threshold_correct=config.crag.threshold_correct,
        threshold_ambiguous=config.crag.threshold_ambiguous,
        container=_agent_container,
    )

    crag_results = await evaluator.evaluate(query, docs)

    # Build serialisable CRAG data
    crag_data = [
        {
            "doc_id": r.doc_id,
            "score": r.score,
            "verdict": r.verdict,
        }
        for r in crag_results
    ]

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "observation",
        "content": f"CRAG: {len(crag_results)} docs survived out of {len(docs)}",
    })

    # Decide whether to re-retrieve
    should_continue = len(crag_results) < 2 and iteration < config.agent.max_iterations

    if should_continue:
        steps.append({
            "id": f"step_{uuid.uuid4().hex[:8]}",
            "type": "decision",
            "content": "Too few quality docs, re-retrieving with refined query",
        })

    # Convert CRAG results back to doc dicts for downstream
    approved = [
        {
            "content": r.content,
            "metadata": r.metadata or {},
            "id": r.doc_id,
            "crag_score": r.score,
            "crag_verdict": r.verdict,
        }
        for r in crag_results
    ]

    return {
        "crag_results": crag_data,
        "approved_docs": approved,
        "steps": steps,
        "should_continue": should_continue,
    }


async def rerank(state: ForgeAgentState) -> dict:
    """ColBERT late-interaction reranking on approved docs."""
    approved = state.get("approved_docs", [])
    steps = list(state.get("steps", []))

    config: ForgeConfig = getattr(_agent_container, "config", None) or ForgeConfig()
    reranker = ForgeReranker(
        cross_encoder_model=config.crag.reranker_model,
        container=_agent_container,
    )

    ranked = await reranker.rerank(
        query=state["query"],
        documents=approved,
        k=config.retrieval.final_k,
    )

    ranked_dicts = [
        {
            "content": r.content,
            "metadata": r.metadata,
            "id": r.id,
            "score": r.score,
        }
        for r in ranked
    ]

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "observation",
        "content": f"Reranked to top {len(ranked_dicts)} documents",
    })

    return {
        "approved_docs": ranked_dicts,
        "steps": steps,
    }


async def generate(state: ForgeAgentState) -> dict:
    """Generate answer with explicit source citations."""
    steps = list(state.get("steps", []))
    approved = state.get("approved_docs", [])

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "thinking",
        "content": f"Generating answer from {len(approved)} sources",
    })

    generator = ForgeGenerator(container=_agent_container)

    # Get conversation context if available
    conversation_context = ""
    if _agent_container:
        try:
            memory = await _agent_container.get_memory()
            conversation_context = await memory.get_context() if memory else ""
        except Exception:
            pass

    answer = await generator.generate(
        query=state["query"],
        documents=approved,
        conversation_context=conversation_context,
    )

    return {
        "answer": answer,
        "steps": steps,
    }


async def verify(state: ForgeAgentState) -> dict:
    """Self-verification: check each claim against sources."""
    answer = state.get("answer", "")
    approved = state.get("approved_docs", [])
    steps = list(state.get("steps", []))

    verifier = ClaimVerifier(container=_agent_container)
    results = await verifier.verify(answer, approved)

    verification_data = [
        {
            "claim": r.claim,
            "supported": r.supported,
            "confidence": r.confidence,
            "supporting_sources": r.supporting_sources,
            "explanation": r.explanation,
        }
        for r in results
    ]

    steps.append({
        "id": f"step_{uuid.uuid4().hex[:8]}",
        "type": "observation",
        "content": (
            f"Verified {sum(1 for r in results if r.supported)}/{len(results)} claims"
        ),
    })

    return {
        "verification": verification_data,
        "steps": steps,
    }


async def finalize(state: ForgeAgentState) -> dict:
    """Compute confidence and prepare final response."""
    approved = state.get("approved_docs", [])
    crag_results = state.get("crag_results", [])
    verification = state.get("verification", [])

    retrieval_scores = [d.get("score", 0.0) for d in approved]
    crag_scores = [c.get("score", 0.0) for c in crag_results]

    scorer = ForgeConfidenceScorer()
    result = scorer.calculate(
        query=state["query"],
        answer=state.get("answer", ""),
        documents=approved,
        retrieval_scores=retrieval_scores,
        crag_scores=crag_scores or None,
        verification_results=verification or None,
    )

    return {
        "confidence": result["overall"],
    }


# ---------------------------------------------------------------------------
# Conditional edge
# ---------------------------------------------------------------------------


def should_retry(state: ForgeAgentState) -> str:
    """Decide whether to re-retrieve or proceed to reranking."""
    if state.get("should_continue") and state.get("iteration", 0) < 3:
        return "execute_retrieval"
    return "rerank"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_forge_graph() -> Any:
    """Compile the Forge agentic RAG graph."""
    graph = StateGraph(ForgeAgentState)

    graph.add_node("analyze_query", analyze_query)
    graph.add_node("execute_retrieval", execute_retrieval)
    graph.add_node("crag_gate", crag_gate)
    graph.add_node("rerank", rerank)
    graph.add_node("generate", generate)
    graph.add_node("verify", verify)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("analyze_query")
    graph.add_edge("analyze_query", "execute_retrieval")
    graph.add_edge("execute_retrieval", "crag_gate")
    graph.add_conditional_edges(
        "crag_gate",
        should_retry,
        {
            "execute_retrieval": "execute_retrieval",
            "rerank": "rerank",
        },
    )
    graph.add_edge("rerank", "generate")
    graph.add_edge("generate", "verify")
    graph.add_edge("verify", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Module-level container (set by ForgeAgent.__init__)
# ---------------------------------------------------------------------------

_agent_container = None


# ---------------------------------------------------------------------------
# ForgeAgent wrapper
# ---------------------------------------------------------------------------


class ForgeAgent:
    """
    High-level wrapper around the LangGraph agent.

    Provides:
      - query()        -> QueryResponse (full, non-streaming)
      - query_stream() -> AsyncGenerator of StreamEvent dicts
      - Direct-mode fast path (skip agent loop)
    """

    def __init__(self, container):
        global _agent_container
        _agent_container = container
        self.container = container
        self.config: ForgeConfig = getattr(container, "config", ForgeConfig())
        self.graph = build_forge_graph()
        self.stream_gen = ForgeStreamGenerator()

        # Initialize tools with the container
        init_tools(container)

    # ------------------------------------------------------------------
    # Full query (non-streaming)
    # ------------------------------------------------------------------

    async def query(
        self, question: str, mode: str = "agentic", use_context: bool = True
    ) -> QueryResponse:
        """
        Run a full query and return a QueryResponse.

        Args:
            question: User question.
            mode: "direct" for fast path, "agentic" for full agent loop.
            use_context: Whether to use conversation memory.
        """
        start = time.perf_counter()

        if mode == "direct":
            return await self._direct_query(question, use_context)

        # Run the full agent graph
        initial_state: ForgeAgentState = {
            "query": question,
            "sub_queries": [],
            "messages": [],
            "retrieved_docs": [],
            "crag_results": [],
            "approved_docs": [],
            "answer": "",
            "verification": [],
            "confidence": 0.0,
            "steps": [],
            "iteration": 0,
            "should_continue": False,
        }

        final_state = await self.graph.ainvoke(initial_state)

        elapsed_ms = (time.perf_counter() - start) * 1000

        sources = [
            Source(
                content=d.get("content", ""),
                metadata=d.get("metadata", {}),
                relevance_score=d.get("score", 0.0),
            )
            for d in final_state.get("approved_docs", [])
        ]

        return QueryResponse(
            answer=final_state.get("answer", ""),
            sources=sources,
            metadata={
                "mode": "agentic",
                "confidence": final_state.get("confidence", 0.0),
                "iterations": final_state.get("iteration", 0),
                "total_ms": round(elapsed_ms, 1),
            },
            verification_results=[],  # Convert separately if needed
        )

    # ------------------------------------------------------------------
    # Streaming query
    # ------------------------------------------------------------------

    async def query_stream(
        self, question: str, mode: str = "agentic", use_context: bool = True
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream query events for SSE.

        Yields dicts with {"type": ..., "content": ...} suitable for
        ForgeStreamGenerator.wrap() or direct JSON serialisation.
        """
        start = time.perf_counter()
        E = ForgeStreamGenerator  # shorthand for static builders

        if mode == "direct":
            async for event in self._direct_stream(question, use_context):
                yield event
            return

        yield E.thinking(f"Analyzing query: '{question[:80]}'")

        # Run graph node by node so we can emit events between steps
        initial_state: ForgeAgentState = {
            "query": question,
            "sub_queries": [],
            "messages": [],
            "retrieved_docs": [],
            "crag_results": [],
            "approved_docs": [],
            "answer": "",
            "verification": [],
            "confidence": 0.0,
            "steps": [],
            "iteration": 0,
            "should_continue": False,
        }

        try:
            # Use the compiled graph's stream to get step-by-step output
            async for step_output in self.graph.astream(initial_state):
                # Each step_output is {node_name: state_update}
                for node_name, state_update in step_output.items():
                    # Emit steps added by each node
                    for step in state_update.get("steps", []):
                        step_type = step.get("type", "thinking")
                        if step_type in ("thinking", "decision", "observation"):
                            yield E.thinking(step.get("content", ""))
                        elif step_type == "tool_call":
                            tc = step.get("content", {})
                            yield E.tool_call(
                                step.get("id", ""),
                                tc.get("tool", ""),
                                tc.get("input", {}),
                            )
                        elif step_type == "tool_result":
                            tr = step.get("content", {})
                            yield E.tool_result(
                                step.get("id", ""),
                                tr.get("tool_call_id", ""),
                                count=tr.get("count", 0),
                                top_score=tr.get("top_score", 0),
                                duration_ms=tr.get("duration_ms", 0),
                            )

                    # Emit CRAG evaluation
                    if "crag_results" in state_update and state_update["crag_results"]:
                        yield E.crag_evaluation(state_update["crag_results"])

                    # Emit retrieval_complete after reranking
                    if node_name == "rerank" and "approved_docs" in state_update:
                        yield E.retrieval_complete(
                            total_docs=len(state_update["approved_docs"]),
                            stages=[],
                        )

                    # Stream answer tokens
                    if node_name == "generate" and "answer" in state_update:
                        answer = state_update["answer"]
                        # Emit as tokens (split on whitespace for word-level streaming)
                        words = answer.split(" ")
                        for i, word in enumerate(words):
                            token_text = word if i == 0 else " " + word
                            yield E.token(token_text)

                    # Emit verification
                    if "verification" in state_update and state_update["verification"]:
                        yield E.verification(state_update["verification"])

                    # Emit confidence as metadata
                    if "confidence" in state_update and state_update["confidence"]:
                        elapsed = (time.perf_counter() - start) * 1000
                        yield E.metadata({
                            "confidence": state_update["confidence"],
                            "total_ms": round(elapsed, 1),
                            "mode": "agentic",
                        })

            # Emit sources
            # We need to get the final approved_docs from the last state
            # The graph already completed, so emit sources from the last answer
            yield E.event("sources", [])
            yield E.done()

        except Exception as e:
            logger.error(f"[ForgeAgent] streaming error: {e}", exc_info=True)
            yield E.error(str(e))
            yield E.done()

    # ------------------------------------------------------------------
    # Direct mode (fast path: single-shot retrieval -> rerank -> generate)
    # ------------------------------------------------------------------

    async def _direct_query(
        self, question: str, use_context: bool
    ) -> QueryResponse:
        """Fast path without agent loop."""
        start = time.perf_counter()

        from forge.retrieval.tools import semantic_search

        # Single retrieval
        results = await semantic_search.ainvoke(
            {"query": question, "level": "L2", "k": 20}
        )

        # Rerank
        reranker = ForgeReranker(
            cross_encoder_model=self.config.crag.reranker_model,
            container=self.container,
        )
        ranked = await reranker.rerank(question, results, k=self.config.retrieval.final_k)

        ranked_dicts = [
            {"content": r.content, "metadata": r.metadata, "id": r.id, "score": r.score}
            for r in ranked
        ]

        # Generate
        generator = ForgeGenerator(container=self.container)
        ctx = ""
        if use_context and self.container:
            try:
                memory = await self.container.get_memory()
                ctx = await memory.get_context() if memory else ""
            except Exception:
                pass

        answer = await generator.generate(question, ranked_dicts, ctx)

        elapsed_ms = (time.perf_counter() - start) * 1000

        sources = [
            Source(
                content=d["content"],
                metadata=d["metadata"],
                relevance_score=d.get("score", 0.0),
            )
            for d in ranked_dicts
        ]

        return QueryResponse(
            answer=answer,
            sources=sources,
            metadata={
                "mode": "direct",
                "total_ms": round(elapsed_ms, 1),
            },
        )

    async def _direct_stream(
        self, question: str, use_context: bool
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Streaming fast path."""
        E = ForgeStreamGenerator
        start = time.perf_counter()

        yield E.thinking("Direct mode: retrieving documents")

        from forge.retrieval.tools import semantic_search

        results = await semantic_search.ainvoke(
            {"query": question, "level": "L2", "k": 20}
        )

        yield E.tool_result(
            "tr_direct",
            "tc_direct",
            count=len(results),
            top_score=max((r.get("score", 0) for r in results), default=0),
            duration_ms=0,
        )

        # Rerank
        reranker = ForgeReranker(
            cross_encoder_model=self.config.crag.reranker_model,
            container=self.container,
        )
        ranked = await reranker.rerank(question, results, k=self.config.retrieval.final_k)
        ranked_dicts = [
            {"content": r.content, "metadata": r.metadata, "id": r.id, "score": r.score}
            for r in ranked
        ]

        yield E.retrieval_complete(len(ranked_dicts), [])

        # Stream generation
        generator = ForgeGenerator(container=self.container)
        ctx = ""
        if use_context and self.container:
            try:
                memory = await self.container.get_memory()
                ctx = await memory.get_context() if memory else ""
            except Exception:
                pass

        async for token in generator.generate_stream(question, ranked_dicts, ctx):
            yield E.token(token)

        # Sources
        yield E.sources([
            {
                "content": d["content"][:500],
                "metadata": d["metadata"],
                "relevance_score": d.get("score", 0.0),
            }
            for d in ranked_dicts
        ])

        elapsed_ms = (time.perf_counter() - start) * 1000
        yield E.metadata({
            "mode": "direct",
            "total_ms": round(elapsed_ms, 1),
        })
        yield E.done()
