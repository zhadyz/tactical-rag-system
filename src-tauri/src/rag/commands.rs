// ATLAS Protocol - Phase 1: Tauri Commands
// Frontend interface for embedding operations

use std::sync::{Arc, Mutex};
use serde::{Deserialize, Serialize};
use tauri::State;

use crate::rag::{EmbeddingEngine, EmbeddingConfig, EmbeddingBatch};

/// Shared state for the embedding engine
pub struct EmbeddingState {
    pub engine: Option<EmbeddingEngine>,
}

impl Default for EmbeddingState {
    fn default() -> Self {
        Self { engine: None }
    }
}

/// Response for embedding operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingResponse {
    /// The generated embedding vectors
    pub embeddings: Vec<Vec<f32>>,
    /// Number of embeddings generated
    pub count: usize,
    /// Processing time in milliseconds
    pub time_ms: f64,
    /// Average time per embedding
    pub avg_time_ms: f64,
    /// Success flag
    pub success: bool,
    /// Error message if any
    pub error: Option<String>,
}

impl From<EmbeddingBatch> for EmbeddingResponse {
    fn from(batch: EmbeddingBatch) -> Self {
        let embeddings = batch.clone().into_vectors();
        Self {
            embeddings,
            count: batch.count,
            time_ms: batch.total_time_ms,
            avg_time_ms: batch.avg_time_ms,
            success: true,
            error: None,
        }
    }
}

impl EmbeddingResponse {
    fn error(message: String) -> Self {
        Self {
            embeddings: Vec::new(),
            count: 0,
            time_ms: 0.0,
            avg_time_ms: 0.0,
            success: false,
            error: Some(message),
        }
    }
}

/// Initialize the embedding engine
///
/// This command should be called once at application startup.
/// It loads the ONNX model and prepares the GPU for inference.
#[tauri::command]
pub async fn init_embedding_engine(
    state: State<'_, Arc<Mutex<EmbeddingState>>>,
) -> Result<String, String> {
    let mut state = state.lock().unwrap();

    if state.engine.is_some() {
        return Ok("Embedding engine already initialized".to_string());
    }

    // Use RTX 5080 optimized configuration
    let config = EmbeddingConfig::for_rtx_5080();

    match EmbeddingEngine::new(config) {
        Ok(engine) => {
            state.engine = Some(engine);
            Ok("Embedding engine initialized successfully".to_string())
        }
        Err(e) => Err(format!("Failed to initialize embedding engine: {}", e)),
    }
}

/// Generate embeddings for a batch of texts
///
/// This is the main command for embedding generation.
/// It handles batching automatically based on the configured batch size.
#[tauri::command]
pub async fn generate_embeddings(
    texts: Vec<String>,
    state: State<'_, Arc<Mutex<EmbeddingState>>>,
) -> Result<EmbeddingResponse, String> {
    let mut state = state.lock().unwrap();

    let engine = state.engine.as_mut()
        .ok_or_else(|| "Embedding engine not initialized. Call init_embedding_engine first.".to_string())?;

    match engine.embed_batch(texts) {
        Ok(batch) => Ok(EmbeddingResponse::from(batch)),
        Err(e) => {
            log::error!("Embedding generation failed: {}", e);
            Ok(EmbeddingResponse::error(e.to_string()))
        }
    }
}

/// Generate a single embedding (convenience method)
#[tauri::command]
pub async fn generate_embedding(
    text: String,
    state: State<'_, Arc<Mutex<EmbeddingState>>>,
) -> Result<Vec<f32>, String> {
    let mut state = state.lock().unwrap();

    let engine = state.engine.as_mut()
        .ok_or_else(|| "Embedding engine not initialized".to_string())?;

    match engine.embed(text) {
        Ok(embedding) => Ok(embedding.vector),
        Err(e) => Err(e.to_string()),
    }
}

/// Get embedding engine status
#[tauri::command]
pub fn get_embedding_status(
    state: State<'_, Arc<Mutex<EmbeddingState>>>,
) -> Result<EmbeddingEngineStatus, String> {
    let state = state.lock().unwrap();

    match &state.engine {
        Some(engine) => Ok(EmbeddingEngineStatus {
            initialized: true,
            dimension: engine.dimension(),
            max_batch_size: engine.max_batch_size(),
            model_loaded: true,
        }),
        None => Ok(EmbeddingEngineStatus {
            initialized: false,
            dimension: 0,
            max_batch_size: 0,
            model_loaded: false,
        }),
    }
}

/// Status response for embedding engine
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingEngineStatus {
    pub initialized: bool,
    pub dimension: usize,
    pub max_batch_size: usize,
    pub model_loaded: bool,
}
