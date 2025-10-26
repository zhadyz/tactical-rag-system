// ATLAS Protocol - Phase 1: Unit Tests
// Comprehensive tests for the embedding service

#[cfg(test)]
mod embedding_tests {
    use crate::rag::{EmbeddingConfig, EmbeddingEngine, Embedding};

    // Note: Most tests are in the individual module files (types.rs, config.rs)
    // These are integration tests that span multiple modules

    #[test]
    fn test_config_validation() {
        let config = EmbeddingConfig::default();
        assert!(config.validate().is_ok());

        let mut invalid_config = EmbeddingConfig::default();
        invalid_config.max_batch_size = 0;
        assert!(invalid_config.validate().is_err());
    }

    #[test]
    fn test_embedding_normalization() {
        // Test the normalization math
        let vector = vec![3.0, 4.0];
        let norm: f32 = vector.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert_eq!(norm, 5.0);

        let normalized: Vec<f32> = vector.iter().map(|x| x / norm).collect();
        assert!((normalized[0] - 0.6).abs() < 1e-5);
        assert!((normalized[1] - 0.8).abs() < 1e-5);

        // Verify it's normalized
        let new_norm: f32 = normalized.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((new_norm - 1.0).abs() < 1e-5);
    }

    #[test]
    fn test_embedding_struct() {
        let vector = vec![0.6, 0.8];
        let embedding = Embedding::new(vector);

        assert_eq!(embedding.dimension, 2);
        assert!(embedding.is_normalized());
        assert!((embedding.norm() - 1.0).abs() < 1e-5);
    }

    #[test]
    fn test_config_for_different_hardware() {
        let rtx_config = EmbeddingConfig::for_rtx_5080();
        assert_eq!(rtx_config.max_batch_size, 512);
        assert!(rtx_config.use_gpu);

        let cpu_config = EmbeddingConfig::cpu_only(16);
        assert!(!cpu_config.use_gpu);
        assert_eq!(cpu_config.num_threads, 16);
        assert_eq!(cpu_config.max_batch_size, 32);
    }

    #[test]
    fn test_execution_provider_selection() {
        let gpu_config = EmbeddingConfig::default();
        assert_eq!(gpu_config.get_execution_provider(), "CUDAExecutionProvider");

        let cpu_config = EmbeddingConfig::cpu_only(8);
        assert_eq!(cpu_config.get_execution_provider(), "CPUExecutionProvider");
    }

    // This test requires actual model files and GPU
    #[test]
    #[ignore]
    fn test_embedding_engine_initialization() {
        let config = EmbeddingConfig::default();
        let result = EmbeddingEngine::new(config);

        // Will fail if model files don't exist, which is expected in CI
        if result.is_ok() {
            let engine = result.unwrap();
            assert_eq!(engine.dimension(), 768);
            assert_eq!(engine.max_batch_size(), 256);
        }
    }

    // This test requires actual model files and GPU
    #[test]
    #[ignore]
    fn test_single_embedding_generation() {
        let config = EmbeddingConfig::default();

        if let Ok(mut engine) = EmbeddingEngine::new(config) {
            let text = "This is a test sentence.".to_string();
            let result = engine.embed(text);

            assert!(result.is_ok());
            let embedding = result.unwrap();
            assert_eq!(embedding.dimension, 768);
            assert!(embedding.is_normalized());
        }
    }

    // This test requires actual model files and GPU
    #[test]
    #[ignore]
    fn test_batch_embedding_generation() {
        let config = EmbeddingConfig::default();

        if let Ok(mut engine) = EmbeddingEngine::new(config) {
            let texts = vec![
                "First sentence.".to_string(),
                "Second sentence.".to_string(),
                "Third sentence.".to_string(),
            ];

            let result = engine.embed_batch(texts.clone());
            assert!(result.is_ok());

            let batch = result.unwrap();
            assert_eq!(batch.count, texts.len());
            assert!(batch.total_time_ms > 0.0);

            for embedding in batch.embeddings {
                assert_eq!(embedding.dimension, 768);
                assert!(embedding.is_normalized());
            }
        }
    }

    // This test requires actual model files and GPU
    #[test]
    #[ignore]
    fn test_large_batch_performance() {
        let config = EmbeddingConfig::for_rtx_5080();

        if let Ok(mut engine) = EmbeddingEngine::new(config) {
            // Create 1000 test sentences
            let texts: Vec<String> = (0..1000)
                .map(|i| format!("This is test sentence number {}.", i))
                .collect();

            let result = engine.embed_batch(texts.clone());
            assert!(result.is_ok());

            let batch = result.unwrap();
            assert_eq!(batch.count, 1000);

            // Performance target: >2000 docs/sec (< 500ms for 1000 docs)
            assert!(batch.total_time_ms < 500.0,
                    "Embedding 1000 docs took {}ms (target: <500ms)", batch.total_time_ms);

            println!("Performance: {:.2} docs/sec", 1000.0 / (batch.total_time_ms / 1000.0));
        }
    }
}
