# Stage 1: Builder
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app/backend

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    alsa-utils \
    mpv \
    libpulse0 \
    pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /install /usr/local

# Create a non-root user and group
RUN groupadd -r npcron && useradd -r -g npcron -G audio,video npcron

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/media && \
    chown -R npcron:npcron /app

# Copy application files
COPY backend /app/backend
COPY frontend /app/frontend

# Switch to non-root user
USER npcron

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Default command: run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
