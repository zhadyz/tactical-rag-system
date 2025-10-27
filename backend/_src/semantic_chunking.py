"""
ATLAS Protocol - Semantic Chunking

Uses embedding similarity to find natural breakpoints in documents
instead of fixed character counts. Keeps policy sections together
for better context coherence.

Research Evidence: LlamaIndex semantic_chunking.ipynb
Expected Impact: +2-4 points on questions requiring multi-rule reasoning
"""

import logging
from typing import List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Semantic-aware document chunking using embeddings.

    Splits documents at semantic boundaries rather than arbitrary
    character positions, preserving policy section coherence.
    """

    def __init__(self, embed_model, buffer_size: int = 1,
                 breakpoint_threshold: float = 0.75):
        """
        Args:
            embed_model: Embedding model for computing similarities
            buffer_size: Number of sentences to combine for each embedding
            breakpoint_threshold: Similarity threshold for splits (0-1)
                Lower = more splits, Higher = fewer, larger chunks
        """
        self.embed_model = embed_model
        self.buffer_size = buffer_size
        self.breakpoint_threshold = breakpoint_threshold

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using basic heuristics.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be enhanced with NLTK/spaCy)
        import re

        # Split on period, exclamation, question mark followed by space/newline
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _create_sentence_groups(self, sentences: List[str]) -> List[str]:
        """
        Group sentences into buffers for embedding.

        Args:
            sentences: List of individual sentences

        Returns:
            List of sentence groups
        """
        groups = []

        for i in range(len(sentences)):
            # Combine current sentence with buffer_size neighbors
            start = max(0, i - self.buffer_size)
            end = min(len(sentences), i + self.buffer_size + 1)

            group = ' '.join(sentences[start:end])
            groups.append(group)

        return groups

    def _calculate_cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Cosine similarity (0-1)
        """
        emb1_arr = np.array(emb1)
        emb2_arr = np.array(emb2)

        # Cosine similarity
        dot_product = np.dot(emb1_arr, emb2_arr)
        norm1 = np.linalg.norm(emb1_arr)
        norm2 = np.linalg.norm(emb2_arr)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        return float(similarity)

    def _find_breakpoints(self, similarities: List[float]) -> List[int]:
        """
        Find semantic breakpoints based on similarity drops.

        Args:
            similarities: List of pairwise similarities

        Returns:
            List of sentence indices where breaks should occur
        """
        if not similarities:
            return []

        breakpoints = []

        # Use percentile-based threshold
        # Find positions where similarity drops significantly
        similarity_array = np.array(similarities)
        percentile_threshold = np.percentile(similarity_array,
                                            (1 - self.breakpoint_threshold) * 100)

        for i, sim in enumerate(similarities):
            if sim < percentile_threshold:
                breakpoints.append(i + 1)  # Break after this position

        logger.debug(f"[SemanticChunker] Found {len(breakpoints)} breakpoints")

        return breakpoints

    def chunk_document(self, text: str, metadata: dict = None) -> List[dict]:
        """
        Split document into semantically coherent chunks.

        Args:
            text: Document text
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunks with metadata
        """
        if not text or not text.strip():
            return []

        logger.info(f"[SemanticChunker] Chunking document ({len(text)} chars)")

        # Split into sentences
        sentences = self._split_into_sentences(text)
        logger.debug(f"[SemanticChunker] Split into {len(sentences)} sentences")

        if len(sentences) <= 1:
            # Too short to chunk semantically
            return [{'content': text, 'metadata': metadata or {}}]

        # Create sentence groups for embedding
        sentence_groups = self._create_sentence_groups(sentences)

        # Embed each group
        try:
            embeddings = self.embed_model.embed_documents(sentence_groups)
        except Exception as e:
            logger.error(f"[SemanticChunker] Embedding failed: {e}")
            # Fallback to single chunk
            return [{'content': text, 'metadata': metadata or {}}]

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._calculate_cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        # Find semantic breakpoints
        breakpoints = self._find_breakpoints(similarities)

        # Create chunks based on breakpoints
        chunks = []
        start_idx = 0

        for bp in breakpoints:
            if bp > start_idx and bp <= len(sentences):
                chunk_sentences = sentences[start_idx:bp]
                chunk_text = ' '.join(chunk_sentences)

                chunks.append({
                    'content': chunk_text,
                    'metadata': {
                        **(metadata or {}),
                        'start_sentence': start_idx,
                        'end_sentence': bp,
                        'num_sentences': len(chunk_sentences)
                    }
                })

                start_idx = bp

        # Add final chunk
        if start_idx < len(sentences):
            final_chunk_sentences = sentences[start_idx:]
            final_chunk_text = ' '.join(final_chunk_sentences)

            chunks.append({
                'content': final_chunk_text,
                'metadata': {
                    **(metadata or {}),
                    'start_sentence': start_idx,
                    'end_sentence': len(sentences),
                    'num_sentences': len(final_chunk_sentences)
                }
            })

        logger.info(f"[SemanticChunker] Created {len(chunks)} semantic chunks")

        # Log chunk sizes for debugging
        chunk_sizes = [len(c['content']) for c in chunks]
        logger.debug(f"[SemanticChunker] Chunk sizes: min={min(chunk_sizes)}, max={max(chunk_sizes)}, avg={np.mean(chunk_sizes):.0f}")

        return chunks


class HybridChunker:
    """
    Combines semantic chunking with size constraints.

    Uses semantic boundaries but enforces min/max chunk sizes
    to prevent extremely small or large chunks.
    """

    def __init__(self, semantic_chunker: SemanticChunker,
                 min_chunk_size: int = 200,
                 max_chunk_size: int = 2000):
        """
        Args:
            semantic_chunker: SemanticChunker instance
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk
        """
        self.semantic_chunker = semantic_chunker
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk_document(self, text: str, metadata: dict = None) -> List[dict]:
        """
        Chunk document with semantic awareness and size constraints.

        Args:
            text: Document text
            metadata: Optional metadata

        Returns:
            List of size-constrained semantic chunks
        """
        # Get semantic chunks
        semantic_chunks = self.semantic_chunker.chunk_document(text, metadata)

        # Post-process to enforce size constraints
        final_chunks = []

        for chunk in semantic_chunks:
            chunk_text = chunk['content']
            chunk_meta = chunk['metadata']

            # If chunk is too large, split it
            if len(chunk_text) > self.max_chunk_size:
                # Simple character-based split for oversized chunks
                parts = []
                current_pos = 0
                while current_pos < len(chunk_text):
                    part = chunk_text[current_pos:current_pos + self.max_chunk_size]
                    parts.append({
                        'content': part,
                        'metadata': {**chunk_meta, 'split_part': True}
                    })
                    current_pos += self.max_chunk_size

                final_chunks.extend(parts)

            # If chunk is too small, merge with previous if possible
            elif len(chunk_text) < self.min_chunk_size and final_chunks:
                # Try to merge with previous chunk
                prev_chunk = final_chunks[-1]
                merged_text = prev_chunk['content'] + ' ' + chunk_text

                if len(merged_text) <= self.max_chunk_size:
                    # Merge successful
                    prev_chunk['content'] = merged_text
                    prev_chunk['metadata']['merged'] = True
                else:
                    # Can't merge, add as-is
                    final_chunks.append(chunk)
            else:
                # Chunk size is acceptable
                final_chunks.append(chunk)

        logger.info(f"[HybridChunker] Finalized to {len(final_chunks)} chunks (min={self.min_chunk_size}, max={self.max_chunk_size})")

        return final_chunks
