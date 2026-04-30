<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-000000?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/Gemini_AI-2.0_Flash-4285F4?logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/Cloud_Run-Ready-4285F4?logo=google-cloud&logoColor=white" alt="Cloud Run">
  <img src="https://img.shields.io/badge/PWA-Installable-5A0FC8?logo=pwa&logoColor=white" alt="PWA">
  <img src="https://img.shields.io/badge/WCAG-2.1_AA-green?logo=accessibility" alt="Accessibility">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

# ⚡ ElectraGuide v4.0

**AI-Powered Democracy Navigator for Indian Elections**

ElectraGuide is a full-stack Progressive Web App (PWA) that helps India's 968M+ registered voters navigate the voting process. Powered by Google Gemini AI and deployed on Google Cloud Run, it features an AI chat assistant, interactive voting checklist, polling booth finder with Google Maps, civic glossary, and real-time election statistics dashboard.

> **Non-partisan by design** — ElectraGuide helps you understand *how* to vote, never *who* to vote for.

---

## 🎯 What Is ElectraGuide?

A civic-tech platform designed to make voting accessible and simple:

| Feature | Description |
|---------|-------------|
| **🤖 AI Chat Assistant** | Gemini-powered Q&A on elections + general knowledge with conversational memory |
| **✅ Voting Readiness Tracker** | 7-step interactive checklist with progress ring visualization |
| **📍 Polling Booth Finder** | Search by city/pincode with embedded Google Maps directions |
| **📖 Civic Glossary** | 16 searchable ECI-verified election terms |
| **📊 Election Dashboard** | Live statistics — voters, turnout, constituencies, polling stations |
| **💡 Did You Know** | Random election facts with one-tap refresh |
| **📲 PWA + Offline** | Installable app with service worker for offline access |
| **⭐ Feedback System** | In-app star rating + comments for continuous improvement |
| **♿ Accessibility** | WCAG 2.1 AA compliant — skip navigation, focus styles, reduced motion |
| **🔐 Security Hardened** | CSP headers, rate limiting, input sanitization, HSTS, XSS prevention |

---

## 🏗️ How It Works

### Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND (PWA)                      │
│  index.html + style.css + app.js + sw.js              │
│  manifest.json · Service Worker · Offline-first       │
├──────────────────────────────────────────────────────┤
│                  REST API (JSON)                       │
├──────────────────────────────────────────────────────┤
│                    BACKEND                             │
│  Flask (app.py) + Gunicorn (production WSGI)          │
│  ├── /api/chat       → Gemini AI + keyword fallback   │
│  ├── /api/checklist  → Session-based progress tracker │
│  ├── /api/booth      → City-based booth lookup        │
│  ├── /api/glossary   → Searchable ECI terms           │
│  ├── /api/tip        → Random election facts          │
│  ├── /api/stats      → Election statistics dashboard  │
│  ├── /api/feedback   → User feedback collection       │
│  ├── /api/session    → User session persistence       │
│  └── /health         → Container health check         │
├──────────────────────────────────────────────────────┤
│              GOOGLE CLOUD PLATFORM                     │
│  Gemini AI · Cloud Run · Cloud Build · Cloud Logging  │
│  Secret Manager · Container Registry                  │
└──────────────────────────────────────────────────────┘
```

### AI Chat Flow

1. User sends a question via the chat interface
2. Frontend POSTs to `/api/chat` with question + last 6 conversation turns
3. Backend tries Gemini models in order: `flash-lite` → `flash` → `2.5-flash`
4. Automatic retry on 429 rate limits with exponential backoff
5. Falls back to keyword-matching knowledge base if all models fail
6. Response streamed word-by-word in the UI for a natural feel

### Security Architecture

- **Content Security Policy (CSP)** — Restricts script/style sources
- **HTTP Security Headers** — HSTS, X-Frame-Options, X-Content-Type-Options
- **Rate Limiting** — Per-IP throttling on all API endpoints
- **Input Sanitization** — HTML escaping, length limits, type validation
- **Non-root Docker** — Container runs as unprivileged `appuser`
- **Secret Manager** — API keys stored in Google Cloud Secret Manager

---

## 📁 Project Structure

```
ElectraGuide/
├── app.py              # Flask backend — 10 API endpoints, Gemini AI integration
├── index.html          # Frontend SPA — splash, onboarding, 5 tabs, feedback modal
├── style.css           # Premium dark theme — glassmorphism, animations, responsive
├── app.js              # Frontend logic — state management, PWA, offline, accessibility
├── sw.js               # Service Worker — offline-first caching strategy
├── manifest.json       # PWA manifest — installable app configuration
├── requirements.txt    # Python dependencies
├── Dockerfile          # Secure Cloud Run container (non-root, healthcheck)
├── deploy.sh           # One-command Cloud Run deployment script
├── .dockerignore       # Files excluded from Docker build
├── .env.example        # Template for environment variables
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

---

## 🛠️ Tools & Technologies

### Backend Stack
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.12+ | Runtime |
| **Flask** | 3.x | Web framework & static file serving |
| **Flask-CORS** | 4.x | Cross-origin request handling |
| **Google GenAI** | 1.x | Gemini AI SDK (`google-genai`) |
| **Gunicorn** | 22.x | Production WSGI server |
| **python-dotenv** | 1.x | Local environment variable loading |
| **Google Cloud Logging** | 3.x | Structured cloud logging |
| **Google Cloud Secret Manager** | 2.x | Secure API key storage |

