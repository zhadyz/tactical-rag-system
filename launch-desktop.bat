@echo off
echo ========================================
echo  Tactical RAG Desktop v4.0
echo  Launching Tauri Application...
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Rust installation...
where cargo >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Cargo not found in PATH
    echo.
    echo Please ensure Rust is installed and in your PATH.
    echo You can install Rust from: https://rustup.rs/
    echo.
    echo After installation, restart your terminal and run this script again.
    pause
    exit /b 1
)

echo Cargo found! Starting Tauri development server...
echo.
echo This will:
echo  1. Compile the Rust backend with Ollama integration
echo  2. Start the React frontend
echo  3. Launch the desktop window
echo.
echo Please wait, this may take a minute on first run...
echo.

npm run tauri dev

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to start Tauri app
    echo.
    echo Please check the error messages above.
    pause
)
