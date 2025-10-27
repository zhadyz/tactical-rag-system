"""
ATLAS Protocol - Advanced Query Transformation Techniques

Implements state-of-the-art query transformation strategies:
1. HyDE (Hypothetical Document Embeddings)
2. Enhanced Multi-Query Rewriting for Policy Language
3. Query Classification for Adaptive Retrieval

Based on research from LangChain, LlamaIndex, and RAG Techniques.

ASYNC INTEGRATION (v4.0.3-llamacpp):
- All LLM-calling methods are now async for llama.cpp compatibility
- Uses await instead of blocking invoke() calls
- Compatible with FastAPI event loop
"""

import logging
from typing import List, Tuple, Optional
from adaptive_feature_config import QueryType  # Import shared QueryType enum

logger = logging.getLogger(__name__)


class HyDETransform:
    """
    Hypothetical Document Embeddings (HyDE)

    Instead of embedding the raw query, generates a hypothetical answer first,
    then uses that answer's embedding for retrieval. This bridges the semantic
    gap between conversational questions and formal policy language.

    Research Evidence: LlamaIndex query_transformations.ipynb
    Expected Impact: +5-8 points on hard questions with procedural/temporal content
    """

    def __init__(self, llm_service):
        """
        Args:
            llm_service: LLM service for generating hypothetical answers
        """
        self.llm = llm_service

    async def generate_hypothetical_document(self, query: str) -> str:
        """
        Generate a hypothetical answer to the query that would appear in policy documents.

        Args:
            query: Original user question

        Returns:
            Hypothetical answer formatted like policy text
        """
        hyde_prompt = f"""You are an expert on Air Force policies. Given a question, write a hypothetical, detailed answer as it would appear in an official policy document. Use formal language, specific numbers, timeframes, and regulatory terminology.

Question: {query}

Write a comprehensive hypothetical answer (2-3 sentences) that directly addresses this question using policy-appropriate language and specific details:"""

        try:
            # ASYNC FIX: Use await with async LlamaCppEngine
            hypothetical_answer = await self.llm.generate(hyde_prompt)

            logger.info(f"[HyDE] Original query: {query}")
            logger.info(f"[HyDE] Hypothetical document: {hypothetical_answer}")

            return hypothetical_answer

        except Exception as e:
            logger.error(f"[HyDE] Failed to generate hypothetical document: {e}")
            # Fallback to original query
            return query

    async def transform(self, query: str, include_original: bool = True) -> List[str]:
        """
        Transform query using HyDE, optionally including original.

        Args:
            query: Original query
            include_original: Whether to include original query alongside HyDE

        Returns:
            List of queries to use for retrieval (HyDE + optional original)
        """
        hypothetical_doc = await self.generate_hypothetical_document(query)

        if include_original:
            return [hypothetical_doc, query]
        else:
            return [hypothetical_doc]


