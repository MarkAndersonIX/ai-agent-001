# Multi-stage build for AI Agent Base
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r aiagent && useradd -r -g aiagent aiagent

# Copy Python packages from builder
COPY --from=builder /root/.local /home/aiagent/.local

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/vectors /app/data/documents /app/data/web_cache /app/logs \
    && chown -R aiagent:aiagent /app

# Set Python path
ENV PATH=/home/aiagent/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to non-root user
USER aiagent

# Create default config if it doesn't exist
RUN python -c "from providers.yaml_config_provider import create_default_config_file; create_default_config_file()"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "api.server"]
