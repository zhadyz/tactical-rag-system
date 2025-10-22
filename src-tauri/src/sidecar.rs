// Backend Sidecar Process Management
// Handles lifecycle of the FastAPI backend as a Tauri sidecar

use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::AppHandle;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendStatus {
    pub running: bool,
    pub healthy: bool,
    pub port: u16,
    pub last_check: String,
    pub error: Option<String>,
}

pub struct BackendSidecar {
    status: Arc<Mutex<BackendStatus>>,
    app_handle: AppHandle,
}

impl BackendSidecar {
    pub fn new(app_handle: AppHandle) -> Self {
        let status = Arc::new(Mutex::new(BackendStatus {
            running: false,
            healthy: false,
            port: 8000,
            last_check: chrono::Utc::now().to_rfc3339(),
            error: None,
        }));

        Self {
            status,
            app_handle,
        }
    }

    /// Start the backend sidecar process
    pub async fn start(&self) -> Result<(), String> {
        log::info!("Starting backend sidecar...");

        // For V4.0, we'll connect to Docker backend during development
        // Production will use bundled Python executable

        // Update status
        {
            let mut status = self.status.lock().unwrap();
            status.running = true;
            status.last_check = chrono::Utc::now().to_rfc3339();
        }

        // Start health monitoring
        self.start_health_monitor();

        log::info!("Backend sidecar started");
        Ok(())
    }

    /// Stop the backend sidecar process
    pub fn stop(&self) -> Result<(), String> {
        log::info!("Stopping backend sidecar...");

        {
            let mut status = self.status.lock().unwrap();
            status.running = false;
            status.healthy = false;
        }

        log::info!("Backend sidecar stopped");
        Ok(())
    }

    /// Get current backend status
    pub fn get_status(&self) -> BackendStatus {
        self.status.lock().unwrap().clone()
    }

    /// Check if backend is healthy
    async fn check_health(&self) -> bool {
        let client = reqwest::Client::new();

        match client
            .get("http://localhost:8000/api/health")
            .timeout(Duration::from_secs(5))
            .send()
            .await
        {
            Ok(response) => {
                let healthy = response.status().is_success();
                log::debug!("Health check: {}", if healthy { "OK" } else { "FAIL" });
                healthy
            }
            Err(e) => {
                log::warn!("Health check failed: {}", e);
                false
            }
        }
    }

    /// Start background health monitoring
    fn start_health_monitor(&self) {
        let status = Arc::clone(&self.status);

        tauri::async_runtime::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_secs(10)).await;

                // Check if backend is still running
                let is_running = {
                    let s = status.lock().unwrap();
                    s.running
                };

                if !is_running {
                    break;
                }

                // Perform health check
                let client = reqwest::Client::new();
                let healthy = match client
                    .get("http://localhost:8000/api/health")
                    .timeout(Duration::from_secs(5))
                    .send()
                    .await
                {
                    Ok(response) => response.status().is_success(),
                    Err(_) => false,
                };

                // Update status
                {
                    let mut s = status.lock().unwrap();
                    s.healthy = healthy;
                    s.last_check = chrono::Utc::now().to_rfc3339();
                    if !healthy {
                        s.error = Some("Backend health check failed".to_string());
                    } else {
                        s.error = None;
                    }
                }
            }
        });
    }
}

// Tauri Commands

#[tauri::command]
pub async fn start_backend(
    state: tauri::State<'_, Arc<Mutex<Option<BackendSidecar>>>>,
) -> Result<(), String> {
    // Clone Arc to avoid holding lock across await
    let sidecar_clone = {
        let sidecar_opt = state.lock().unwrap();
        sidecar_opt.as_ref().map(|s| Arc::new(Mutex::new(s.status.clone())))
    };

    if sidecar_clone.is_some() {
        // Simulate backend start (connect to Docker)
        log::info!("Backend sidecar started");
        Ok(())
    } else {
        Err("Backend sidecar not initialized".to_string())
    }
}

#[tauri::command]
pub fn stop_backend(
    state: tauri::State<'_, Arc<Mutex<Option<BackendSidecar>>>>,
) -> Result<(), String> {
    let sidecar_opt = state.lock().unwrap();
    if let Some(sidecar) = sidecar_opt.as_ref() {
        sidecar.stop()
    } else {
        Err("Backend sidecar not initialized".to_string())
    }
}

#[tauri::command]
pub fn get_backend_status(
    state: tauri::State<'_, Arc<Mutex<Option<BackendSidecar>>>>,
) -> Result<BackendStatus, String> {
    let sidecar_opt = state.lock().unwrap();
    if let Some(sidecar) = sidecar_opt.as_ref() {
        Ok(sidecar.get_status())
    } else {
        Err("Backend sidecar not initialized".to_string())
    }
}
