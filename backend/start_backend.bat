@echo off
REM Tactical RAG Backend - Quick Start Script (Windows)
REM This script starts the backend API server locally

echo ========================================================================
echo   TACTICAL RAG BACKEND - QUICK START (Windows)
echo ========================================================================
echo.

REM Check if we're in the right directory
if not exist "app\main.py" (
    echo Error: Must run from backend\ directory
    echo Usage: cd backend ^&^& start_backend.bat
    exit /b 1
)

REM Check Python version
echo 1. Checking Python version...
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo 2. Creating virtual environment...
    python -m venv venv
    echo    Virtual environment created
) else (
    echo 2. Using existing virtual environment
)
echo.

REM Activate virtual environment
echo 3. Activating virtual environment...
call venv\Scripts\activate.bat
echo    Virtual environment activated
echo.

REM Install dependencies
echo 4. Installing dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
echo    Dependencies installed
echo.

REM Set environment variables (defaults)
echo 5. Setting environment configuration...
if not defined OLLAMA_HOST set OLLAMA_HOST=http://localhost:11434
if not defined RAG_VECTOR_DB_DIR set RAG_VECTOR_DB_DIR=..\chroma_db
if not defined RAG_DOCUMENTS_DIR set RAG_DOCUMENTS_DIR=..\documents
if not defined RAG_CACHE__USE_REDIS set RAG_CACHE__USE_REDIS=true
if not defined RAG_CACHE__REDIS_HOST set RAG_CACHE__REDIS_HOST=localhost
if not defined RAG_CACHE__REDIS_PORT set RAG_CACHE__REDIS_PORT=6379

echo    OLLAMA_HOST:          %OLLAMA_HOST%
echo    RAG_VECTOR_DB_DIR:    %RAG_VECTOR_DB_DIR%
echo    RAG_DOCUMENTS_DIR:    %RAG_DOCUMENTS_DIR%
echo    RAG_CACHE__USE_REDIS: %RAG_CACHE__USE_REDIS%
echo    RAG_CACHE__REDIS_HOST: %RAG_CACHE__REDIS_HOST%
echo.

REM Check if vector database exists
echo 6. Checking vector database...
if exist "%RAG_VECTOR_DB_DIR%\" (
    echo    Vector database found at %RAG_VECTOR_DB_DIR%
) else (
    echo    ERROR: Vector database not found
    echo    Please run indexing first: python _src\index_documents.py
    exit /b 1
)
echo.

REM Start the server
echo ========================================================================
echo   STARTING BACKEND SERVER
echo ========================================================================
echo.
echo Server will be available at:
echo   - API:     http://localhost:8000
echo   - Docs:    http://localhost:8000/docs
echo   - Health:  http://localhost:8000/api/health
echo.
echo Press Ctrl+C to stop
echo.

REM Start uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
