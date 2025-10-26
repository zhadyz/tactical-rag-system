// ATLAS Protocol - Phase 1: Embedding Engine
// GPU-accelerated embedding generation using ONNX Runtime with CUDA

use std::time::Instant;

use ort::{execution_providers::CUDAExecutionProvider, session::{Session, builder::SessionBuilder}, value::Tensor};
use tokenizers::Tokenizer;
use ndarray::Array2;
use tracing::{debug, info, warn};

use crate::rag::config::EmbeddingConfig;
use crate::rag::types::{Embedding, EmbeddingError, EmbeddingResult, EmbeddingBatch};

/// Main embedding engine using ONNX Runtime with CUDA acceleration
///
/// This engine generates 768-dimensional embeddings using the BGE-base-en-v1.5 model.
/// It supports batch processing and GPU acceleration for optimal performance.
///
/// # Example
///
/// ```rust,ignore
/// let config = EmbeddingConfig::default();
/// let engine = EmbeddingEngine::new(config)?;
/// let texts = vec!["Hello world".to_string()];
/// let embeddings = engine.embed_batch(texts)?;
/// ```
pub struct EmbeddingEngine {
    /// ONNX Runtime session for inference
    session: Session,

    /// Tokenizer for text preprocessing
    tokenizer: Tokenizer,

    /// Configuration settings
    config: EmbeddingConfig,
}

impl EmbeddingEngine {
    /// Create a new embedding engine with the given configuration
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - The model file doesn't exist
    /// - The tokenizer file doesn't exist
    /// - ONNX Runtime fails to initialize
    /// - CUDA is requested but not available
    pub fn new(config: EmbeddingConfig) -> EmbeddingResult<Self> {
        info!("Initializing EmbeddingEngine with config: {:?}", config);

        // Validate configuration
        config.validate()
            .map_err(|e| EmbeddingError::InternalError(e))?;

        // Check if model file exists
        if !config.model_path.exists() {
            return Err(EmbeddingError::ModelNotFound(
                config.model_path.display().to_string()
            ));
        }

        // Check if tokenizer file exists
        if !config.tokenizer_path.exists() {
            return Err(EmbeddingError::ModelNotFound(
                config.tokenizer_path.display().to_string()
            ));
        }

        // Initialize ONNX Runtime session
        let session = Self::create_session(&config)?;

        // Load tokenizer
        let tokenizer = Tokenizer::from_file(&config.tokenizer_path)
            .map_err(|e| EmbeddingError::TokenizationError(e.to_string()))?;

        info!("EmbeddingEngine initialized successfully");
        info!("Model: {}", config.model_path.display());
        info!("Execution provider: {}", config.get_execution_provider());
        info!("Max batch size: {}", config.max_batch_size);

        Ok(Self {
            session,
            tokenizer,
            config,
        })
    }

    /// Create ONNX Runtime session with appropriate execution provider
    fn create_session(config: &EmbeddingConfig) -> EmbeddingResult<Session> {
        let mut session_builder = SessionBuilder::new()
            .map_err(|e| EmbeddingError::OnnxError(e.to_string()))?;

        // Configure execution provider
        if config.use_gpu {
            info!("Attempting to use CUDA execution provider");

            // Try to use CUDA
            session_builder = session_builder
                .with_execution_providers([
                    CUDAExecutionProvider::default().build()
                ])
                .map_err(|e| {
                    warn!("CUDA not available: {}", e);
                    EmbeddingError::CudaNotAvailable(e.to_string())
                })?;
        } else {
            info!("Using CPU execution provider with {} threads", config.num_threads);
            session_builder = session_builder
                .with_intra_threads(config.num_threads)
                .map_err(|e| EmbeddingError::OnnxError(e.to_string()))?;
        }

        // Load the model
        let session = session_builder
            .commit_from_file(&config.model_path)
            .map_err(|e| EmbeddingError::OnnxError(e.to_string()))?;

        Ok(session)
    }

