"""
Enterprise RAG System - Advanced Document Processing
Parallel processing, intelligent chunking, and metadata extraction
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import hashlib
import logging
from dataclasses import dataclass

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredMarkdownLoader
)
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Document processing result"""
    documents: List[Document]
    metadata: Dict
    errors: List[str]


class IntelligentChunker:
    """Advanced chunking with multiple strategies"""
    
    def __init__(self, config):
        self.config = config
        self.sentence_model = None
        
        if config.chunking.strategy in ["semantic", "hybrid"]:
            logger.info("Loading sentence transformer for semantic chunking...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def chunk(self, documents: List[Document]) -> List[Document]:
        """Apply intelligent chunking strategy"""
        
        strategy = self.config.chunking.strategy
        
        if strategy == "recursive":
            return self._recursive_chunk(documents)
        elif strategy == "semantic":
            return self._semantic_chunk(documents)
        elif strategy == "sentence":
            return self._sentence_chunk(documents)
        elif strategy == "hybrid":
            return self._hybrid_chunk(documents)
        else:
            return self._recursive_chunk(documents)
    
    def _recursive_chunk(self, documents: List[Document]) -> List[Document]:
        """Standard recursive character splitting with optimization"""
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunking.chunk_size,
            chunk_overlap=self.config.chunking.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
        
        chunks = []
        for doc in documents:
            if len(doc.page_content) < self.config.chunking.min_chunk_size:
                continue
            
            doc_chunks = splitter.split_documents([doc])
            
            # Add chunk index to metadata
            for i, chunk in enumerate(doc_chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = len(doc_chunks)
                chunk.metadata["chunking_strategy"] = "recursive"
            
            chunks.extend(doc_chunks)
        
        return chunks
    
    def _semantic_chunk(self, documents: List[Document]) -> List[Document]:
        """Semantic chunking based on sentence similarity"""
        
        chunks = []
        
        for doc in documents:
            # Split into sentences
            sentences = self._split_sentences(doc.page_content)
            
            if len(sentences) < 3:
                chunks.append(doc)
                continue
            
            # Get embeddings
            embeddings = self.sentence_model.encode(sentences)
            
            # Find semantic boundaries
            boundaries = self._find_semantic_boundaries(
                embeddings,
                self.config.chunking.semantic_similarity_threshold
            )
            
            # Create chunks
            doc_chunks = []
            start_idx = 0
            
            for boundary in boundaries:
                chunk_text = " ".join(sentences[start_idx:boundary])
                
                if len(chunk_text) >= self.config.chunking.min_chunk_size:
                    chunk_doc = Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_index": len(doc_chunks),
                            "chunking_strategy": "semantic",
                            "sentence_start": start_idx,
                            "sentence_end": boundary
                        }
                    )
                    doc_chunks.append(chunk_doc)
                
                start_idx = boundary
            
            # Add remaining sentences
            if start_idx < len(sentences):
                chunk_text = " ".join(sentences[start_idx:])
                if len(chunk_text) >= self.config.chunking.min_chunk_size:
                    chunk_doc = Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_index": len(doc_chunks),
                            "chunking_strategy": "semantic"
                        }
                    )
                    doc_chunks.append(chunk_doc)
            
            # Update total_chunks metadata
            for chunk in doc_chunks:
                chunk.metadata["total_chunks"] = len(doc_chunks)
            
            chunks.extend(doc_chunks)
        
        return chunks
    
    def _sentence_chunk(self, documents: List[Document]) -> List[Document]:
        """Sentence-based chunking with fixed sentence count"""
        
        sentences_per_chunk = self.config.chunking.chunk_size // 100  # Rough estimate
        chunks = []
        
        for doc in documents:
            sentences = self._split_sentences(doc.page_content)
            
            doc_chunks = []
            for i in range(0, len(sentences), sentences_per_chunk):
                chunk_sentences = sentences[i:i + sentences_per_chunk]
                chunk_text = " ".join(chunk_sentences)
                
                if len(chunk_text) >= self.config.chunking.min_chunk_size:
                    chunk_doc = Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_index": len(doc_chunks),
                            "chunking_strategy": "sentence"
                        }
                    )
                    doc_chunks.append(chunk_doc)
            
            for chunk in doc_chunks:
                chunk.metadata["total_chunks"] = len(doc_chunks)
            
            chunks.extend(doc_chunks)
        
        return chunks
    
    def _hybrid_chunk(self, documents: List[Document]) -> List[Document]:
        """Hybrid chunking: recursive with semantic refinement"""
        
        # First pass: recursive chunking
        recursive_chunks = self._recursive_chunk(documents)
        
        # Second pass: refine boundaries semantically
        refined_chunks = []
        
        for chunk in recursive_chunks:
            # Only refine large chunks
            if len(chunk.page_content) > self.config.chunking.chunk_size * 1.5:
                # Split into sentences
                sentences = self._split_sentences(chunk.page_content)
                
                if len(sentences) > 5:
                    embeddings = self.sentence_model.encode(sentences)
                    boundaries = self._find_semantic_boundaries(embeddings, 0.8)
                    
                    # Create sub-chunks
                    start_idx = 0
                    for boundary in boundaries:
                        sub_text = " ".join(sentences[start_idx:boundary])
                        if len(sub_text) >= self.config.chunking.min_chunk_size:
                            sub_chunk = Document(
                                page_content=sub_text,
                                metadata={
                                    **chunk.metadata,
                                    "chunking_strategy": "hybrid"
                                }
                            )
                            refined_chunks.append(sub_chunk)
                        start_idx = boundary
                    
                    # Remaining
                    if start_idx < len(sentences):
                        sub_text = " ".join(sentences[start_idx:])
                        if len(sub_text) >= self.config.chunking.min_chunk_size:
                            sub_chunk = Document(
                                page_content=sub_text,
                                metadata={
                                    **chunk.metadata,
                                    "chunking_strategy": "hybrid"
                                }
                            )
                            refined_chunks.append(sub_chunk)
                    continue
            
            refined_chunks.append(chunk)
        
        return refined_chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_semantic_boundaries(
        self,
        embeddings: np.ndarray,
        threshold: float
    ) -> List[int]:
        """Find semantic boundaries in embeddings"""
        
        boundaries = []
        current_chunk_size = 0
        
        for i in range(1, len(embeddings)):
            # Calculate similarity with previous sentence
            similarity = np.dot(embeddings[i-1], embeddings[i]) / (
                np.linalg.norm(embeddings[i-1]) * np.linalg.norm(embeddings[i])
            )
            
            # If similarity drops below threshold, mark as boundary
            if similarity < threshold:
                boundaries.append(i)
                current_chunk_size = 0
            else:
                current_chunk_size += 1
            
            # Also enforce maximum chunk size
            if current_chunk_size >= 10:  # Max 10 sentences per chunk
                boundaries.append(i)
                current_chunk_size = 0
        
        return boundaries


