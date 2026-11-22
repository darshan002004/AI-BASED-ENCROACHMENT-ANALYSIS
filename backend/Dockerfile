# ==============================================================================
# EncroWatch AI — Production FastAPI Backend Container
# Multi-stage security-hardened container running as non-root user
# ==============================================================================

FROM python:3.12-slim AS runtime

# System runtime dependencies for OpenCV (headless), networking, and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Optimize Python execution in containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Create dedicated non-root application user
RUN groupadd -g 1001 encrowatch && \
    useradd -u 1001 -g encrowatch -m -s /bin/bash encrowatch

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and default weights
COPY . .

# Ensure storage directories exist with appropriate non-root ownership
RUN mkdir -p /app/uploads/original \
             /app/uploads/annotated \
             /app/uploads/privacy \
             /app/uploads/inspections \
             /app/uploads/reports \
             /app/data \
             /app/app/ai/weights/versions \
             /app/app/ai/weights/backups && \
    chown -R encrowatch:encrowatch /app

# Switch to non-root user
USER encrowatch

EXPOSE 8000

# Automated container healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
