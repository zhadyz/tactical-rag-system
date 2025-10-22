// Ollama Detection and Configuration
// Simplified for Qwen model integration

use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OllamaStatus {
    pub installed: bool,
    pub running: bool,
    pub version: Option<String>,
    pub models: Vec<String>,
    pub qwen_available: bool,
    pub recommended_model: String,
}

impl Default for OllamaStatus {
    fn default() -> Self {
        Self {
            installed: false,
            running: false,
            version: None,
            models: Vec::new(),
            qwen_available: false,
            recommended_model: "qwen2.5:14b-instruct-q4_K_M".to_string(),
        }
    }
}

/// Detect if Ollama is installed on the system
pub fn detect_ollama() -> OllamaStatus {
    let mut status = OllamaStatus::default();

    // Check if ollama command exists
    let ollama_check = if cfg!(target_os = "windows") {
        Command::new("where").arg("ollama").output()
    } else {
        Command::new("which").arg("ollama").output()
    };

    match ollama_check {
        Ok(output) if output.status.success() => {
            status.installed = true;
            log::info!("Ollama detected in PATH");

            // Get version
            if let Ok(version_output) = Command::new("ollama").arg("--version").output() {
                if version_output.status.success() {
                    if let Ok(version_str) = String::from_utf8(version_output.stdout) {
                        status.version = Some(version_str.trim().to_string());
                        log::info!("Ollama version: {}", version_str.trim());
                    }
                }
            }

            // Check if Ollama service is running
            status.running = check_ollama_service();

            // Get installed models
            if status.running {
                status.models = get_installed_models();
                status.qwen_available = status.models.iter().any(|m| m.contains("qwen"));
                log::info!("Found {} installed models", status.models.len());
                if status.qwen_available {
                    log::info!("Qwen model is available");
                }
            }
        }
        _ => {
            log::warn!("Ollama not found in PATH");
            status.installed = false;
        }
    }

    status
}

/// Check if Ollama service is running by trying to connect
fn check_ollama_service() -> bool {
    // Try to connect to Ollama API
    match std::net::TcpStream::connect("127.0.0.1:11434") {
        Ok(_) => {
            log::info!("Ollama service is running on localhost:11434");
            true
        }
        Err(_) => {
            log::warn!("Ollama service not running on localhost:11434");
            false
        }
    }
}

/// Get list of installed Ollama models
fn get_installed_models() -> Vec<String> {
    match Command::new("ollama").arg("list").output() {
        Ok(output) if output.status.success() => {
            if let Ok(output_str) = String::from_utf8(output.stdout) {
                // Parse ollama list output
                output_str
                    .lines()
                    .skip(1) // Skip header
                    .filter_map(|line| {
                        line.split_whitespace()
                            .next()
                            .map(|s| s.to_string())
                    })
                    .collect()
            } else {
                Vec::new()
            }
        }
        _ => {
            log::warn!("Failed to get Ollama models list");
            Vec::new()
        }
    }
}

/// Pull a model from Ollama registry
pub async fn pull_model(model_name: &str) -> Result<(), String> {
    log::info!("Pulling model: {}", model_name);

    let output = tokio::process::Command::new("ollama")
        .arg("pull")
        .arg(model_name)
        .output()
        .await
        .map_err(|e| format!("Failed to execute ollama pull: {}", e))?;

    if output.status.success() {
        log::info!("Successfully pulled model: {}", model_name);
        Ok(())
    } else {
        let error = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to pull model: {}", error))
    }
}

/// Verify Qwen model is available, pull if not
pub async fn ensure_qwen_model(model_name: &str) -> Result<(), String> {
    let status = detect_ollama();

    if !status.installed {
        return Err("Ollama not installed. Please install from https://ollama.com".to_string());
    }

    if !status.running {
        return Err("Ollama service not running. Please start Ollama.".to_string());
    }

    // Check if model already exists
    if status.models.iter().any(|m| m == model_name) {
        log::info!("Qwen model {} already installed", model_name);
        return Ok(());
    }

    // Model not found, pull it
    log::info!("Qwen model not found, pulling: {}", model_name);
    pull_model(model_name).await
}

// Tauri Commands

#[tauri::command]
pub fn get_ollama_status() -> OllamaStatus {
    detect_ollama()
}

#[tauri::command]
pub async fn pull_qwen_model(model: String) -> Result<(), String> {
    pull_model(&model).await
}

#[tauri::command]
pub async fn verify_qwen() -> Result<(), String> {
    let recommended = "qwen2.5:14b-instruct-q4_K_M";
    ensure_qwen_model(recommended).await
}

#[tauri::command]
pub fn get_recommended_qwen_model() -> String {
    "qwen2.5:14b-instruct-q4_K_M".to_string()
}
