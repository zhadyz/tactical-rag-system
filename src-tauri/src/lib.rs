mod sidecar;
mod ollama;
// mod rag;  // Commented out: Backend handles embeddings via Python
mod commands;

use std::sync::{Arc, Mutex};
use sidecar::BackendSidecar;
// use rag::EmbeddingState;  // Commented out: Backend handles embeddings
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    // Register all plugins
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_dialog::init())
    .plugin(tauri_plugin_store::Builder::default().build())
    .plugin(tauri_plugin_shell::init())
    .setup(|app| {
      // Enable logging in debug mode
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      // Initialize backend sidecar
      let sidecar = BackendSidecar::new(app.handle().clone());
      let sidecar_state = Arc::new(Mutex::new(Some(sidecar)));
      app.manage(sidecar_state);

      // Initialize ATLAS embedding state
      // Commented out: Backend handles embeddings via Python
      // let embedding_state = Arc::new(Mutex::new(EmbeddingState::default()));
      // app.manage(embedding_state);

      // Initialize ATLAS backend state
      let backend_url = std::env::var("ATLAS_BACKEND_URL")
        .unwrap_or_else(|_| "http://localhost:8000".to_string());
      log::info!("ATLAS backend URL: {}", backend_url);

      let app_state = Arc::new(tokio::sync::Mutex::new(
        commands::AppState::new(backend_url)
      ));
      app.manage(app_state);

      // Auto-start backend in development mode (disabled for now)
      // Backend sidecar will be started manually or via Docker
      if cfg!(debug_assertions) {
        log::info!("Development mode: Backend sidecar available for manual start");
      }

      Ok(())
    })
    // Register Tauri commands
    .invoke_handler(tauri::generate_handler![
      sidecar::start_backend,
      sidecar::stop_backend,
      sidecar::get_backend_status,
      ollama::get_ollama_status,
      ollama::pull_qwen_model,
      ollama::verify_qwen,
      ollama::get_recommended_qwen_model,
      // ATLAS Protocol - Embedding Commands (Commented out: Backend handles embeddings via Python)
      // rag::commands::init_embedding_engine,
      // rag::commands::generate_embeddings,
      // rag::commands::generate_embedding,
      // rag::commands::get_embedding_status,
      // ATLAS Protocol - Backend Integration Commands
      commands::check_atlas_health,
      commands::check_backend_connected,
      commands::get_cache_stats,
      commands::get_available_models,
      commands::open_url,
      commands::show_notification,
      // ATLAS Protocol - Model Hotswap Commands
      commands::get_models_list,
      commands::get_current_model,
      commands::switch_model,
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