class DocumentLoader:
    """Parallel document loading with error handling"""
    
    def __init__(self, config):
        self.config = config
        self.supported_extensions = {
            '.txt': self._load_txt,
            '.pdf': self._load_pdf,
            '.docx': self._load_docx,
            '.doc': self._load_docx,
            '.md': self._load_markdown
        }
    
    async def load_directory(self, directory: Path) -> ProcessingResult:
        """Load all documents from directory in parallel"""
        
        if not directory.exists():
            return ProcessingResult([], {}, [f"Directory not found: {directory}"])
        
        # Find all supported files
        files = []
        for ext in self.supported_extensions.keys():
            files.extend(list(directory.rglob(f"*{ext}")))
        
        if not files:
            return ProcessingResult([], {}, ["No supported files found"])
        
        logger.info(f"Found {len(files)} files to process")
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.config.performance.max_workers) as executor:
            tasks = [
                asyncio.get_event_loop().run_in_executor(
                    executor,
                    self._load_file,
                    file_path
                )
                for file_path in files
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        all_documents = []
        errors = []
        file_stats = {}
        
        for file_path, result in zip(files, results):
            if isinstance(result, Exception):
                error_msg = f"{file_path.name}: {str(result)}"
                errors.append(error_msg)
                logger.error(error_msg)
            elif result:
                docs, file_meta = result
                all_documents.extend(docs)
                file_stats[file_path.name] = file_meta
        
        metadata = {
            "total_files": len(files),
            "successful": len(file_stats),
            "failed": len(errors),
            "total_documents": len(all_documents),
            "file_stats": file_stats,
            "processing_date": datetime.now().isoformat()
        }
        
        return ProcessingResult(all_documents, metadata, errors)
    
    def _load_file(self, file_path: Path) -> Optional[Tuple[List[Document], Dict]]:
        """Load a single file"""
        
        ext = file_path.suffix.lower()
        if ext not in self.supported_extensions:
            return None
        
        logger.info(f"Processing: {file_path.name}")
        
        try:
            loader_func = self.supported_extensions[ext]
            documents = loader_func(file_path)
            
            if not documents:
                return None
            
            # Enhance metadata
            file_hash = self._compute_file_hash(file_path)
            file_size = file_path.stat().st_size
            
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "file_name": file_path.name,
                    "file_type": ext,
                    "file_size_bytes": file_size,
                    "file_hash": file_hash,
                    "processing_date": datetime.now().isoformat()
                })
            
            file_meta = {
                "num_sections": len(documents),
                "file_size_bytes": file_size,
                "file_hash": file_hash
            }
            
            logger.info(f"✓ {file_path.name}: {len(documents)} sections")
            return documents, file_meta
            
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            raise
    
    def _load_txt(self, file_path: Path) -> List[Document]:
        """Load text file with encoding detection"""
        
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                
                if text.strip():
                    return [Document(page_content=text)]
                    
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Fallback: ignore errors
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        if text.strip():
            return [Document(page_content=text)]
        
        return []
    
    def _load_pdf(self, file_path: Path) -> List[Document]:
        """Load PDF with OCR fallback"""
        
        try:
            loader = PyPDFLoader(str(file_path))
            docs = loader.load()
            
            # Filter empty pages
            valid_docs = [doc for doc in docs if doc.page_content.strip()]
            
            if valid_docs:
                # Add page numbers
                for i, doc in enumerate(valid_docs):
                    doc.metadata["page_number"] = i + 1
                return valid_docs
            
            # Try OCR if no text extracted
            return self._load_pdf_with_ocr(file_path)
            
        except Exception as e:
            logger.warning(f"PDF loading failed, trying OCR: {e}")
            return self._load_pdf_with_ocr(file_path)
    
    def _load_pdf_with_ocr(self, file_path: Path) -> List[Document]:
        """OCR-based PDF loading"""
        
        try:
            from pdf2image import convert_from_path
            import pytesseract
            from PIL import Image
            
            images = convert_from_path(str(file_path), dpi=200)
            documents = []
            
            for i, image in enumerate(images):
                # Resize if too large
                if image.size[0] > 2000 or image.size[1] > 2000:
                    image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                
                # Convert to grayscale
                image = image.convert('L')
                
                # OCR
                text = pytesseract.image_to_string(
                    image,
                    lang='eng',
                    config='--psm 3 --oem 1'
                )
                
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "page_number": i + 1,
                            "extraction_method": "ocr"
                        }
                    )
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return []
    
    def _load_docx(self, file_path: Path) -> List[Document]:
        """Load DOCX file"""
        
        try:
            loader = Docx2txtLoader(str(file_path))
            docs = loader.load()
            return [doc for doc in docs if doc.page_content.strip()]
        except Exception as e:
            logger.error(f"DOCX loading failed: {e}")
            return []
    
    def _load_markdown(self, file_path: Path) -> List[Document]:
        """Load Markdown file"""
        
        try:
            loader = UnstructuredMarkdownLoader(str(file_path))
            docs = loader.load()
            return [doc for doc in docs if doc.page_content.strip()]
        except Exception as e:
            logger.error(f"Markdown loading failed: {e}")
            return []
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file"""
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


class DocumentProcessor:
    """Complete document processing pipeline"""
    
    def __init__(self, config):
        self.config = config
        self.loader = DocumentLoader(config)
        self.chunker = IntelligentChunker(config)
    
    async def process_documents(self, directory: Path) -> ProcessingResult:
        """Complete document processing pipeline"""
        
        logger.info("=" * 60)
        logger.info("DOCUMENT PROCESSING PIPELINE")
        logger.info("=" * 60)
        
        # Stage 1: Load documents
        logger.info("\nStage 1: Loading documents...")
        load_result = await self.loader.load_directory(directory)
        
        if not load_result.documents:
            logger.error("No documents loaded!")
            return load_result
        
        logger.info(f"✓ Loaded {len(load_result.documents)} document sections")
        
        # Stage 2: Chunk documents
        logger.info(f"\nStage 2: Chunking (strategy: {self.config.chunking.strategy})...")
        chunks = await asyncio.to_thread(
            self.chunker.chunk,
            load_result.documents
        )
        
        logger.info(f"✓ Created {len(chunks)} chunks")
        
        # Update metadata
        load_result.metadata["total_chunks"] = len(chunks)
        load_result.metadata["avg_chunk_size"] = np.mean([
            len(chunk.page_content) for chunk in chunks
        ])
        
        # Stage 3: Quality checks
        logger.info("\nStage 3: Quality validation...")
        valid_chunks = self._validate_chunks(chunks)
        logger.info(f"✓ {len(valid_chunks)} chunks passed validation")
        
        load_result.documents = valid_chunks
        
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        
        return load_result
    
    def _validate_chunks(self, chunks: List[Document]) -> List[Document]:
        """Validate chunk quality"""
        
        valid_chunks = []
        
        for chunk in chunks:
            # Check minimum size
            if len(chunk.page_content) < self.config.chunking.min_chunk_size:
                continue
            
            # Check if mostly whitespace
            if len(chunk.page_content.strip()) / len(chunk.page_content) < 0.3:
                continue
            
            # Check if contains actual words
            words = chunk.page_content.split()
            if len(words) < 10:
                continue
            
            valid_chunks.append(chunk)
        
        return valid_chunks