# ── ElectraGuide v3.0 — Cloud Run Dockerfile ────────────────────────────────
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source (respects .dockerignore)
COPY . .

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run with gunicorn (production WSGI server)
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 8 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    app:app
