#!/bin/bash
# Build backend binary using Docker
# This avoids Python 3.14 dependency conflicts on Windows host

set -e

echo "========================================"
echo "Tactical RAG Backend Binary Build"
echo "========================================"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"

echo "Building Docker image for PyInstaller..."
docker build -f Dockerfile.pyinstaller -t tactical-rag-pyinstaller ..

echo ""
echo "Extracting binary from Docker container..."

# Create output directory
mkdir -p dist

# Run container and copy binary
docker create --name tactical-rag-build tactical-rag-pyinstaller
docker cp tactical-rag-build:/app/backend/dist/tactical-rag-backend ./dist/
docker rm tactical-rag-build

echo ""
echo "✓ Build complete!"
echo "Binary location: dist/tactical-rag-backend/"
echo ""

# List contents
ls -lh dist/tactical-rag-backend/ | head -20

echo ""
echo "To test the binary:"
echo "  cd dist/tactical-rag-backend"
echo "  ./tactical-rag-backend.exe"
