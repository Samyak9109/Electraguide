# ── ElectraGuide — Cloud Run Dockerfile ─────────────────────────────────────
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080
ENV FLASK_ENV=production

# Expose port
EXPOSE 8080

# Run with gunicorn (production WSGI server)
# --workers: 2x CPU cores + 1 is standard; Cloud Run gives 1 vCPU by default
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 8 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    app:app
