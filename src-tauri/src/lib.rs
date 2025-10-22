mod sidecar;
mod ollama;

use std::sync::{Arc, Mutex};
use sidecar::BackendSidecar;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    // Register all plugins
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_dialog::init())
    .plugin(tauri_plugin_store::Builder::default().build())
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
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