class PolicyQueryRewriter:
    """
    Enhanced Multi-Query Rewriting for Policy Language

    Generates multiple reformulated versions of queries using policy-specific
    terminology to improve retrieval from formal documents.

    Research Evidence: RAG Techniques query_transformations.ipynb
    Expected Impact: +3-5 points across medium/hard questions
    """

    def __init__(self, llm_service):
        """
        Args:
            llm_service: LLM service for query rewriting
        """
        self.llm = llm_service

    async def rewrite_for_policy_retrieval(self, query: str, num_variants: int = 4) -> List[str]:
        """
        Generate multiple policy-oriented reformulations of the query.

        Args:
            query: Original user question
            num_variants: Number of query variants to generate

        Returns:
            List of reformulated queries
        """
        rewrite_prompt = f"""You are an expert at reformulating questions for searching Air Force policy documents. Given a user's question, generate {num_variants} different reformulations that:

1. Use formal military terminology and regulatory language
2. Include specific keywords likely to appear in policy documents (e.g., "authorized", "entitled", "mandatory", "minimum/maximum", "regulation")
3. Convert conversational phrasing to policy-appropriate phrasing
4. Add context about relevant regulations or programs

Original Question: {query}

Generate {num_variants} reformulated queries, one per line, focusing on different aspects or phrasings that would match official policy text:

1."""

        try:
            # ASYNC FIX: Use await with async LlamaCppEngine
            response = await self.llm.generate(rewrite_prompt)

            # Parse numbered list from response
            lines = response.strip().split('\n')
            variants = []

            for line in lines:
                # Remove numbering and clean up
                cleaned = line.strip()
                if cleaned and len(cleaned) > 10:  # Valid query
                    # Remove leading numbers/bullets
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•']:
                        if cleaned.startswith(prefix):
                            cleaned = cleaned[len(prefix):].strip()
                    if cleaned:
                        variants.append(cleaned)

            # Ensure we have at least 2 variants
            if len(variants) < 2:
                variants.append(query)  # Fallback to original

            # Limit to requested number
            variants = variants[:num_variants]

            logger.info(f"[PolicyRewriter] Original: {query}")
            logger.info(f"[PolicyRewriter] Generated {len(variants)} variants")
            for i, variant in enumerate(variants, 1):
                logger.info(f"[PolicyRewriter] Variant {i}: {variant}")

            return variants

        except Exception as e:
            logger.error(f"[PolicyRewriter] Failed to rewrite query: {e}")
            # Fallback to original query
            return [query]


class QueryClassifier:
    """
    Query Classification for Adaptive Retrieval

    Classifies queries into types (factual, procedural, temporal, etc.) to
    enable adaptive retrieval strategies.

    Research Evidence: RAG Techniques adaptive_retrieval.ipynb
    Expected Impact: +1-2 points on edge cases
    """

    def __init__(self, llm_service):
        """
        Args:
            llm_service: LLM service for classification
        """
        self.llm = llm_service

    async def classify_query(self, query: str) -> QueryType:
        """
        Classify the query into a type for adaptive retrieval.

        Args:
            query: User question

        Returns:
            QueryType enum value
        """
        classification_prompt = f"""Classify the following question into ONE of these categories:

1. FACTUAL - Simple fact lookups (e.g., "How many days of leave?", "What is the passing score?")
2. PROCEDURAL - Process or steps (e.g., "What is the process for...", "How do I...")
3. TEMPORAL - Time-based rules or timelines (e.g., "When can...", "How long...", "What is the timeline...")
4. COMPARATIVE - Comparisons or differences (e.g., "What are the differences between...", "How does X compare to Y...")
5. COMPLEX - Multi-part questions requiring multiple pieces of information

Question: {query}

Classification (respond with just the category name):"""

        try:
            # ASYNC FIX: Use await with async LlamaCppEngine
            response = await self.llm.generate(classification_prompt)
            response = response.strip().upper()

            # Map response to QueryType
            if "FACTUAL" in response:
                query_type = QueryType.FACTUAL
            elif "PROCEDURAL" in response:
                query_type = QueryType.PROCEDURAL
            elif "TEMPORAL" in response:
                query_type = QueryType.TEMPORAL
            elif "COMPARATIVE" in response:
                query_type = QueryType.COMPARATIVE
            else:
                query_type = QueryType.COMPLEX

            logger.info(f"[QueryClassifier] Query: {query}")
            logger.info(f"[QueryClassifier] Type: {query_type.value}")

            return query_type

        except Exception as e:
            logger.error(f"[QueryClassifier] Classification failed: {e}")
            # Default to COMPLEX for safety
            return QueryType.COMPLEX