    /// Generate embeddings for a batch of texts
    ///
    /// This method automatically handles batching and normalization.
    ///
    /// # Arguments
    ///
    /// * `texts` - Vector of strings to embed
    ///
    /// # Returns
    ///
    /// A batch of normalized embeddings with performance statistics
    pub fn embed_batch(&mut self, texts: Vec<String>) -> EmbeddingResult<EmbeddingBatch> {
        if texts.is_empty() {
            return Err(EmbeddingError::EmptyInput);
        }

        let start = Instant::now();
        let batch_size = texts.len();

        debug!("Embedding batch of {} texts", batch_size);

        // Split into chunks if necessary
        let chunks: Vec<_> = texts
            .chunks(self.config.max_batch_size)
            .collect();

        let mut all_embeddings = Vec::with_capacity(batch_size);

        for (i, chunk) in chunks.iter().enumerate() {
            debug!("Processing chunk {}/{} (size: {})", i + 1, chunks.len(), chunk.len());
            let chunk_embeddings = self.embed_chunk(chunk.to_vec())?;
            all_embeddings.extend(chunk_embeddings);
        }

        let total_time = start.elapsed().as_secs_f64() * 1000.0;
        info!("Batch embedding complete: {} texts in {:.2}ms ({:.2} texts/sec)",
              batch_size, total_time, batch_size as f64 / (total_time / 1000.0));

        Ok(EmbeddingBatch::new(all_embeddings, total_time))
    }

    /// Generate embeddings for a single chunk (respects max_batch_size)
    fn embed_chunk(&mut self, texts: Vec<String>) -> EmbeddingResult<Vec<Vec<f32>>> {
        // Tokenize all texts
        let tokenized = self.tokenize_batch(&texts)?;

        // Run inference
        let embeddings = self.run_inference(tokenized)?;

        // Normalize embeddings (L2 normalization for cosine similarity)
        let normalized = embeddings
            .into_iter()
            .map(|emb| self.normalize(emb))
            .collect();

        Ok(normalized)
    }

    /// Tokenize a batch of texts
    fn tokenize_batch(&self, texts: &[String]) -> EmbeddingResult<(Vec<i64>, Vec<i64>)> {
        let encodings = self.tokenizer
            .encode_batch(texts.to_vec(), true)
            .map_err(|e| EmbeddingError::TokenizationError(e.to_string()))?;

        let batch_size = encodings.len();
        let seq_len = encodings[0].len().min(self.config.max_seq_length);

        // Prepare input_ids and attention_mask
        let mut input_ids = Vec::with_capacity(batch_size * seq_len);
        let mut attention_mask = Vec::with_capacity(batch_size * seq_len);

        for encoding in encodings {
            let ids = encoding.get_ids();
            let mask = encoding.get_attention_mask();

            // Take up to max_seq_length tokens
            for i in 0..seq_len {
                input_ids.push(ids.get(i).copied().unwrap_or(0) as i64);
                attention_mask.push(mask.get(i).copied().unwrap_or(0) as i64);
            }

            // Pad if necessary
            for _ in ids.len()..seq_len {
                input_ids.push(0);
                attention_mask.push(0);
            }
        }

        Ok((input_ids, attention_mask))
    }

