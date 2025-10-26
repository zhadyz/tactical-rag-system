// ATLAS Protocol - Phase 1: Embedding Configuration
// Configuration for the embedding engine

use std::path::PathBuf;
use serde::{Deserialize, Serialize};

/// Configuration for the embedding engine
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingConfig {
    /// Path to the ONNX model file
    pub model_path: PathBuf,

    /// Path to the tokenizer configuration
    pub tokenizer_path: PathBuf,

    /// Maximum batch size for embedding generation
    /// RTX 5080 can handle 256-512 documents per batch
    pub max_batch_size: usize,

    /// Maximum sequence length for tokenization
    /// BGE-base-en-v1.5 uses 512 tokens
    pub max_seq_length: usize,

    /// Use GPU acceleration (CUDA)
    pub use_gpu: bool,

    /// Number of threads for CPU inference (if GPU disabled)
    pub num_threads: usize,

    /// Expected embedding dimension (768 for BGE-base-en-v1.5)
    pub embedding_dim: usize,
}

impl Default for EmbeddingConfig {
    fn default() -> Self {
        Self {
            model_path: PathBuf::from("models/embeddings/bge-base-en-v1.5.onnx"),
            tokenizer_path: PathBuf::from("models/embeddings/tokenizer.json"),
            max_batch_size: 256,
            max_seq_length: 512,
            use_gpu: true,
            num_threads: 8,
            embedding_dim: 768,
        }
    }
}

impl EmbeddingConfig {
    /// Create a new configuration with custom paths
    pub fn new(model_path: PathBuf, tokenizer_path: PathBuf) -> Self {
        Self {
            model_path,
            tokenizer_path,
            ..Default::default()
        }
    }

    /// Create a configuration optimized for RTX 5080
    pub fn for_rtx_5080() -> Self {
        Self {
            max_batch_size: 512, // RTX 5080 can handle larger batches
            ..Default::default()
        }
    }

    /// Create a CPU-only configuration
    pub fn cpu_only(num_threads: usize) -> Self {
        Self {
            use_gpu: false,
            num_threads,
            max_batch_size: 32, // Smaller batches for CPU
            ..Default::default()
        }
    }

    /// Validate the configuration
    pub fn validate(&self) -> Result<(), String> {
        if self.max_batch_size == 0 {
            return Err("max_batch_size must be greater than 0".to_string());
        }

        if self.max_seq_length == 0 {
            return Err("max_seq_length must be greater than 0".to_string());
        }

        if self.embedding_dim == 0 {
            return Err("embedding_dim must be greater than 0".to_string());
        }

        if !self.use_gpu && self.num_threads == 0 {
            return Err("num_threads must be greater than 0 for CPU mode".to_string());
        }

        Ok(())
    }

    /// Get the execution provider name for ONNX Runtime
    pub fn get_execution_provider(&self) -> &str {
        if self.use_gpu {
            "CUDAExecutionProvider"
        } else {
            "CPUExecutionProvider"
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = EmbeddingConfig::default();
        assert_eq!(config.max_batch_size, 256);
        assert_eq!(config.max_seq_length, 512);
        assert_eq!(config.embedding_dim, 768);
        assert!(config.use_gpu);
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_rtx_5080_config() {
        let config = EmbeddingConfig::for_rtx_5080();
        assert_eq!(config.max_batch_size, 512);
        assert!(config.use_gpu);
    }

    #[test]
    fn test_cpu_config() {
        let config = EmbeddingConfig::cpu_only(16);
        assert!(!config.use_gpu);
        assert_eq!(config.num_threads, 16);
        assert_eq!(config.max_batch_size, 32);
    }

    #[test]
    fn test_validation() {
        let mut config = EmbeddingConfig::default();
        assert!(config.validate().is_ok());

        config.max_batch_size = 0;
        assert!(config.validate().is_err());

        config = EmbeddingConfig::default();
        config.max_seq_length = 0;
        assert!(config.validate().is_err());
    }

    #[test]
    fn test_execution_provider() {
        let gpu_config = EmbeddingConfig::default();
        assert_eq!(gpu_config.get_execution_provider(), "CUDAExecutionProvider");

        let cpu_config = EmbeddingConfig::cpu_only(8);
        assert_eq!(cpu_config.get_execution_provider(), "CPUExecutionProvider");
    }
}
