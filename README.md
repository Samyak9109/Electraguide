<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-000000?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/Gemini_AI-2.0_Flash-4285F4?logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/Cloud_Run-Ready-4285F4?logo=google-cloud&logoColor=white" alt="Cloud Run">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

# ⚡ ElectraGuide v3.0

**AI-Powered Democracy Navigator for Indian Elections**

ElectraGuide is a full-stack web application that helps Indian citizens navigate the voting process with an AI-powered assistant, interactive voting checklist, polling booth finder, and civic glossary. Built with Flask and powered by Google Gemini AI, it's designed to be deployed on Google Cloud Run.

> **Non-partisan by design** — ElectraGuide helps you understand *how* to vote, never *who* to vote for.

---

## 🎯 What Is ElectraGuide?

ElectraGuide is a civic-tech platform designed to make voting accessible and simple for India's 900M+ registered voters. It provides:

- **🤖 AI Chat Assistant** — Powered by Google Gemini, answers any question about elections, voter registration, ID requirements, and more. Also works as a general-purpose AI assistant.
- **✅ Voting Readiness Checklist** — 7-step interactive tracker from registration to Election Day with progress visualization.
- **📍 Polling Booth Finder** — Search by city/pincode with Google Maps integration for directions.
- **📖 Civic Glossary** — 16 searchable election terms (NOTA, EVM, VVPAT, etc.) with verified ECI sources.
- **💡 Did You Know** — Random election facts to boost civic awareness.
- **📱 Mobile-First Design** — Premium dark theme with glassmorphism, optimized for mobile browsers.

---

## 🏗️ How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND                        │
│  index.html + style.css + app.js                │
│  (Vanilla HTML/CSS/JS — no framework)           │
├─────────────────────────────────────────────────┤
│                REST API (JSON)                   │
├─────────────────────────────────────────────────┤
│                  BACKEND                         │
│  Flask (app.py) + Gunicorn (production)         │
│  ├── /api/chat     → Gemini AI + keyword fallback│
│  ├── /api/checklist → Session-based tracker      │
│  ├── /api/booth    → City-based booth lookup     │
│  ├── /api/glossary → Searchable ECI terms        │
│  ├── /api/tip      → Random election facts       │
│  └── /health       → Container health check      │
├─────────────────────────────────────────────────┤
│              GOOGLE GEMINI AI                    │
│  Model fallback chain:                          │
│  gemini-2.0-flash-lite → 2.0-flash → 2.5-flash │
└─────────────────────────────────────────────────┘
```

### AI Chat Flow

1. User sends a question via the chat interface
2. Frontend POSTs to `/api/chat` with the question + last 6 conversation turns
3. Backend tries Gemini models in order with retry logic (handles 429 rate limits)
4. If all models fail, falls back to keyword-matching knowledge base
5. Response streamed word-by-word in the UI for a natural feel

### Data Flow

- **User data** stored in `localStorage` (never leaves the device)
- **Session state** managed in-memory on the server (use Redis for production)
- **Booth data** sourced from Election Commission of India (ECI) records
- **Glossary** verified against official ECI definitions

---

## 📁 Project Structure

```
ElectraGuide/
├── app.py              # Flask backend — API routes, Gemini integration
├── index.html          # Frontend — single-page app with 5 tabs
├── style.css           # Premium dark theme — glassmorphism, animations
├── app.js              # Frontend logic — API calls, state management
├── requirements.txt    # Python dependencies
├── Dockerfile          # Cloud Run container config
├── .dockerignore       # Files excluded from Docker build
├── deploy.sh           # One-command Cloud Run deployment script
├── .env                # Local environment variables (git-ignored)
├── .env.example        # Template for environment variables
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Key Files Explained

| File | Purpose | Size |
|------|---------|------|
| `app.py` | Flask server with 8 API endpoints, Gemini AI with model fallback + retry | ~340 lines |
| `index.html` | Semantic HTML5 with splash, onboarding, and 5 main tabs | ~380 lines |
| `style.css` | CSS custom properties, glassmorphism, responsive dark theme | ~325 lines |
| `app.js` | State management, API communication, animations | ~670 lines |
| `Dockerfile` | Python 3.12 slim image with gunicorn WSGI server | ~30 lines |
| `deploy.sh` | Automated gcloud CLI deployment with env injection | ~90 lines |

---

## 🛠️ Tools & Technologies

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.12+ | Runtime |
| **Flask** | 3.x | Web framework & static file serving |
| **Flask-CORS** | 4.x | Cross-origin request handling |
| **Google GenAI** | 1.x | Gemini AI SDK (modern `google-genai` package) |
| **Gunicorn** | 22.x | Production WSGI server |
| **python-dotenv** | 1.x | Local environment variable loading |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **HTML5** | Semantic markup, mobile-first meta tags |
| **CSS3** | Custom properties, glassmorphism, gradients, animations |
| **Vanilla JavaScript** | State management, API calls, DOM manipulation |
| **Google Fonts (Outfit)** | Modern typography |
| **Google Maps Embed** | Polling booth directions |

### AI & Cloud
| Technology | Purpose |
|-----------|---------|
| **Google Gemini 2.0 Flash** | AI chat (with automatic model fallback chain) |
| **Google Cloud Run** | Serverless container hosting |
| **Google Cloud Build** | Docker image building |
| **Google Container Registry** | Image storage |