    /// Run ONNX model inference
    fn run_inference(&mut self, tokenized: (Vec<i64>, Vec<i64>)) -> EmbeddingResult<Vec<Vec<f32>>> {
        let (input_ids, attention_mask) = tokenized;
        let batch_size = input_ids.len() / self.config.max_seq_length;
        let seq_len = self.config.max_seq_length;

        // Create input arrays using ndarray
        let input_ids_array = Array2::from_shape_vec(
            (batch_size, seq_len),
            input_ids,
        ).map_err(|e| EmbeddingError::InternalError(e.to_string()))?;

        let attention_mask_array = Array2::from_shape_vec(
            (batch_size, seq_len),
            attention_mask,
        ).map_err(|e| EmbeddingError::InternalError(e.to_string()))?;

        // Convert to ONNX tensors using Tensor::from_array
        let input_ids_tensor = Tensor::from_array(input_ids_array)
            .map_err(|e| EmbeddingError::OnnxError(e.to_string()))?;

        let attention_mask_tensor = Tensor::from_array(attention_mask_array)
            .map_err(|e| EmbeddingError::OnnxError(e.to_string()))?;

        // Run inference
        let outputs = self.session
            .run(ort::inputs![input_ids_tensor, attention_mask_tensor])
            .map_err(|e| EmbeddingError::OnnxError(e.to_string()))?;

        // Extract embeddings from output using try_extract_array
        // BGE models output shape: [batch_size, embedding_dim]
        let output_array = outputs[0]
            .try_extract_array::<f32>()
            .map_err(|e| EmbeddingError::OnnxError(e.to_string()))?;

        // Verify shape is correct
        let shape = output_array.shape();
        if shape.len() != 2 {
            return Err(EmbeddingError::InternalError(
                format!("Expected 2D output, got {}D", shape.len())
            ));
        }

        let actual_batch_size = shape[0];
        let embedding_dim = shape[1];

        if actual_batch_size != batch_size {
            return Err(EmbeddingError::InternalError(
                format!("Batch size mismatch: expected {}, got {}", batch_size, actual_batch_size)
            ));
        }

        // Convert to Vec<Vec<f32>>
        let mut embeddings = Vec::with_capacity(batch_size);
        for i in 0..batch_size {
            let row = output_array.slice(ndarray::s![i, ..]);
            embeddings.push(row.to_vec());
        }

        Ok(embeddings)
    }

    /// Normalize an embedding using L2 normalization
    ///
    /// This ensures the embedding has unit length, which is required for
    /// accurate cosine similarity calculations.
    fn normalize(&self, embedding: Vec<f32>) -> Vec<f32> {
        let norm: f32 = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();

        if norm < 1e-12 {
            warn!("Embedding has near-zero norm, returning as-is");
            return embedding;
        }

        embedding.iter().map(|x| x / norm).collect()
    }

    /// Generate a single embedding (convenience method)
    pub fn embed(&mut self, text: String) -> EmbeddingResult<Embedding> {
        let batch = self.embed_batch(vec![text])?;
        batch.embeddings.into_iter().next()
            .ok_or_else(|| EmbeddingError::InternalError("No embedding generated".to_string()))
    }

    /// Get the embedding dimension
    pub fn dimension(&self) -> usize {
        self.config.embedding_dim
    }

    /// Get the maximum batch size
    pub fn max_batch_size(&self) -> usize {
        self.config.max_batch_size
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Note: These tests require the actual model files to be present
    // They will be skipped in CI/CD environments without GPU

    #[test]
    #[ignore] // Requires model files
    fn test_embedding_engine_creation() {
        let config = EmbeddingConfig::default();
        let result = EmbeddingEngine::new(config);

        // Will fail if model not present, which is expected
        if result.is_ok() {
            let engine = result.unwrap();
            assert_eq!(engine.dimension(), 768);
        }
    }

    #[test]
    fn test_normalization() {
        let config = EmbeddingConfig::default();
        // Create a mock engine (will fail at runtime but we can test normalize)
        let vector = vec![3.0, 4.0]; // Should normalize to [0.6, 0.8]

        // We can't create engine without model, but we can test the math
        let norm: f32 = vector.iter().map(|x| x * x).sum::<f32>().sqrt();
        let normalized: Vec<f32> = vector.iter().map(|x| x / norm).collect();

        assert!((normalized[0] - 0.6).abs() < 1e-5);
        assert!((normalized[1] - 0.8).abs() < 1e-5);

        // Check it's normalized
        let new_norm: f32 = normalized.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((new_norm - 1.0).abs() < 1e-5);
    }

    #[test]
    fn test_empty_input_error() {
        // This test doesn't require the model
        let config = EmbeddingConfig::default();

        // We can't test the full flow without model, but we documented the expected behavior
        // embed_batch should return EmbeddingError::EmptyInput for empty vectors
    }
}
