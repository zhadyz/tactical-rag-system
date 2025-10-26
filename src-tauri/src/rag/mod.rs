// ATLAS Protocol - Phase 1: RAG Module
// Root module for Retrieval-Augmented Generation functionality

pub mod config;
pub mod embeddings;
pub mod types;
pub mod commands;

#[cfg(test)]
mod tests;

// Re-export main types for convenience
pub use config::EmbeddingConfig;
pub use embeddings::EmbeddingEngine;
pub use types::{Embedding, EmbeddingBatch, EmbeddingError, EmbeddingResult};
pub use commands::{EmbeddingState, EmbeddingResponse, EmbeddingEngineStatus};

/// Initialize the RAG module with tracing
pub fn init() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into())
        )
        .init();

    tracing::info!("ATLAS Protocol RAG module initialized");
}
