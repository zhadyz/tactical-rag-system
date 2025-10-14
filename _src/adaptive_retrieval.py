"""
Adaptive Retrieval Engine - Production Version with Dynamic Settings
WITH CUDA GPU ACCELERATION
WITH EXPLAINABILITY
"""

import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging
import numpy as np
import torch  # ADDED: For CUDA detection
import os  # ADDED: For environment variable setting

from langchain.docstore.document import Document
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_community.llms import Ollama as OllamaLLM
from sentence_transformers import CrossEncoder

from explainability import QueryExplanation, create_query_explanation

logger = logging.getLogger(__name__)

# CRITICAL: Force rerankers to use CUDA (prevents silent CPU fallback)
os.environ['DEVICE_TYPE'] = 'cuda'

# Military terminology synonym dictionary for vague query handling
MILITARY_SYNONYMS = {
    # Songs and music
    "song": ["national anthem", "anthem", "To The Color", "music"],
    "music": ["anthem", "national anthem", "song"],

    # Headgear
    "hat": ["headgear", "cover", "cap", "hat"],
    "cap": ["headgear", "cover", "cap"],

    # Facial hair
    "beard": ["beard", "facial hair", "grooming", "shaving"],
    "shave": ["shaving", "facial hair", "beard", "grooming"],
    "shaving": ["shave", "facial hair", "beard", "grooming"],
    "facial hair": ["beard", "grooming", "shaving"],

    # Clothing
    "clothes": ["uniform", "attire", "dress"],
    "clothing": ["uniform", "attire", "dress"],

    # Body modifications
    "tattoo": ["tattoo", "body art", "ink"],
    "tattoos": ["tattoo", "body art", "ink"],

    # Jewelry
    "earring": ["earring", "jewelry", "accessory"],
    "earrings": ["earring", "jewelry", "accessories"],
    "jewelry": ["accessory", "earring", "ornament"],

    # Ceremonies
    "salute": ["saluting", "render honors", "courtesy", "respect"],
    "saluting": ["salute", "render honors", "courtesy"],
}


@dataclass
class RetrievalResult:
    """Retrieval result with proper scoring and explainability"""
    documents: List[Document]
    scores: List[float]
    strategy_used: str
    query_type: str
    explanation: Optional[QueryExplanation] = None


