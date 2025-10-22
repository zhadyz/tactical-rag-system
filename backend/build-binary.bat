@echo off
REM Build backend binary using Docker (Windows)
REM This avoids Python 3.14 dependency conflicts on Windows host

echo ========================================
echo Tactical RAG Backend Binary Build
echo ========================================
echo.

cd /d "%~dp0"

echo Building Docker image for PyInstaller...
docker build -f Dockerfile.pyinstaller -t tactical-rag-pyinstaller ..

echo.
echo Extracting binary from Docker container...

REM Create output directory
if not exist dist mkdir dist

REM Run container and copy binary
docker create --name tactical-rag-build tactical-rag-pyinstaller
docker cp tactical-rag-build:/app/backend/dist/tactical-rag-backend ./dist/
docker rm tactical-rag-build

echo.
echo Build complete!
echo Binary location: dist\tactical-rag-backend\
echo.

REM List contents
dir dist\tactical-rag-backend

echo.
echo To test the binary:
echo   cd dist\tactical-rag-backend
echo   tactical-rag-backend.exe
