"""
Forge - Self-Verification

Extracts claims from a generated answer and checks each against
the source documents. Reports which claims are supported.
"""

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Verification outcome for a single claim."""
    claim: str
    supported: bool
    confidence: float
    supporting_sources: list[str]
    explanation: str = ""


class ClaimVerifier:
    """
    Post-generation self-verification.

    Step 1: Use the LLM to extract atomic claims from the answer.
    Step 2: For each claim, check whether any source document supports it.
    Step 3: Return structured verification results.

    Args:
        container: ServiceContainer for LLM access.
    """

    def __init__(self, container=None):
        self.container = container

    async def verify(
        self, answer: str, sources: list[dict]
    ) -> list[VerificationResult]:
        """
        Verify claims in an answer against source documents.

        Args:
            answer: The generated answer text.
            sources: List of source dicts with 'content' and optional 'id'.

        Returns:
            List of VerificationResult for each extracted claim.
        """
        if not answer or not sources:
            return []

        start = time.perf_counter()

        # ------------------------------------------------------------------
        # Step 1: Extract claims
        # ------------------------------------------------------------------
        claims = await self._extract_claims(answer)
        if not claims:
            logger.info("[Verifier] No claims extracted from answer")
            return []

        # ------------------------------------------------------------------
        # Step 2: Check each claim against sources
        # ------------------------------------------------------------------
        results: list[VerificationResult] = []

        source_texts = [
            s.get("content", "")[:2000] for s in sources
        ]
        source_ids = [
            s.get("id", s.get("metadata", {}).get("file_name", f"Source {i+1}"))
            for i, s in enumerate(sources)
        ]

        for claim in claims:
            verification = await self._verify_claim(claim, source_texts, source_ids)
            results.append(verification)

        elapsed_ms = (time.perf_counter() - start) * 1000
        supported = sum(1 for r in results if r.supported)
        logger.info(
            f"[Verifier] {supported}/{len(results)} claims supported "
            f"time={elapsed_ms:.1f}ms"
        )

        return results

    async def _extract_claims(self, answer: str) -> list[str]:
        """Use the LLM to extract atomic claims from the answer."""
        if self.container is None:
            return self._heuristic_extract(answer)

        try:
            llm = await self.container.get_llm()

            prompt = (
                "Extract the key factual claims from the following answer. "
                "List each claim as a short, self-contained statement on its own line. "
                "Only include verifiable factual claims, not opinions or hedges. "
                "Return ONLY the numbered list, nothing else.\n\n"
                f"Answer:\n{answer[:3000]}\n\n"
                "Claims:"
            )

            response = await llm.generate(prompt)

            claims: list[str] = []
            for line in response.strip().split("\n"):
                cleaned = line.strip()
                if not cleaned or len(cleaned) < 10:
                    continue
                # Strip numbering
                for prefix in (
                    "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.",
                    "-", "*",
                ):
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):].strip()
                        break
                if cleaned:
                    claims.append(cleaned)

            return claims[:10]  # Cap at 10 claims

        except Exception as e:
            logger.warning(f"[Verifier] LLM claim extraction failed: {e}")
            return self._heuristic_extract(answer)

    def _heuristic_extract(self, answer: str) -> list[str]:
        """Fallback: split answer into sentences as pseudo-claims."""
        import re

        sentences = re.split(r'(?<=[.!?])\s+', answer.strip())
        claims = [
            s.strip() for s in sentences
            if len(s.strip()) > 20 and not s.strip().startswith("I ")
        ]
        return claims[:8]

    async def _verify_claim(
        self,
        claim: str,
        source_texts: list[str],
        source_ids: list[str],
    ) -> VerificationResult:
        """Check a single claim against all source documents."""
        if self.container is None:
            return self._heuristic_verify(claim, source_texts, source_ids)

        try:
            llm = await self.container.get_llm()

            source_block = "\n\n".join(
                f"[Source {i+1}] {text}"
                for i, text in enumerate(source_texts)
            )

            prompt = (
                "Determine if the following claim is supported by the source documents.\n\n"
                f"Claim: {claim}\n\n"
                f"Sources:\n{source_block[:4000]}\n\n"
                "Reply in this exact format:\n"
                "SUPPORTED: yes or no\n"
                "CONFIDENCE: 0.0 to 1.0\n"
                "SOURCES: comma-separated source numbers that support it (e.g. 1,3) or none\n"
                "REASON: one sentence explanation"
            )

            response = await llm.generate(prompt)
            return self._parse_verification(response, claim, source_ids)

        except Exception as e:
            logger.warning(f"[Verifier] LLM verification failed for claim: {e}")
            return self._heuristic_verify(claim, source_texts, source_ids)

    def _parse_verification(
        self, response: str, claim: str, source_ids: list[str]
    ) -> VerificationResult:
        """Parse LLM verification response."""
        lines = response.strip().split("\n")

        supported = False
        confidence = 0.5
        supporting: list[str] = []
        explanation = ""

        for line in lines:
            line_lower = line.strip().lower()
            if line_lower.startswith("supported:"):
                supported = "yes" in line_lower
            elif line_lower.startswith("confidence:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, IndexError):
                    pass
            elif line_lower.startswith("sources:"):
                raw = line.split(":", 1)[1].strip()
                if raw.lower() != "none":
                    import re
                    nums = re.findall(r'\d+', raw)
                    for n in nums:
                        idx = int(n) - 1
                        if 0 <= idx < len(source_ids):
                            supporting.append(source_ids[idx])
            elif line_lower.startswith("reason:"):
                explanation = line.split(":", 1)[1].strip()

        return VerificationResult(
            claim=claim,
            supported=supported,
            confidence=confidence,
            supporting_sources=supporting,
            explanation=explanation,
        )

    def _heuristic_verify(
        self,
        claim: str,
        source_texts: list[str],
        source_ids: list[str],
    ) -> VerificationResult:
        """Fallback keyword-overlap verification."""
        claim_words = set(claim.lower().split())
        # Remove stopwords
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "about", "that", "this", "it", "its", "and",
            "or", "but", "not", "no", "if", "than", "so",
        }
        claim_words -= stopwords

        supporting: list[str] = []
        max_overlap = 0.0

        for text, sid in zip(source_texts, source_ids):
            source_words = set(text.lower().split())
            if not claim_words:
                continue
            overlap = len(claim_words & source_words) / len(claim_words)
            if overlap > 0.4:
                supporting.append(sid)
            max_overlap = max(max_overlap, overlap)

        return VerificationResult(
            claim=claim,
            supported=bool(supporting),
            confidence=min(1.0, max_overlap),
            supporting_sources=supporting,
            explanation="Heuristic keyword-overlap verification",
        )