class AdaptiveRetriever:
    """Adaptive retriever with dynamic settings support"""
    
    def __init__(
        self,
        vectorstore: Chroma,
        bm25_retriever: BM25Retriever,
        llm: OllamaLLM,
        config,
        runtime_settings: Dict
    ):
        self.vectorstore = vectorstore
        self.bm25_retriever = bm25_retriever
        self.llm = llm
        self.config = config
        self.runtime_settings = runtime_settings  # Reference to shared settings dict
        
        # Load reranker with CUDA support
        self.reranker = None
        if config.retrieval.rerank_k > 0:
            try:
                # CRITICAL: Detect CUDA and set device explicitly
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                logger.info(f"Initializing reranker on device: {device}")
                
                self.reranker = CrossEncoder(
                    'cross-encoder/ms-marco-MiniLM-L-6-v2',
                    device=device  # ADDED: Explicit device setting
                )
                
                # ADDED: Verify device and log GPU info
                logger.info(f"Reranker device: {self.reranker.model.device}")
                if torch.cuda.is_available():
                    gpu_name = torch.cuda.get_device_name(0)
                    logger.info(f"Reranker using GPU: {gpu_name}")
                else:
                    logger.warning("Reranker using CPU - performance may be slower")
                    
            except Exception as e:
                logger.warning(f"Failed to load reranker: {e}")
    
    def _get_setting(self, key: str, default):
        """Safely get setting with fallback"""
        try:
            return self.runtime_settings.get(key, default)
        except:
            return default

    def _expand_with_synonyms(self, query: str) -> str:
        """
        Expand query with domain-specific military synonyms.
        Handles vague casual language → formal military terminology mapping.
        Zero latency cost.
        """
        words = query.lower().split()
        expanded_terms = set(words)  # Start with original words

        for word in words:
            # Remove punctuation for matching
            clean_word = word.strip('.,!?')
            if clean_word in MILITARY_SYNONYMS:
                # Add top 2 synonyms for this word
                synonyms = MILITARY_SYNONYMS[clean_word][:2]
                expanded_terms.update(synonyms)
                logger.debug(f"Synonym expansion: '{clean_word}' → {synonyms}")

        expanded_query = " ".join(expanded_terms)
        if expanded_query != query.lower():
            logger.info(f"Query expanded: '{query}' → includes terms: {expanded_terms - set(words)}")

        return expanded_query

    async def retrieve(self, query: str) -> RetrievalResult:
        """Adaptive retrieval with dynamic settings and explainability"""

        # Classify query with explanation
        query_type, explanation = self._classify_query(query)
        logger.info(f"Query classified as: {query_type}")
        logger.info(f"Explanation: {explanation.example_text}")

        # Route to appropriate strategy
        if query_type == "simple":
            return await self._simple_retrieval(query, explanation)
        elif query_type == "moderate":
            return await self._hybrid_retrieval(query, explanation)
        else:
            return await self._advanced_retrieval(query, explanation)
    
    def _classify_query(self, query: str) -> Tuple[str, QueryExplanation]:
        """Multi-factor query classification with dynamic thresholds and explainability"""

        query_lower = query.lower()
        words = query.split()
        score = 0
        scoring_breakdown = {}

        # Factor 1: Length
        length_score = 0
        if len(words) <= 6:
            length_score = 0
            scoring_breakdown['length'] = f"{len(words)} words (+0)"
        elif len(words) <= 10:
            length_score = 1
            scoring_breakdown['length'] = f"{len(words)} words (+1)"
        elif len(words) <= 15:
            length_score = 2
            scoring_breakdown['length'] = f"{len(words)} words (+2)"
        else:
            length_score = 3
            scoring_breakdown['length'] = f"{len(words)} words (+3)"
        score += length_score

        # Factor 2: Question type
        simple_starters = ["where", "who", "when", "which", "is there", "does", "can i", "do i"]
        moderate_starters = ["what", "how many", "how much", "list"]
        complex_starters = ["why", "how does", "explain", "analyze", "compare", "evaluate"]

        question_score = 0
        question_type = "other"
        if any(query_lower.startswith(s) for s in simple_starters):
            question_score = 0
            question_type = next(s for s in simple_starters if query_lower.startswith(s))
            scoring_breakdown['question_type'] = f"{question_type} (+0)"
        elif any(query_lower.startswith(s) for s in moderate_starters):
            question_score = 1
            question_type = next(s for s in moderate_starters if query_lower.startswith(s))
            scoring_breakdown['question_type'] = f"{question_type} (+1)"
        elif any(query_lower.startswith(s) for s in complex_starters):
            question_score = 3
            question_type = next(s for s in complex_starters if query_lower.startswith(s))
            scoring_breakdown['question_type'] = f"{question_type} (+3)"
        else:
            scoring_breakdown['question_type'] = "other (+0)"
        score += question_score

        # Factor 3: Complexity indicators
        if " and " in query_lower:
            score += 1
            scoring_breakdown['has_and_operator'] = "yes (+1)"

        if " or " in query_lower:
            score += 1
            scoring_breakdown['has_or_operator'] = "yes (+1)"

        if "?" in query and query.count("?") > 1:
            score += 2
            scoring_breakdown['multiple_questions'] = f"{query.count('?')} questions (+2)"

        # Get dynamic thresholds
        simple_threshold = self._get_setting('simple_threshold', 1)
        moderate_threshold = self._get_setting('moderate_threshold', 3)

        # Classify
        if score <= simple_threshold:
            query_type = "simple"
        elif score <= moderate_threshold:
            query_type = "moderate"
        else:
            query_type = "complex"

        # Create explanation
        explanation = create_query_explanation(
            query=query,
            query_type=query_type,
            complexity_score=score,
            scoring_breakdown=scoring_breakdown,
            simple_threshold=simple_threshold,
            moderate_threshold=moderate_threshold
        )

        return query_type, explanation
    
    async def _simple_retrieval(self, query: str, explanation: QueryExplanation) -> RetrievalResult:
        """Simple retrieval with synonym expansion for vague queries"""

        logger.info(f"SIMPLE retrieval: {query[:60]}...")

        # Expand query with military synonyms (zero latency cost)
        expanded_query = self._expand_with_synonyms(query)

        # Get dynamic K value
        k = self._get_setting('simple_k', 5)

        # Get top K results using expanded query
        results = await asyncio.to_thread(
            self.vectorstore.similarity_search_with_score,
            expanded_query,
            k=k
        )

        if not results:
            return RetrievalResult([], [], "simple_dense", "simple", explanation)

        # Normalize scores properly
        distances = [dist for _, dist in results]
        min_dist = min(distances)
        max_dist = max(distances)
        dist_range = max_dist - min_dist if max_dist != min_dist else 1.0

        # Convert to 0-1 similarity (0 = worst, 1 = best)
        normalized = []
        for doc, dist in results:
            # Normalize distance to 0-1
            norm_dist = (dist - min_dist) / dist_range
            # Invert: lower distance = higher similarity
            similarity = 1.0 - norm_dist
            normalized.append((doc, similarity))

        # Sort by similarity (highest first)
        normalized.sort(key=lambda x: x[1], reverse=True)

        # Take top results (max 3 or all if fewer)
        top_n = min(3, len(normalized))
        documents = [doc for doc, _ in normalized[:top_n]]
        scores = [score for _, score in normalized[:top_n]]

        return RetrievalResult(
            documents=documents,
            scores=scores,
            strategy_used="simple_dense",
            query_type="simple",
            explanation=explanation
        )
    
    async def _hybrid_retrieval(self, query: str, explanation: QueryExplanation) -> RetrievalResult:
        """Hybrid retrieval with RRF fusion, synonym expansion, and dynamic settings"""

        logger.info(f"HYBRID retrieval: {query[:60]}...")

        # Expand query with military synonyms
        expanded_query = self._expand_with_synonyms(query)

        # Get dynamic K value
        k = self._get_setting('hybrid_k', 20)
        rrf_k = self._get_setting('rrf_constant', 60)

        # Parallel retrieval with expanded query
        dense_task = asyncio.to_thread(
            self.vectorstore.similarity_search_with_score,
            expanded_query,
            k=k
        )
        sparse_task = asyncio.to_thread(
            self.bm25_retriever.get_relevant_documents,
            expanded_query
        )
        
        dense_results, sparse_results = await asyncio.gather(
            dense_task, sparse_task, return_exceptions=True
        )
        
        # Handle errors
        if isinstance(dense_results, Exception):
            logger.error(f"Dense retrieval failed: {dense_results}")
            dense_results = []
        if isinstance(sparse_results, Exception):
            logger.error(f"Sparse retrieval failed: {sparse_results}")
            sparse_results = []
        
        # RRF fusion
        doc_scores = {}
        
        # Dense results
        for rank, (doc, _) in enumerate(dense_results):
            content_hash = hash(doc.page_content)
            rrf_score = 1.0 / (rrf_k + rank + 1)
            doc_scores[content_hash] = {
                'doc': doc,
                'score': rrf_score,
                'methods': ['dense']
            }
        
        # Sparse results
        for rank, doc in enumerate(sparse_results[:k]):
            content_hash = hash(doc.page_content)
            rrf_score = 1.0 / (rrf_k + rank + 1)
            
            if content_hash in doc_scores:
                # Sum RRF scores
                doc_scores[content_hash]['score'] += rrf_score
                doc_scores[content_hash]['methods'].append('sparse')
            else:
                doc_scores[content_hash] = {
                    'doc': doc,
                    'score': rrf_score,
                    'methods': ['sparse']
                }
        
        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:15]
        
        # Rerank if available (will use GPU if configured)
        if self.reranker and len(sorted_docs) > 3:
            documents = [item['doc'] for item in sorted_docs]
            pairs = [[query, doc.page_content[:512]] for doc in documents]
            
            try:
                # ADDED: Reranking with GPU acceleration
                logger.info(f"Reranking {len(pairs)} documents on {self.reranker.model.device}")
                
                rerank_scores = await asyncio.to_thread(
                    self.reranker.predict,
                    pairs,
                    batch_size=16  # ADDED: Batch processing for GPU efficiency
                )
                
                # Normalize rerank scores to 0-1
                rerank_scores = list(rerank_scores)
                min_score = min(rerank_scores)
                max_score = max(rerank_scores)
                score_range = max_score - min_score if max_score != min_score else 1.0
                
                norm_rerank = [
                    (s - min_score) / score_range
                    for s in rerank_scores
                ]
                
                # Get dynamic rerank weight
                rerank_weight = self._get_setting('rerank_weight', 0.7)
                fusion_weight = 1.0 - rerank_weight
                
                # Combine: dynamic weight between RRF and reranking
                final_scores = [
                    (item['doc'], fusion_weight * item['score'] + rerank_weight * norm_rerank[i])
                    for i, item in enumerate(sorted_docs)
                ]
                final_scores.sort(key=lambda x: x[1], reverse=True)
                
                documents = [doc for doc, _ in final_scores[:5]]
                scores = [score for _, score in final_scores[:5]]

                return RetrievalResult(
                    documents=documents,
                    scores=scores,
                    strategy_used="hybrid_reranked",
                    query_type="moderate",
                    explanation=explanation
                )
            except Exception as e:
                logger.warning(f"Reranking failed: {e}")
        
        # Fallback without reranking
        documents = [item['doc'] for item in sorted_docs[:5]]
        scores = [item['score'] for item in sorted_docs[:5]]

        return RetrievalResult(
            documents=documents,
            scores=scores,
            strategy_used="hybrid",
            query_type="moderate",
            explanation=explanation
        )
    
    async def _advanced_retrieval(self, query: str, explanation: QueryExplanation) -> RetrievalResult:
        """Advanced retrieval with query expansion and dynamic settings"""

        logger.info(f"ADVANCED retrieval: {query[:60]}...")
        
        # Get dynamic K value
        k = self._get_setting('advanced_k', 15)
        
        # Generate variants
        variants = await self._generate_variants(query)
        all_queries = [query] + variants[:2]  # Original + max 2 variants
        
        logger.info(f"Searching with {len(all_queries)} query variants")
        
        # Multi-query retrieval
        all_results = {}
        
        for q in all_queries:
            try:
                results = await asyncio.to_thread(
                    self.vectorstore.similarity_search_with_score,
                    q,
                    k=k
                )
                
                for doc, _ in results:
                    content_hash = hash(doc.page_content)
                    if content_hash not in all_results:
                        all_results[content_hash] = {'doc': doc, 'count': 0}
                    all_results[content_hash]['count'] += 1
                    
            except Exception as e:
                logger.warning(f"Query variant failed: {e}")
        
        # Sort by how many queries found this doc
        sorted_docs = sorted(
            all_results.values(),
            key=lambda x: x['count'],
            reverse=True
        )[:15]
        
        # Rerank (will use GPU if configured)
        if self.reranker and sorted_docs:
            documents = [item['doc'] for item in sorted_docs]
            pairs = [[query, doc.page_content[:512]] for doc in documents]
            
            try:
                # ADDED: Reranking with GPU acceleration
                logger.info(f"Reranking {len(pairs)} documents on {self.reranker.model.device}")
                
                rerank_scores = await asyncio.to_thread(
                    self.reranker.predict,
                    pairs,
                    batch_size=16  # ADDED: Batch processing for GPU efficiency
                )
                
                # Normalize
                rerank_scores = list(rerank_scores)
                min_score = min(rerank_scores)
                max_score = max(rerank_scores)
                score_range = max_score - min_score if max_score != min_score else 1.0
                
                norm_scores = [
                    (s - min_score) / score_range
                    for s in rerank_scores
                ]
                
                # Get dynamic rerank weight
                rerank_weight = self._get_setting('rerank_weight', 0.7)
                fusion_weight = 1.0 - rerank_weight
                
                # Combine query match count with reranking
                final_scores = [
                    (item['doc'], fusion_weight * (item['count'] / len(all_queries)) + rerank_weight * norm_scores[i])
                    for i, item in enumerate(sorted_docs)
                ]
                final_scores.sort(key=lambda x: x[1], reverse=True)
                
                documents = [doc for doc, _ in final_scores[:5]]
                scores = [score for _, score in final_scores[:5]]

                return RetrievalResult(
                    documents=documents,
                    scores=scores,
                    strategy_used="advanced_expanded",
                    query_type="complex",
                    explanation=explanation
                )
            except Exception as e:
                logger.warning(f"Reranking failed: {e}")
        
        # Fallback
        documents = [item['doc'] for item in sorted_docs[:5]]
        scores = [item['count'] / len(all_queries) for item in sorted_docs[:5]]

        return RetrievalResult(
            documents=documents,
            scores=scores,
            strategy_used="advanced_expanded",
            query_type="complex",
            explanation=explanation
        )
    
    async def _generate_variants(self, query: str) -> List[str]:
        """Generate query variants"""
        
        prompt = f"""Generate 2 alternative phrasings using different words:

Original: {query}

Alternative 1:
Alternative 2:"""
        
        try:
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            lines = [
                line.strip().lstrip('123456789.-) ')
                for line in response.split('\n')
                if line.strip() and len(line.strip()) > 10
            ]
            # Filter out labels
            variants = [
                line.split(':', 1)[1].strip() if ':' in line else line
                for line in lines
                if not line.lower().startswith('original')
            ]
            return variants[:2]
        except Exception as e:
            logger.warning(f"Variant generation failed: {e}")
            return []


