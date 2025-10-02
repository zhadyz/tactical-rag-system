"""
Dynamic Example Question Generator
Analyzes indexed documents and generates relevant example questions
"""

import asyncio
import logging
import random
from typing import List, Optional
from pathlib import Path
import json

from langchain_ollama import OllamaLLM
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

logger = logging.getLogger(__name__)


class ExampleGenerator:
    """Generate example questions based on document content"""
    
    def __init__(self, config, llm: Optional[OllamaLLM] = None):
        self.config = config
        self.llm = llm
        self.cache_file = Path(".cache/example_questions.json")
    
    async def generate_examples(
        self,
        vectorstore: Chroma,
        num_examples: int = 4
    ) -> List[str]:
        """Generate example questions from document analysis"""
        
        # Try loading from cache first (faster startup)
        cached = self._load_from_cache()
        if cached:
            logger.info(f"Loaded {len(cached)} example questions from cache")
            return random.sample(cached, min(num_examples, len(cached)))
        
        logger.info("Generating example questions from documents...")
        
        try:
            # Step 1: Get diverse document samples
            samples = await self._get_document_samples(vectorstore, num_samples=8)
            
            if not samples:
                logger.warning("No document samples found, using defaults")
                return self._get_default_examples()
            
            # Step 2: Generate questions from samples
            if self.llm:
                questions = await self._generate_with_llm(samples, num_examples)
            else:
                questions = self._generate_heuristic(samples, num_examples)
            
            # Step 3: Cache for next time
            self._save_to_cache(questions)
            
            logger.info(f"Generated {len(questions)} example questions")
            return questions
            
        except Exception as e:
            logger.error(f"Example generation failed: {e}")
            return self._get_default_examples()
    
    async def _get_document_samples(
        self,
        vectorstore: Chroma,
        num_samples: int = 8
    ) -> List[str]:
        """Get diverse samples from the document collection"""
        
        try:
            # Strategy: Use diverse queries to get varied content
            seed_queries = [
                "policy",
                "procedure",
                "requirement",
                "standard",
                "regulation",
                "guideline",
                "rule",
                "instruction"
            ]
            
            samples = []
            seen_content = set()
            
            for query in seed_queries:
                results = await asyncio.to_thread(
                    vectorstore.similarity_search,
                    query,
                    k=2
                )
                
                for doc in results:
                    # Avoid duplicates
                    content_hash = hash(doc.page_content[:100])
                    if content_hash not in seen_content:
                        samples.append(doc.page_content[:500])  # First 500 chars
                        seen_content.add(content_hash)
                
                if len(samples) >= num_samples:
                    break
            
            return samples
            
        except Exception as e:
            logger.error(f"Failed to get samples: {e}")
            return []
    
    async def _generate_with_llm(
        self,
        samples: List[str],
        num_examples: int
    ) -> List[str]:
        """Generate questions using LLM"""
        
        # Combine samples
        combined_text = "\n\n---\n\n".join(samples[:4])
        
        prompt = f"""Based on these document excerpts, generate {num_examples} example questions that someone might ask about this content. 

Make the questions:
- Specific and realistic
- Varied in complexity (some simple, some complex)
- Representative of what the documents cover
- Natural sounding

DOCUMENT EXCERPTS:
{combined_text}

Generate exactly {num_examples} questions, one per line, without numbering:"""
        
        try:
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            
            # Parse questions
            lines = response.strip().split('\n')
            questions = []
            
            for line in lines:
                # Clean up
                line = line.strip()
                # Remove numbering like "1.", "Q1:", etc.
                line = line.lstrip('0123456789.-:) ')
                # Remove quotes
                line = line.strip('"\'')
                
                if line and len(line) > 10 and '?' in line:
                    questions.append(line)
            
            # Take the requested number
            return questions[:num_examples]
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_heuristic(samples, num_examples)
    
    def _generate_heuristic(
        self,
        samples: List[str],
        num_examples: int
    ) -> List[str]:
        """Generate questions using heuristics (no LLM needed)"""
        
        questions = []
        
        # Extract key topics from samples
        topics = self._extract_topics(samples)
        
        if not topics:
            return self._get_default_examples()
        
        # Generate question templates
        templates = [
            f"What are the requirements for {topics[0]}?",
            f"Can you explain {topics[1] if len(topics) > 1 else topics[0]}?",
            f"What is the policy on {topics[2] if len(topics) > 2 else topics[0]}?",
            f"How does {topics[3] if len(topics) > 3 else topics[0]} work?",
        ]
        
        return templates[:num_examples]
    
    def _extract_topics(self, samples: List[str]) -> List[str]:
        """Extract key topics/phrases from samples"""
        
        # Simple keyword extraction
        keywords = []
        
        for sample in samples:
            words = sample.lower().split()
            
            # Look for noun phrases (simple heuristic)
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                
                # Filter common phrases
                if any(kw in phrase for kw in ['the', 'and', 'or', 'for', 'with']):
                    continue
                
                if len(phrase) > 8 and phrase not in keywords:
                    keywords.append(phrase)
        
        return keywords[:10]
    
    def _get_default_examples(self) -> List[str]:
        """Fallback default questions"""
        return [
            "What are the main requirements?",
            "Can you summarize the key policies?",
            "What procedures should I follow?",
            "What are the standards mentioned?"
        ]
    
    def _load_from_cache(self) -> Optional[List[str]]:
        """Load cached examples"""
        
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check if cache is stale (older than 7 days)
                import time
                cache_age = time.time() - self.cache_file.stat().st_mtime
                if cache_age < 7 * 24 * 3600:  # 7 days
                    return data.get('questions', [])
        
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        
        return None
    
    def _save_to_cache(self, questions: List[str]) -> None:
        """Save examples to cache"""
        
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w') as f:
                json.dump({'questions': questions}, f, indent=2)
            
            logger.info(f"Cached {len(questions)} example questions")
        
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")