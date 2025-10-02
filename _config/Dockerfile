
# This is a Dockerfile - a recipe to build a Docker image
# Each line is an instruction that runs in order

# ============================================================
# STEP 1: Choose a base image (starting point)
# ============================================================
# We use Python 3.11 on Debian (slim = smaller size)
FROM python:3.11-slim

# ============================================================
# STEP 2: Set metadata 
# ============================================================
LABEL maintainer="Abdul.baril@us.af.mil"
LABEL description="Tactical RAG Document Intelligence System"

# ============================================================
# STEP 3: Install system dependencies
# ============================================================
# Update package lists and install required system tools
# These are needed for Tesseract OCR and Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*
# The last line cleans up to keep image size small

# ============================================================
# STEP 4: Set working directory
# ============================================================
# All future commands will run from this directory inside the container
WORKDIR /app

# ============================================================
# STEP 5: Copy requirements and install Python packages
# ============================================================
# Copy requirements.txt first (Docker caching optimization)
# If requirements don't change, this layer is cached and faster
COPY _config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# STEP 6: Copy application code
# ============================================================
# Copy all your application files into the container
COPY _src/*.py /app/

# ============================================================
# STEP 7: Create necessary directories
# ============================================================
# Make sure documents and database folders exist
RUN mkdir -p /app/documents /app/chroma_db

# Copy and setup startup script
COPY _config/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# ============================================================
# STEP 8: Expose the port
# ============================================================
# Tell Docker that this container will listen on port 7860
# This doesn't actually publish the port, just documents it
EXPOSE 7860

# ============================================================
# STEP 9: Set environment variables
# ============================================================
# Configure the application environment
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME=0.0.0.0

# ============================================================
# STEP 10: Define the startup command
# ============================================================
# This runs when the container starts
# We'll use a shell script to handle both indexing and running the app
# Copy and make startup script executable


CMD ["/app/startup.sh"]