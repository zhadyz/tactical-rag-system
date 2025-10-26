// ATLAS Protocol - Phase 1: Embedding Types
// Shared types for the embedding service

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Represents a single embedding vector with metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Embedding {
    /// The embedding vector (768 dimensions for BGE-base-en-v1.5)
    pub vector: Vec<f32>,
    /// Dimensionality of the embedding
    pub dimension: usize,
}

impl Embedding {
    /// Create a new embedding with validation
    pub fn new(vector: Vec<f32>) -> Self {
        let dimension = vector.len();
        Self { vector, dimension }
    }

    /// Get the L2 norm of the embedding
    pub fn norm(&self) -> f32 {
        self.vector.iter().map(|x| x * x).sum::<f32>().sqrt()
    }

    /// Check if this embedding is normalized (L2 norm ≈ 1.0)
    pub fn is_normalized(&self) -> bool {
        let norm = self.norm();
        (norm - 1.0).abs() < 1e-5
    }
}

/// Errors that can occur during embedding generation
#[derive(Debug, Error)]
pub enum EmbeddingError {
    #[error("ONNX Runtime error: {0}")]
    OnnxError(String),

    #[error("Tokenization error: {0}")]
    TokenizationError(String),

    #[error("Model not found at path: {0}")]
    ModelNotFound(String),

    #[error("Invalid model format: {0}")]
    InvalidModel(String),

    #[error("CUDA not available: {0}")]
    CudaNotAvailable(String),

    #[error("Batch size {0} exceeds maximum allowed {1}")]
    BatchSizeExceeded(usize, usize),

    #[error("Empty input: cannot generate embeddings for empty text")]
    EmptyInput,

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Internal error: {0}")]
    InternalError(String),
}

/// Result type for embedding operations
pub type EmbeddingResult<T> = Result<T, EmbeddingError>;

/// Batch of embeddings with statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingBatch {
    /// The generated embeddings
    pub embeddings: Vec<Embedding>,
    /// Number of embeddings in this batch
    pub count: usize,
    /// Average time per embedding (milliseconds)
    pub avg_time_ms: f64,
    /// Total batch processing time (milliseconds)
    pub total_time_ms: f64,
}

impl EmbeddingBatch {
    /// Create a new batch from vectors
    pub fn new(vectors: Vec<Vec<f32>>, total_time_ms: f64) -> Self {
        let count = vectors.len();
        let embeddings = vectors.into_iter().map(Embedding::new).collect();
        let avg_time_ms = if count > 0 {
            total_time_ms / count as f64
        } else {
            0.0
        };

        Self {
            embeddings,
            count,
            avg_time_ms,
            total_time_ms,
        }
    }

    /// Extract just the vectors
    pub fn into_vectors(self) -> Vec<Vec<f32>> {
        self.embeddings.into_iter().map(|e| e.vector).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_embedding_creation() {
        let vector = vec![0.1, 0.2, 0.3];
        let embedding = Embedding::new(vector.clone());
        assert_eq!(embedding.dimension, 3);
        assert_eq!(embedding.vector, vector);
    }

    #[test]
    fn test_embedding_norm() {
        let vector = vec![3.0, 4.0]; // 3-4-5 triangle
        let embedding = Embedding::new(vector);
        assert!((embedding.norm() - 5.0).abs() < 1e-5);
    }

    #[test]
    fn test_embedding_normalization_check() {
        let normalized = vec![0.6, 0.8]; // Normalized 3-4-5
        let embedding = Embedding::new(normalized);
        assert!(embedding.is_normalized());

        let unnormalized = vec![3.0, 4.0];
        let embedding2 = Embedding::new(unnormalized);
        assert!(!embedding2.is_normalized());
    }

    #[test]
    fn test_embedding_batch() {
        let vectors = vec![vec![1.0, 2.0], vec![3.0, 4.0]];
        let batch = EmbeddingBatch::new(vectors, 100.0);
        assert_eq!(batch.count, 2);
        assert_eq!(batch.avg_time_ms, 50.0);
        assert_eq!(batch.total_time_ms, 100.0);
    }
}