class QueryTransformationPipeline:
    """
    Orchestrates all query transformation techniques.

    Combines HyDE, multi-query rewriting, and classification for maximum
    retrieval improvement.
    """

    def __init__(self, llm_service, enable_hyde: bool = True,
                 enable_multiquery: bool = True, enable_classification: bool = True):
        """
        Args:
            llm_service: LLM service for transformations
            enable_hyde: Enable HyDE transformation
            enable_multiquery: Enable multi-query rewriting
            enable_classification: Enable query classification
        """
        self.llm = llm_service
        self.enable_hyde = enable_hyde
        self.enable_multiquery = enable_multiquery
        self.enable_classification = enable_classification

        # Initialize components
        if enable_hyde:
            self.hyde = HyDETransform(llm_service)
        if enable_multiquery:
            self.rewriter = PolicyQueryRewriter(llm_service)
        if enable_classification:
            self.classifier = QueryClassifier(llm_service)

    async def transform(self, query: str, use_adaptive: bool = True) -> Tuple[List[str], Optional[QueryType]]:
        """
        Apply query transformations adaptively based on query classification.

        ADAPTIVE MODE (use_adaptive=True, default):
        - Classifies query first
        - Applies features based on query complexity:
          * FACTUAL: Skip HyDE, skip multi-query → ~10s response
          * PROCEDURAL: Use HyDE, 2 variants → ~15s response
          * COMPLEX: All features, 4 variants → ~25s response

        Args:
            query: Original user question
            use_adaptive: Use adaptive feature toggling (default: True for 10-15s speed)

        Returns:
            Tuple of (transformed_queries, query_type)
            - transformed_queries: List of queries to use for retrieval
            - query_type: Classified query type (if classification enabled)
        """
        transformed_queries = []
        query_type = None

        # STEP 1: Classify query first (always do this to enable adaptive mode)
        if self.enable_classification:
            query_type = await self.classifier.classify_query(query)

        # STEP 2: Get adaptive configuration based on query type
        adaptive_config = None
        if use_adaptive and query_type:
            try:
                from adaptive_feature_config import get_adaptive_config
                adaptive_config = get_adaptive_config(query_type)
                logger.info(
                    f"[ADAPTIVE] Query type: {query_type.value}, "
                    f"HyDE={adaptive_config.enable_hyde}, "
                    f"MultiQuery={adaptive_config.enable_multiquery} (variants={adaptive_config.num_query_variants})"
                )
            except Exception as e:
                logger.warning(f"[ADAPTIVE] Failed to load adaptive config, using defaults: {e}")
                adaptive_config = None

        # STEP 3: Apply HyDE (adaptively)
        should_use_hyde = self.enable_hyde
        if adaptive_config:
            should_use_hyde = should_use_hyde and adaptive_config.enable_hyde

        if should_use_hyde:
            hyde_queries = await self.hyde.transform(query, include_original=True)
            transformed_queries.extend(hyde_queries)
            logger.debug(f"[ADAPTIVE] Applied HyDE: {len(hyde_queries)} queries")
        else:
            # Always include original if skipping HyDE
            if not transformed_queries:
                transformed_queries.append(query)
            logger.debug(f"[ADAPTIVE] Skipped HyDE for {query_type.value if query_type else 'unknown'} query")

        # STEP 4: Apply multi-query rewriting (adaptively)
        should_use_multiquery = self.enable_multiquery
        num_variants = 3  # Default
        if adaptive_config:
            should_use_multiquery = should_use_multiquery and adaptive_config.enable_multiquery
            num_variants = adaptive_config.num_query_variants

        if should_use_multiquery and num_variants > 1:
            rewritten_queries = await self.rewriter.rewrite_for_policy_retrieval(query, num_variants=num_variants)
            transformed_queries.extend(rewritten_queries)
            logger.debug(f"[ADAPTIVE] Applied MultiQuery: {num_variants} variants")
        else:
            logger.debug(f"[ADAPTIVE] Skipped MultiQuery for {query_type.value if query_type else 'unknown'} query")

        # If no transformations generated, use original
        if not transformed_queries:
            transformed_queries = [query]

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in transformed_queries:
            q_lower = q.lower().strip()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)

        logger.info(
            f"[TransformPipeline] Generated {len(unique_queries)} unique queries "
            f"(type={query_type.value if query_type else 'unknown'}): {query[:60]}..."
        )

        return unique_queries, query_type
