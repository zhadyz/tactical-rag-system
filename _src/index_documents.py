"""
Enterprise RAG System - Document Indexing Pipeline
High-performance parallel indexing with advanced chunking
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import List
import sys
import os

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document

# Import our modules
from config import SystemConfig, load_config
from document_processor import DocumentProcessor, ProcessingResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/indexing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DocumentIndexer:
    """High-performance document indexing system"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.processor = DocumentProcessor(config)
    
    async def index_documents(self) -> bool:
        """Complete indexing pipeline"""
        
        logger.info("=" * 70)
        logger.info("ENTERPRISE DOCUMENT INDEXING PIPELINE")
        logger.info("=" * 70)
        
        # Validate directories
        if not self.config.documents_dir.exists():
            logger.error(f"Documents directory not found: {self.config.documents_dir}")
            self.config.documents_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory. Please add documents and re-run.")
            return False
        
        # Stage 1: Process documents
        logger.info("\n📂 STAGE 1: DOCUMENT PROCESSING")
        logger.info("-" * 70)
        
        result = await self.processor.process_documents(self.config.documents_dir)
        
        if not result.documents:
            logger.error("No documents to index!")
            return False
        
        if result.errors:
            logger.warning(f"⚠ {len(result.errors)} files failed to process:")
            for error in result.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        logger.info(f"\n✓ Successfully processed {len(result.documents)} chunks")
        logger.info(f"  Average chunk size: {result.metadata['avg_chunk_size']:.0f} characters")
        
        # Stage 2: Generate embeddings
        logger.info("\n🔢 STAGE 2: EMBEDDING GENERATION")
        logger.info("-" * 70)
        
        embeddings = OllamaEmbeddings(
            model=self.config.embedding.model_name,
            base_url=self.config.ollama_host
        )
        
        # Test embedding
        logger.info("Testing embedding model...")
        test_embed = await asyncio.to_thread(embeddings.embed_query, "test")
        logger.info(f"✓ Embedding dimension: {len(test_embed)}")
        
        # Stage 3: Create vector store
        logger.info("\n💾 STAGE 3: VECTOR DATABASE CREATION")
        logger.info("-" * 70)
        
        success = await self._create_vector_store(result.documents, embeddings)
        
        if not success:
            logger.error("Failed to create vector store")
            return False
        
        # Stage 4: Save metadata for BM25
        logger.info("\n📊 STAGE 4: METADATA PERSISTENCE")
        logger.info("-" * 70)
        
        await self._save_metadata(result.documents)
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ INDEXING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"\n📈 STATISTICS:")
        logger.info(f"  Total files processed: {result.metadata['successful']}")
        logger.info(f"  Total chunks indexed: {len(result.documents)}")
        logger.info(f"  Database location: {self.config.vector_db_dir}")
        logger.info(f"  Chunking strategy: {self.config.chunking.strategy}")
        logger.info(f"  Embedding model: {self.config.embedding.model_name}")
        logger.info("\n🚀 Ready to start querying!")
        logger.info("=" * 70)
        
        return True
    
    async def _create_vector_store(
        self,
        documents: List[Document],
        embeddings: OllamaEmbeddings
    ) -> bool:
        """Create vector store with progress tracking"""
        
        try:
            persist_directory = str(self.config.vector_db_dir)
            
            # Check if database already exists with content
            if os.path.exists(persist_directory):
                db_files = os.listdir(persist_directory)
                if db_files and any(f.endswith('.sqlite3') for f in db_files):
                    logger.warning("Vector database already exists, skipping creation")
                    return True
                
                # Directory exists but empty - just use it
                logger.info("Using existing empty database directory...")
            else:
                # Create directory
                os.makedirs(persist_directory, exist_ok=True)
                logger.info("Created database directory...")
            
            # Batch processing for large document sets
            batch_size = 32  # Optimized for GPU
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            logger.info(f"Processing {len(documents)} chunks in {total_batches} batches...")
            
            vectorstore = None
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"  Batch {batch_num}/{total_batches}: {len(batch)} chunks...")
                
                if vectorstore is None:
                    # Create initial vectorstore
                    vectorstore = await asyncio.to_thread(
                        Chroma.from_documents,
                        documents=batch,
                        embedding=embeddings,
                        persist_directory=persist_directory
                    )
                else:
                    # Add to existing vectorstore
                    await asyncio.to_thread(
                        vectorstore.add_documents,
                        documents=batch
                    )
                
                progress = (batch_num / total_batches) * 100
                logger.info(f"  Progress: {progress:.1f}%")
            
            logger.info("Vector database created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Vector store creation failed: {e}", exc_info=True)
            return False
    
    async def _save_metadata(self, documents: List[Document]) -> None:
        """Save chunk metadata for BM25 retriever"""
        
        try:
            texts = [doc.page_content for doc in documents]
            metadata = [doc.metadata for doc in documents]
            
            metadata_file = self.config.vector_db_dir / "chunk_metadata.json"
            
            data = {
                "texts": texts,
                "metadata": metadata,
                "total_chunks": len(documents),
                "indexed_at": str(asyncio.get_event_loop().time())
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f)
            
            logger.info(f"✓ Metadata saved: {metadata_file}")
            
        except Exception as e:
            logger.error(f"Metadata save failed: {e}")


async def main():
    """Main indexing entry point"""
    
    # Load configuration
    config = load_config()
    
    # Create indexer
    indexer = DocumentIndexer(config)
    
    # Run indexing
    success = await indexer.index_documents()
    
    if success:
        logger.info("\n✅ Indexing completed successfully!")
        logger.info("You can now run app_v2.py to start the RAG system.")
        sys.exit(0)
    else:
        logger.error("\n❌ Indexing failed!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n\n⚠ Indexing cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)