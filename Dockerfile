# MCP Educational Server - Production Dockerfile
# Optimized for Raspberry Pi (ARM64) deployment

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY main.py .

# Create data directories
RUN mkdir -p data/incoming data/processed data/failed data/jsonl data/statistics

# Set Python to run in unbuffered mode (better for Docker logs)
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose HTTP port
EXPOSE 8000

# Run server in HTTP mode (for production behind reverse proxy)
CMD ["python", "main.py", "--http"]
