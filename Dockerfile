# Multi-stage Dockerfile for ekko application
# Optimized for Google Cloud Run deployment

# Stage 1: Builder stage for dependencies
FROM python:3.13-slim AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip for better compatibility
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY requirements.txt .

# Create virtual environment and install dependencies with uv
RUN python -m venv .venv
RUN . .venv/bin/activate && uv pip install --no-cache -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 ekko && \
    mkdir -p /app /app/logs /app/audio /app/transcripts /app/chroma && \
    chown -R ekko:ekko /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=ekko:ekko /app/.venv /app/.venv

# Copy application code
COPY --chown=ekko:ekko . .

# Set environment variables
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Environment variables for production
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_THEME_BASE="light"

# Create volume mount points
VOLUME ["/app/logs", "/app/audio", "/app/transcripts", "/app/chroma"]

# Switch to non-root user
USER ekko

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Expose port for Cloud Run
EXPOSE 8080

# Start the Streamlit application
CMD ["streamlit", "run", "ekko_prototype/landing.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