### Frontend Stack
| Technology | Purpose |
|-----------|---------|
| **HTML5** | Semantic markup, ARIA labels, structured data (JSON-LD) |
| **CSS3** | Custom properties, glassmorphism, gradients, keyframe animations |
| **Vanilla JavaScript** | State management, PWA, offline detection, accessibility |
| **Service Worker** | Offline-first caching, background sync |
| **Google Fonts (Outfit)** | Modern typography |
| **Google Maps Embed** | Polling booth directions |

### Cloud & AI
| Technology | Purpose |
|-----------|---------|
| **Google Gemini 2.0 Flash** | AI chat with 3-model fallback chain |
| **Google Cloud Run** | Serverless container hosting (Mumbai region) |
| **Google Cloud Build** | Automated Docker image building |
| **Google Container Registry** | Docker image storage |
| **Google Cloud Logging** | Production log aggregation |
| **Google Cloud Secret Manager** | Secure credential management |

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
source venv/bin/activate

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

## ☁️ Cloud Run Deployment

### One-Command Deploy
```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
bash deploy.sh
```

### Cloud Run Configuration
| Setting | Value | Reason |
|---------|-------|--------|
| Region | `asia-south1` (Mumbai) | Lowest latency for Indian users |
| Memory | `512Mi` | Flask + Gemini calls |
| CPU | `1` | Handles 80 concurrent requests |
| Min instances | `0` | Scale-to-zero for cost savings |
| Max instances | `3` | Rate limit protection |
| Timeout | `120s` | Gemini API response time |

---

## 🔌 API Reference

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `GET` | `/` | Frontend SPA | — |
| `GET` | `/health` | Health check (status, version, AI mode) | — |
| `GET` | `/api/checklist?session=ID` | Get voting checklist | 60/min |
| `POST` | `/api/checklist/toggle` | Mark item as done | 30/min |
| `POST` | `/api/chat` | AI assistant query | 20/min |
| `POST` | `/api/booth` | Find polling booth | 30/min |
| `GET` | `/api/glossary?q=term` | Search civic glossary | 60/min |
| `GET` | `/api/tip` | Random election fact | 60/min |
| `GET` | `/api/stats` | Election statistics | 60/min |
| `POST` | `/api/feedback` | Submit user feedback | 5/5min |
| `POST` | `/api/session` | Save user session | 10/min |

---

## ♿ Accessibility Features

- **Skip Navigation** — Keyboard-accessible skip link to main content
- **Focus Indicators** — Visible focus styles on all interactive elements
- **ARIA Labels** — Screen reader support on buttons and modals
- **Reduced Motion** — Respects `prefers-reduced-motion` media query
- **Keyboard Shortcuts** — Navigate tabs with `1-5`, `?` for feedback
- **Semantic HTML** — Proper heading hierarchy, landmark roles
- **Scalable Text** — No `user-scalable=no` restriction

---

## 📊 Innovation Highlights

- **Progressive Web App** — Installable on mobile/desktop with offline support
- **AI Model Fallback Chain** — 3-tier Gemini model cascade with retry logic
- **Offline-First Architecture** — Service worker caches static assets
- **Social Sharing** — Web Share API integration for voting readiness
- **Structured Data** — JSON-LD schema for search engine discoverability
- **Dynamic Countdown** — Real-time registration deadline with urgency colors
- **Privacy-First** — All user data stored locally, never sent to third parties

---

## ✅ Testing

```bash
python3 -c "
from app import app
client = app.test_client()
tests = [
    ('Health',    lambda: client.get('/health')),
    ('Checklist', lambda: client.get('/api/checklist?session=test')),
    ('Toggle',    lambda: client.post('/api/checklist/toggle', json={'session':'test','id':2})),
    ('Chat AI',   lambda: client.post('/api/chat', json={'question':'What is NOTA?','history':[]})),
    ('Booth',     lambda: client.post('/api/booth', json={'query':'mumbai'})),
    ('Glossary',  lambda: client.get('/api/glossary')),
    ('Tip',       lambda: client.get('/api/tip')),
    ('Stats',     lambda: client.get('/api/stats')),
    ('Feedback',  lambda: client.post('/api/feedback', json={'rating':5,'comment':'Great!'})),
    ('Session',   lambda: client.post('/api/session', json={'session':'t','user':{'name':'Sam'}})),
    ('Index',     lambda: client.get('/')),
    ('CSS',       lambda: client.get('/style.css')),
    ('JS',        lambda: client.get('/app.js')),
    ('SW',        lambda: client.get('/sw.js')),
    ('Manifest',  lambda: client.get('/manifest.json')),
]
for name, fn in tests:
    r = fn()
    status = '✅' if r.status_code == 200 else '❌'
    print(f'{status} {name}: {r.status_code}')
"
```

Expected output: all 15 endpoints return `✅ 200`.

---

## 🔐 Security Measures

| Layer | Implementation |
|-------|---------------|
| **Transport** | HSTS with 1-year max-age, includeSubDomains |
| **Content** | CSP restricts scripts, styles, frames, and objects |
| **Input** | HTML escaping, length truncation, type validation |
| **Rate Limiting** | Per-IP throttling on all endpoints |
| **Container** | Non-root user, read-only filesystem where possible |
| **Secrets** | Google Cloud Secret Manager integration |
| **Headers** | X-Frame-Options DENY, X-Content-Type-Options nosniff |
| **CORS** | Restrictive origin policy in production |

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
