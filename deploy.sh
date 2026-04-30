#!/bin/bash
# ─────────────────────────────────────────────────────────────
# ElectraGuide — Google Cloud Run Deploy Script
# Usage: bash deploy.sh
# Requirements: gcloud CLI installed & authenticated
# ─────────────────────────────────────────────────────────────

set -e  # Exit on any error

# ── CONFIGURATION ─────────────────────────────────────────────
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-electraguide-494807}"
SERVICE_NAME="electraguide"
REGION="asia-south1"          # Mumbai — closest to India
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}"
MEMORY="512Mi"
CPU="1"
CONCURRENCY="80"
MIN_INSTANCES="0"             # Scale to 0 when idle (free tier)
MAX_INSTANCES="3"

# Load API Key from .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   ElectraGuide — Cloud Run Deploy    ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Project:   $PROJECT_ID"
echo "  Service:   $SERVICE_NAME"
echo "  Region:    $REGION"
echo "  Image:     $IMAGE"
echo ""

# ── STEP 1: Set project ────────────────────────────────────────
echo "► Setting GCP project..."
gcloud config set project "$PROJECT_ID"

# ── STEP 2: Enable required APIs ──────────────────────────────
echo "► Enabling Cloud Run & Artifact Registry APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --quiet

# ── STEP 2b: Ensure Artifact Registry repo exists ─────────────
gcloud artifacts repositories describe cloud-run-source-deploy \
  --location="$REGION" 2>/dev/null || \
gcloud artifacts repositories create cloud-run-source-deploy \
  --repository-format=docker \
  --location="$REGION" \
  --description="ElectraGuide Docker images" \
  --quiet

# ── STEP 3: Build & push Docker image ─────────────────────────
echo "► Building Docker image..."
gcloud builds submit \
  --tag "$IMAGE" \
  --timeout=600s \
  .

echo "► Image built: $IMAGE"

# ── STEP 4: Deploy to Cloud Run ────────────────────────────────
echo "► Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --memory "$MEMORY" \
  --cpu "$CPU" \
  --concurrency "$CONCURRENCY" \
  --min-instances "$MIN_INSTANCES" \
  --max-instances "$MAX_INSTANCES" \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --port 8080 \
  --quiet

# ── STEP 5: Get service URL ────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --format "value(status.url)")

echo ""
echo "╔══════════════════════════════════════╗"
echo "║          DEPLOY SUCCESSFUL! 🎉       ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Live URL: $SERVICE_URL"
echo ""
echo "  Health check: $SERVICE_URL/health"
echo ""
echo "  To view logs:"
echo "  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\" --limit=50"
echo ""
