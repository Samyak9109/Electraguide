# ⚡ ElectraGuide v2.0

> AI-powered election assistant — deployable on Google Cloud Run

---

## Project Structure

```
electraguide-webapp/
├── app.py                  ← Flask backend (REST API)
├── requirements.txt        ← Python deps
├── Dockerfile              ← Cloud Run container
├── .dockerignore
├── deploy.sh               ← One-command deploy script
├── templates/
│   └── index.html          ← Full SPA frontend
└── public/
    ├── css/style.css       ← All styles (responsive)
    └── js/app.js           ← Frontend logic + API calls
```

---

## Run Locally

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Run Flask dev server
FLASK_ENV=development python app.py

# 3. Open http://localhost:8080
```

---

## Deploy to Google Cloud Run

### Prerequisites
- Google Cloud account with billing enabled
- `gcloud` CLI installed: https://cloud.google.com/sdk/docs/install
- Authenticated: `gcloud auth login`

### One-command deploy

```bash
# Set your GCP project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Make deploy script executable
chmod +x deploy.sh

# Deploy (builds image, pushes to GCR, deploys to Cloud Run)
bash deploy.sh
```

### Manual deploy steps

```bash
# 1. Set project
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# 3. Build & push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/electraguide .

# 4. Deploy
gcloud run deploy electraguide \
  --image gcr.io/YOUR_PROJECT_ID/electraguide \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 512Mi

# 5. Get URL
gcloud run services describe electraguide \
  --platform managed --region asia-south1 \
  --format "value(status.url)"
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve frontend SPA |
| GET | `/health` | Health check (Cloud Run probe) |
| GET | `/api/checklist` | Get user checklist |
| POST | `/api/checklist/toggle` | Mark item done |
| POST | `/api/chat` | AI chat response |
| POST | `/api/booth` | Find polling booth |
| GET | `/api/glossary` | Civic glossary (filterable) |
| GET | `/api/tip` | Random civic tip |
| POST | `/api/session` | Save user session |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port (Cloud Run sets this) |
| `FLASK_ENV` | `production` | `development` for local debug |

---

## Scaling & Cost

- **Min instances: 0** — scales to zero when idle (no traffic = no cost)
- **Max instances: 3** — handles traffic spikes
- **Free tier:** Cloud Run gives 2M requests/month free
- **Estimated cost:** ~$0 for low-traffic civic app

---

## Production Upgrades (Next Steps)

1. **Persistent storage** — Replace in-memory `sessions` dict with Firestore or Redis
2. **Real AI** — Wire `/api/chat` to Gemini/OpenAI with RAG over ECI documents
3. **Real booth data** — Integrate ECI's official voter service API
4. **Auth** — Add Google Sign-In for personalized voter profiles
5. **Analytics** — Add Google Analytics or Plausible for completion rate tracking
6. **PWA** — Add `manifest.json` + service worker for installable mobile app
7. **i18n** — Add Hindi translation using Flask-Babel

---

## Tech Stack

- **Backend:** Python 3.12 + Flask 3.0 + Gunicorn
- **Frontend:** Vanilla JS (no framework) + CSS custom properties
- **Container:** Docker (python:3.12-slim)
- **Platform:** Google Cloud Run (serverless)
- **Fonts:** Fraunces + DM Sans + DM Mono (Google Fonts)

---

## Non-Partisan Commitment

ElectraGuide helps citizens understand **how** to vote — never **who** to vote for.
All data is sourced from the Election Commission of India (ECI) and NVSP.
