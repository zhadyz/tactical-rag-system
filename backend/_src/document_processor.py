"""
Document Processor for ATLAS Protocol
Handles document loading, chunking, and preparation for vector database indexing
Supports: Markdown (.md), PDF (.pdf)
"""

import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# PDF processing imports
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("pypdf not available - PDF support disabled")

logger = logging.getLogger(__name__)


@dataclass
class DocumentProcessingResult:
    """Result of document processing"""
    documents: List[Document] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    message: str = ""


class DocumentProcessor:
    """
    Document processor that handles markdown files for the case study
    """

    def __init__(self, config):
        """Initialize with config"""
        self.config = config

        # Use config values if available, otherwise use sensible defaults
        try:
            chunk_size = config.chunking.chunk_size
            chunk_overlap = config.chunking.chunk_overlap
        except AttributeError:
            chunk_size = 512
            chunk_overlap = 50
            logger.info(f"Using default chunking: size={chunk_size}, overlap={chunk_overlap}")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file using pypdf

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        if not PDF_SUPPORT:
            raise ImportError("pypdf library not available - cannot process PDF files")

        try:
            reader = PdfReader(str(pdf_path))
            text_parts = []

            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)
            logger.debug(f"Extracted {len(full_text)} chars from {len(reader.pages)} pages in {pdf_path.name}")
            return full_text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path.name}: {e}")
            raise

    async def process_documents(self, documents_dir: Path) -> DocumentProcessingResult:
        """
        Process all markdown and PDF documents in the specified directory

        Args:
            documents_dir: Path to directory containing documents

        Returns:
            DocumentProcessingResult with LangChain Document objects and metadata
        """
        logger.info(f"Processing documents from: {documents_dir}")

        if not isinstance(documents_dir, Path):
            documents_dir = Path(documents_dir)

        if not documents_dir.exists():
            error_msg = f"Documents directory does not exist: {documents_dir}"
            logger.error(error_msg)
            return DocumentProcessingResult(
                documents=[],
                success=False,
                message=error_msg
            )

        all_documents = []
        successful_files = 0
        failed_files = 0

        # Collect all supported file types
        supported_extensions = ["*.md"]
        if PDF_SUPPORT:
            supported_extensions.append("*.pdf")
            logger.info("PDF support enabled")
        else:
            logger.warning("PDF support disabled - install pypdf to enable")

        all_files = []
        for pattern in supported_extensions:
            all_files.extend(list(documents_dir.rglob(pattern)))

        logger.info(f"Found {len(all_files)} documents to process")

        # Process all files
        for file_path in all_files:
            try:
                logger.info(f"Processing file: {file_path.name}")

                # Determine file type and extract content
                file_extension = file_path.suffix.lower()

                if file_extension == '.md':
                    # Read markdown file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_type = "markdown"

                elif file_extension == '.pdf':
                    # Extract text from PDF
                    content = self._extract_pdf_text(file_path)
                    file_type = "pdf"

                else:
                    logger.warning(f"Unsupported file type: {file_extension}")
                    failed_files += 1
                    continue

                # Calculate file hash for deduplication
                file_hash = hashlib.sha256(content.encode()).hexdigest()

                # Get file metadata
                file_stats = file_path.stat()
                file_size = file_stats.st_size

                # Split into chunks
                chunks = self.text_splitter.split_text(content)
                logger.info(f"  Split {file_path.name} ({file_type}) into {len(chunks)} chunks")

                # Create LangChain Documents with metadata
                for i, chunk in enumerate(chunks):
                    metadata = {
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "file_type": file_type,
                        "file_size_bytes": file_size,
                        "file_hash": file_hash,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "processing_date": datetime.now().isoformat()
                    }

                    doc = Document(
                        page_content=chunk,
                        metadata=metadata
                    )
                    all_documents.append(doc)

                successful_files += 1

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
                failed_files += 1
                continue

        result_metadata = {
            "successful": successful_files,
            "failed": failed_files,
            "total_chunks": len(all_documents)
        }

        if len(all_documents) == 0:
            message = f"No documents processed. Successful: {successful_files}, Failed: {failed_files}"
            logger.warning(message)
            return DocumentProcessingResult(
                documents=[],
                metadata=result_metadata,
                success=False,
                message=message
            )

        message = f"Processed {successful_files} files into {len(all_documents)} chunks"
        logger.info(message)

        return DocumentProcessingResult(
            documents=all_documents,
            metadata=result_metadata,
            success=True,
            message=message
        )
