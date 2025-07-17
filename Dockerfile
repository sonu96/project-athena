# Athena DeFi Agent - Production Container

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.phase1.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
# COPY CLAUDE.md .  # Skip if not present
# COPY README.md .  # Skip if not present

# Create necessary directories
RUN mkdir -p wallet_data logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Expose API port
EXPOSE 8080

# Set PORT for Cloud Run
ENV PORT=8080

# Run the simple server for Phase 1
CMD ["python", "/app/src/simple_server.py"]