### Development
| Tool | Purpose |
|------|---------|
| **Docker** | Containerization |
| **Git** | Version control |
| **gcloud CLI** | Cloud deployment |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- A free [Gemini API key](https://aistudio.google.com/app/apikey)

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Samyak9109/Electraguide.git
cd ElectraGuide

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Run the development server
python app.py
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

---

## ☁️ Deploying to Google Cloud Run

### Prerequisites

- [Google Cloud account](https://cloud.google.com/) with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- A Gemini API key

### One-Command Deploy

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

# Deploy
bash deploy.sh
```

### Manual Deploy Steps

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# 3. Build & push Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/electraguide .

# 4. Deploy to Cloud Run
gcloud run deploy electraguide \
  --image gcr.io/YOUR_PROJECT_ID/electraguide \
  --platform managed \
  --region asia-south1 \
  --memory 512Mi \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=your_key_here" \
  --port 8080

# 5. Get the live URL
gcloud run services describe electraguide \
  --region asia-south1 \
  --format "value(status.url)"
```

### Cloud Run Configuration

| Setting | Value | Reason |
|---------|-------|--------|
| Region | `asia-south1` (Mumbai) | Lowest latency for Indian users |
| Memory | `512Mi` | Sufficient for Flask + Gemini calls |
| CPU | `1` | Single vCPU handles 80 concurrent requests |
| Min instances | `0` | Scale-to-zero for cost savings |
| Max instances | `3` | Rate limit protection |
| Timeout | `120s` | Allows time for Gemini API responses |

---

## 🔌 API Reference

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | Serves the frontend SPA | None |
| `GET` | `/health` | Health check (status, version, AI mode) | None |
| `GET` | `/api/checklist?session=ID` | Get voting checklist for session | None |
| `POST` | `/api/checklist/toggle` | Mark a checklist item as done | None |
| `POST` | `/api/chat` | Send a question to the AI assistant | None |
| `POST` | `/api/booth` | Find polling booth by city/pincode | None |
| `GET` | `/api/glossary?q=term` | Search civic glossary | None |
| `GET` | `/api/tip` | Get a random election fact | None |
| `POST` | `/api/session` | Save user session data | None |

### Example: Chat API

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What ID do I need to vote?", "history": []}'
```

Response:
```json
{
  "answer": "You need your Voter ID card (EPIC), or any ONE of: Aadhaar, PAN, Passport...",
  "source": "gemini"
}
```

---

## ✅ Testing

Run the built-in test suite:

```bash
python3 -c "
from app import app
import json
client = app.test_client()

# Test all endpoints
tests = [
    ('Health',    lambda: client.get('/health')),
    ('Checklist', lambda: client.get('/api/checklist?session=test')),
    ('Toggle',    lambda: client.post('/api/checklist/toggle', json={'session':'test','id':2})),
    ('Chat AI',   lambda: client.post('/api/chat', json={'question':'What is NOTA?','history':[]})),
    ('Booth',     lambda: client.post('/api/booth', json={'query':'mumbai'})),
    ('Glossary',  lambda: client.get('/api/glossary')),
    ('Tip',       lambda: client.get('/api/tip')),
    ('Session',   lambda: client.post('/api/session', json={'session':'t','user':{'name':'Sam'}})),
    ('Index',     lambda: client.get('/')),
    ('CSS',       lambda: client.get('/style.css')),
    ('JS',        lambda: client.get('/app.js')),
]

for name, fn in tests:
    r = fn()
    status = '✅' if r.status_code == 200 else '❌'
    print(f'{status} {name}: {r.status_code}')
"
```

Expected output: all 11 endpoints return `✅ 200`.

---

## 🔐 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key ([get one free](https://aistudio.google.com/app/apikey)) |
| `PORT` | No | `8080` | Server port |
| `FLASK_ENV` | No | `production` | Set to `development` for debug mode |

---

## 📊 Features Breakdown

### AI Assistant (Gemini-Powered)
- Answers election questions with ECI-verified sources
- Also answers **any general question** as a helpful AI
- Conversational memory (last 6 turns)
- Model fallback chain: `gemini-2.0-flash-lite` → `gemini-2.0-flash` → `gemini-2.5-flash`
- Automatic retry on rate limits (429)
- Keyword fallback when API is unavailable

### Voting Readiness Tracker
- 7 essential pre-election tasks
- Visual progress ring (0–100%)
- Milestone roadmap: Register → Documents → Find Booth → Vote Day
- Downloadable voting plan (`.txt`)
- Data persisted in localStorage

### Booth Finder
- Covers 7 major Indian cities (Delhi, Mumbai, Bangalore, Chennai, Hyderabad, Kolkata, Pune)
- Google Maps embed for directions
- One-tap "Open in Google Maps" navigation

### Civic Glossary
- 16 election terms with definitions
- Real-time search filtering
- Sources verified against ECI

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- [Election Commission of India](https://eci.gov.in/) — Official data source
- [Google Gemini AI](https://ai.google.dev/) — AI chat engine
- [Google Cloud Run](https://cloud.google.com/run) — Serverless hosting
- [NVSP](https://nvsp.in/) — National Voters' Service Portal

---

<p align="center">
  Made with ❤️ for Indian Democracy<br>
  <strong>Every vote counts. Be ready.</strong>
</p>