class AdaptiveAnswerGenerator:
    """Answer generator with proper prompting"""

    def __init__(self, llm: OllamaLLM, embeddings=None, collection_metadata=None, scope_config=None):
        self.llm = llm
        self.embeddings = embeddings
        self.collection_metadata = collection_metadata
        self.scope_config = scope_config
    
    async def generate(
        self,
        query: str,
        retrieval_result: RetrievalResult
    ) -> str:
        """Generate answer with proper context"""
        
        query_type = retrieval_result.query_type
        
        # Build context with source numbers
        context_parts = []
        for i, (doc, score) in enumerate(zip(
            retrieval_result.documents,
            retrieval_result.scores
        ), 1):
            source = doc.metadata.get('file_name', 'Unknown')
            page = doc.metadata.get('page_number', 'N/A')
            context_parts.append(
                f"[Source {i}: {source}, Page {page} | Relevance: {score:.2%}]\n{doc.page_content}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Adaptive instructions
        if query_type == "simple":
            instruction = "Provide a direct, concise answer in 1-2 sentences."
        elif query_type == "moderate":
            instruction = "Provide a clear answer with supporting details. Cite sources by number."
        else:
            instruction = "Provide a comprehensive answer addressing all aspects. Cite sources."
        
        prompt = f"""Answer based on the provided sources.

{instruction}

RULES:
- Answer ONLY from the sources provided
- Cite sources by number when making claims
- If information is missing, state what's unclear
- Be precise and factual

SOURCES:
{context}

QUESTION: {query}

ANSWER:"""
        
        answer = await asyncio.to_thread(self.llm.invoke, prompt)
        return answer.strip()