# ── ElectraGuide v4.0 — Secure Cloud Run Dockerfile ──────────────────────────
FROM python:3.12-slim

# Security: Run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source (respects .dockerignore)
COPY . .

# Security: Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
# Security: Disable Python bytecode generation (reduces attack surface)
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8080

# Security: Switch to non-root user
USER appuser

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run with gunicorn (production WSGI server)
# --limit-request-line: prevents oversized request headers (security)
# --limit-request-fields: limits number of headers (DoS protection)
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 8 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --limit-request-line 8190 \
    --limit-request-fields 100 \
    app:app
