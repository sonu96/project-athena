# Athena DeFi Agent - Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user for security
RUN groupadd -g 1000 athena && \
    useradd -r -u 1000 -g athena athena

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY cloud_functions/ ./cloud_functions/
COPY sql/ ./sql/

# Copy configuration files
COPY .env.example .env
COPY pytest.ini .

# Create necessary directories
RUN mkdir -p logs data

# Set ownership to app user
RUN chown -R athena:athena /app

# Switch to app user
USER athena

# Expose port for health checks (if needed)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - run the main agent
CMD ["python", "-m", "src.core.agent"]