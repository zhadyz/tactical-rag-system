// ATLAS Protocol - Tauri Commands
// ================================
//
// Backend integration commands for V4.0 desktop application.
// Connects React frontend to ATLAS FastAPI backend.

use serde::{Deserialize, Serialize};
use tauri::State;
use std::sync::Arc;
use tokio::sync::Mutex;

/// Health status response from backend
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthStatus {
    pub status: String,
    pub backend: String,
    pub version: String,
    pub models: ModelsStatus,
    pub cache: CacheStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelsStatus {
    pub llm: String,
    pub embeddings: String,
    pub vector_db: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheStatus {
    pub redis_connected: bool,
    pub hit_rate: f64,
}

/// Application state
pub struct AppState {
    pub backend_url: String,
    pub http_client: reqwest::Client,
}

impl AppState {
    pub fn new(backend_url: String) -> Self {
        Self {
            backend_url,
            http_client: reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(30))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }
}

/// Check ATLAS backend health
#[tauri::command]
pub async fn check_atlas_health(
    state: State<'_, Arc<Mutex<AppState>>>
) -> Result<HealthStatus, String> {
    let state = state.lock().await;
    let url = format!("{}/api/health", state.backend_url);

    let response = state.http_client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Backend unreachable: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Backend returned error: {}", response.status()));
    }

    let health: HealthStatus = response
        .json()
        .await
        .map_err(|e| format!("Invalid response format: {}", e))?;

    Ok(health)
}

/// Check if backend is connected (simple connectivity check)
#[tauri::command]
pub async fn check_backend_connected(
    state: State<'_, Arc<Mutex<AppState>>>
) -> Result<bool, String> {
    let state = state.lock().await;
    let url = format!("{}/api/health", state.backend_url);

    match state.http_client.get(&url).send().await {
        Ok(response) => Ok(response.status().is_success()),
        Err(_) => Ok(false),
    }
}

/// Get cache statistics
#[tauri::command]
pub async fn get_cache_stats(
    state: State<'_, Arc<Mutex<AppState>>>
) -> Result<CacheStats, String> {
    let state = state.lock().await;
    let url = format!("{}/api/cache/metrics", state.backend_url);

    let response = state.http_client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch cache stats: {}", e))?;

    let stats: CacheStats = response
        .json()
        .await
        .map_err(|e| format!("Invalid response: {}", e))?;

    Ok(stats)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheStats {
    pub hit_rate: f64,
    pub total_requests: u64,
    pub cache_hits: u64,
    pub cache_misses: u64,
    pub avg_latency_ms: f64,
}

/// Get available models
#[tauri::command]
pub async fn get_available_models(
    state: State<'_, Arc<Mutex<AppState>>>
) -> Result<Vec<String>, String> {
    let state = state.lock().await;
    let url = format!("{}/api/models", state.backend_url);

    let response = state.http_client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch models: {}", e))?;

    let models: Vec<String> = response
        .json()
        .await
        .map_err(|e| format!("Invalid response: {}", e))?;

    Ok(models)
}

/// Open URL in default browser
#[tauri::command]
pub fn open_url(url: String) -> Result<(), String> {
    open::that(&url)
        .map_err(|e| format!("Failed to open URL: {}", e))
}

/// Show notification
#[tauri::command]
pub fn show_notification(title: String, body: String) -> Result<(), String> {
    // Note: Requires tauri-plugin-notification
    // For now, just log
    println!("Notification: {} - {}", title, body);
    Ok(())
}

// ============================================================
// MODEL HOTSWAP COMMANDS
// ============================================================

/// Model information (detailed)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub id: String,
    pub name: String,
    pub backend: String,
    pub description: String,
    pub expected_vram_gb: f64,
    pub expected_tokens_per_sec: f64,
    pub active: bool,
}

/// Model switch response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelSwitchResponse {
    pub success: bool,
    pub message: String,
    pub previous_model: Option<String>,
    pub current_model: Option<String>,
}

/// Get detailed list of available models for hotswapping
#[tauri::command]
pub async fn get_models_list(
    state: State<'_, Arc<Mutex<AppState>>>
) -> Result<Vec<ModelInfo>, String> {
    let state = state.lock().await;
    let url = format!("{}/api/models/available", state.backend_url);

    let response = state.http_client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch models: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Backend returned error: {}", response.status()));
    }

    let models: Vec<ModelInfo> = response
        .json()
        .await
        .map_err(|e| format!("Invalid response: {}", e))?;

    Ok(models)
}

/// Get currently active model
#[tauri::command]
pub async fn get_current_model(
    state: State<'_, Arc<Mutex<AppState>>>
) -> Result<ModelInfo, String> {
    let state = state.lock().await;
    let url = format!("{}/api/models/current", state.backend_url);

    let response = state.http_client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch current model: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Backend returned error: {}", response.status()));
    }

    let model: ModelInfo = response
        .json()
        .await
        .map_err(|e| format!("Invalid response: {}", e))?;

    Ok(model)
}

/// Switch to a different model at runtime
#[tauri::command]
pub async fn switch_model(
    model_id: String,
    state: State<'_, Arc<Mutex<AppState>>>
) -> Result<ModelSwitchResponse, String> {
    let state = state.lock().await;
    let url = format!("{}/api/models/switch", state.backend_url);

    #[derive(Serialize)]
    struct SwitchRequest {
        model_id: String,
    }

    let request = SwitchRequest { model_id };

    let response = state.http_client
        .post(&url)
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Failed to switch model: {}", e))?;

    if !response.status().is_success() {
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        return Err(format!("Model switch failed: {}", error_text));
    }

    let switch_response: ModelSwitchResponse = response
        .json()
        .await
        .map_err(|e| format!("Invalid response: {}", e))?;

    Ok(switch_response)
}
