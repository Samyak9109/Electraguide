"""
ElectraGuide v4.0 — Flask backend
Powered by Google Gemini AI · Deployed on Google Cloud Run
Enhanced with security hardening, accessibility, PWA & Google Cloud integration
"""

import os
import json
import re
import html
import uuid
import random
import time
import logging
from functools import wraps
from collections import defaultdict
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, abort

# Load .env file if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on real env vars

# ── Google Cloud Logging integration ───────────────────────────────────────────
# Uses Cloud Logging when running on GCP; standard logging locally
try:
    import google.cloud.logging as cloud_logging
    cloud_client = cloud_logging.Client()
    cloud_client.setup_logging()
    logging.info("☁️  Google Cloud Logging attached")
except (ImportError, Exception):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

logger = logging.getLogger("electraguide")

# ── Google Cloud Secret Manager (optional) ─────────────────────────────────────
def get_secret(secret_id: str) -> str | None:
    """Fetch a secret from Google Cloud Secret Manager.
    Falls back to environment variable if Secret Manager is unavailable."""
    try:
        from google.cloud import secretmanager
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        if not project:
            return None
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception:
        return None

# ── Gemini setup ───────────────────────────────────────────────────────────────
# Priority: Secret Manager > Environment Variable
GEMINI_API_KEY = get_secret("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
gemini_client = None

# Model preference order — try lighter/more-available models first
MODEL_CANDIDATES = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
]

SYSTEM_PROMPT = (
    "You are ElectraGuide, a friendly and intelligent AI assistant. "
    "You are primarily focused on Indian elections and the voting process, "
    "but you are also a general-purpose assistant who can answer ANY question the user asks. "
    "For election-related queries: provide clear, accurate, step-by-step guidance on voter registration, "
    "finding polling booths, required ID documents, mail-in/postal ballots, "
    "EVM usage, NOTA, election schedules, and related civic topics. "
    "Always cite official sources like the Election Commission of India (ECI), "
    "nvsp.in, or voterportal.eci.gov.in when relevant. "
    "If a question is about party politics, candidates, or who to vote for, "
    "politely decline and redirect to civic process information. "
    "For NON-election questions: answer them helpfully and accurately as a general AI assistant. "
    "Keep answers concise (3-5 sentences max unless the user asks for detail), "
    "warm, and empowering. "
    "Respond in the same language the user writes in (English or Hindi)."
)

if GEMINI_API_KEY:
    try:
        from google import genai as google_genai
        from google.genai import types as genai_types
        gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini AI client initialized (google.genai)")
    except ImportError:
        logger.warning("⚠️  google-genai package not installed — run: pip install google-genai")
    except Exception as e:
        logger.error(f"⚠️  Gemini setup failed: {e}")
else:
    logger.info("ℹ️  No GEMINI_API_KEY found — running in keyword-fallback mode")

# ── Flask app ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

# ── Security: Restrictive CORS ─────────────────────────────────────────────────
# Only allow same-origin in production; permissive in development
FLASK_ENV = os.environ.get("FLASK_ENV", "production")
if FLASK_ENV == "development":
    from flask_cors import CORS
    CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080"])
else:
    from flask_cors import CORS
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")
    CORS(app, origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != [""] else ["*"],
         methods=["GET", "POST"],
         allow_headers=["Content-Type"])

# ── Security: HTTP Headers ─────────────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    """Add security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "frame-src https://maps.google.com https://www.google.com; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    return response

# ── Security: Rate Limiter ─────────────────────────────────────────────────────
class RateLimiter:
    """Simple in-memory rate limiter per IP address."""
    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(self, ip: str, max_requests: int = 30, window_seconds: int = 60) -> bool:
        now = time.time()
        # Clean old entries
        self.requests[ip] = [t for t in self.requests[ip] if now - t < window_seconds]
        if len(self.requests[ip]) >= max_requests:
            return False
        self.requests[ip].append(now)
        return True

rate_limiter = RateLimiter()

def rate_limit(max_requests=30, window=60):
    """Decorator to rate-limit an endpoint."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            if ip:
                ip = ip.split(",")[0].strip()
            if not rate_limiter.is_allowed(ip, max_requests, window):
                logger.warning(f"Rate limit exceeded for IP: {ip}")
                return jsonify({"error": "Too many requests. Please wait a moment."}), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ── Security: Input Sanitizer ──────────────────────────────────────────────────
def sanitize_input(text: str, max_length: int = 500) -> str:
    """Sanitize and limit user input to prevent injection and abuse."""
    if not isinstance(text, str):
        return ""
    # Truncate to max length
    text = text[:max_length]
    # Strip leading/trailing whitespace
    text = text.strip()
    # Escape HTML entities to prevent XSS
    text = html.escape(text)
    return text

def validate_session_id(session_id: str) -> str:
    """Validate session ID format to prevent injection."""
    if not session_id or not isinstance(session_id, str):
        return "default"
    # Only allow alphanumeric, underscores, and hyphens
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '', session_id[:64])
    return cleaned or "default"

# In-memory session store (use Redis/Firestore for production)
sessions = {}

# ── STATIC DATA ───────────────────────────────────────────────────────────────
GLOSSARY = [
    {"term": "NOTA", "def": "None Of The Above — lets you reject all candidates without choosing any.", "source": "ECI"},
    {"term": "EVM", "def": "Electronic Voting Machine — tamper-proof device used at polling booths to record votes.", "source": "ECI"},
    {"term": "VVPAT", "def": "Voter Verified Paper Audit Trail — prints a paper slip showing your vote for verification.", "source": "ECI"},
    {"term": "EPIC", "def": "Electors Photo Identity Card — the official Voter ID card issued by the Election Commission.", "source": "ECI"},
    {"term": "Constituency", "def": "Geographic area whose residents vote together to elect one representative.", "source": "ECI"},
    {"term": "Lok Sabha", "def": "Lower house of India's Parliament. Members directly elected every 5 years.", "source": "Parliament"},
    {"term": "Vidhan Sabha", "def": "State Legislative Assembly — voters elect MLAs for each constituency.", "source": "Parliament"},
    {"term": "Model Code of Conduct", "def": "ECI guidelines governing parties and candidates from announcement to results.", "source": "ECI"},
    {"term": "Booth Level Officer", "def": "Official responsible for voter registration updates at the local polling booth.", "source": "ECI"},
    {"term": "Affidavit", "def": "Sworn declaration candidates must file disclosing criminal records, assets, and education.", "source": "ECI"},
    {"term": "Turnout", "def": "Percentage of eligible voters who actually cast a vote. Higher means stronger democracy.", "source": "ECI"},
    {"term": "Primary Election", "def": "Preliminary vote within a party to choose their candidate for the general election.", "source": "ECI"},
    {"term": "Postal Ballot", "def": "A voting method allowing eligible voters (service voters, elderly, disabled) to vote by post.", "source": "ECI"},
    {"term": "Returning Officer", "def": "District official responsible for conducting elections and declaring results in a constituency.", "source": "ECI"},
    {"term": "Form 6", "def": "Application form for new voter registration on the electoral roll. Submit at nvsp.in.", "source": "ECI"},
    {"term": "e-EPIC", "def": "Digital version of your Voter ID card downloadable as PDF from voterportal.eci.gov.in.", "source": "ECI"},
]

CHAT_KB = {
    "id":       "You need your Voter ID card (EPIC), or any ONE of: Aadhaar, PAN, Passport, Driving Licence, or MNREGA Job Card. Originals only — no photocopies.\n\n✅ Source: Election Commission of India",
    "nota":     "NOTA = None Of The Above. Lets you register dissent without supporting any candidate. Your vote counts but goes to no party. Introduced in 2013 by the Supreme Court.\n\n✅ Source: ECI",
    "booth":    "Visit voters.eci.gov.in → Search by EPIC number or mobile. Or SMS EPIC <voter-id> to 1950. Your booth is usually the nearest government school or community hall in your ward.\n\n📍 Source: ECI Portal",
    "register": "Registration closes 30 days before Election Day. Apply on nvsp.in or the Voter Helpline App. Call 1950 for state-specific dates.\n\n✅ Source: NVSP",
    "postal":   "Apply for postal ballot if you're a service voter, senior citizen (80+), or person with disability. Form 12D must be submitted to your Returning Officer.\n\n✅ Source: ECI",
    "aadhaar":  "Linking Aadhaar to your Voter ID is voluntary but recommended for de-duplication. Link via nvsp.in or the Voter Helpline App.\n\n✅ Source: ECI",
    "evm":      "EVMs are standalone devices that record votes electronically. They are standalone machines with no internet connection, making them tamper-proof. Used in India since 1998.\n\n✅ Source: ECI",
}

BOOTHS = {
    "delhi":     {"name": "Govt. Boys Sr. Secondary School, Sector 14", "address": "Dwarka Sector 14, New Delhi — 110078", "ward": "Ward 142, Dwarka Sector-14", "distance": "0.8 km"},
    "mumbai":    {"name": "Municipal School, Andheri West", "address": "Jai Hind Colony, Andheri West, Mumbai — 400058", "ward": "K/West Ward — Andheri", "distance": "1.2 km"},
    "bangalore": {"name": "Government Primary School, Koramangala", "address": "5th Block, Koramangala, Bengaluru — 560095", "ward": "Ward 151 — Koramangala", "distance": "0.6 km"},
    "chennai":   {"name": "Corporation Higher Secondary School", "address": "T. Nagar, Chennai — 600017", "ward": "Ward 131 — T. Nagar", "distance": "1.0 km"},
    "hyderabad": {"name": "Zilla Parishad High School", "address": "Banjara Hills, Hyderabad — 500034", "ward": "Ward 56 — Banjara Hills", "distance": "0.9 km"},
    "kolkata":   {"name": "Ballygunge Government High School", "address": "Ballygunge, Kolkata — 700019", "ward": "Ward 85 — Ballygunge", "distance": "0.7 km"},
    "pune":      {"name": "Pune Municipal Corporation School", "address": "Kothrud, Pune — 411029", "ward": "Ward 14 — Kothrud", "distance": "1.1 km"},
}

DEFAULT_CHECKLIST = [
    {"id": 0, "title": "Register on Voter ID portal",    "meta": "nvsp.in · Required",                          "tag": "done",    "done": True},
    {"id": 1, "title": "Verify Aadhaar linkage",         "meta": "voters.eci.gov.in · Required",                "tag": "done",    "done": True},
    {"id": 2, "title": "Find your polling booth",        "meta": "Due 7 days before election · Urgent",         "tag": "urgent",  "done": False},
    {"id": 3, "title": "Download Voter ID slip (e-EPIC)","meta": "voterportal.eci.gov.in",                      "tag": "pending", "done": False},
    {"id": 4, "title": "Set Election Day reminder",      "meta": "Optional but recommended",                    "tag": "pending", "done": False},
    {"id": 5, "title": "Check your name on voter list",  "meta": "electoralsearch.eci.gov.in · 30 days before", "tag": "pending", "done": False},
    {"id": 6, "title": "Arrange valid photo ID for booth","meta": "Aadhaar / EPIC / PAN / Passport",            "tag": "pending", "done": False},
]

TIPS = [
    "India has over 900 million registered voters — the world's largest democratic electorate.",
    "EVMs have been used in Indian elections since 1998 and have no internet connection.",
    "NOTA was introduced in 2013 following a landmark Supreme Court ruling.",
    "Voting typically takes less than 5 minutes at the booth.",
    "Women account for nearly 49% of India's registered voters as of 2024.",
    "Mobile phones are NOT allowed inside polling booths during voting.",
    "The Election Commission of India was established on 25 January 1950.",
    "You can track your voter application status on nvsp.in anytime.",
    "e-EPIC lets you carry a digital voter ID on your phone — download it at voterportal.eci.gov.in.",
    "If your name is missing from the voter list, you can apply to add it using Form 6 on nvsp.in.",
    "The National Voter Helpline number is 1950 — free to call from any phone.",
    "Persons with disabilities can request a wheelchair or assistance at any polling booth.",
]

# ── Keyword fallback helper ────────────────────────────────────────────────────
def keyword_answer(question: str) -> str | None:
    q = question.lower()
    for key, response in CHAT_KB.items():
        if key in q:
            return response
    if any(w in q for w in ["vote", "voting", "election", "ballot", "booth", "registration"]):
        return (
            "For your specific query, I recommend:\n\n"
            "• voters.eci.gov.in — official ECI portal\n"
            "• Voter Helpline: 1950 (toll-free)\n"
            "• nvsp.in — National Voters' Service Portal\n\n"
            "I can answer questions about IDs, booths, NOTA, registration, postal ballots, and Aadhaar linking."
        )
    return None


# ── Gemini call with model fallback + retry ────────────────────────────────────
def call_gemini(question: str, history: list) -> str | None:
    """Try calling Gemini with model fallback and retry logic."""
    if not gemini_client:
        return None

    from google.genai import types as _t

    # Build conversation contents from history
    contents = []
    for turn in history[-6:]:
        role = turn.get("role")
        text = turn.get("text", "")
        if role in ("user", "model") and text:
            contents.append(
                _t.Content(role=role, parts=[_t.Part(text=text)])
            )
    contents.append(_t.Content(role="user", parts=[_t.Part(text=question)]))

    config = _t.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)

    # Try each model candidate
    for model_name in MODEL_CANDIDATES:
        for attempt in range(2):  # max 2 attempts per model
            try:
                resp = gemini_client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                answer = resp.text.strip()
                if answer:
                    logger.info(f"Gemini response OK via {model_name}")
                    return answer
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt == 0:
                        time.sleep(2)  # brief pause before retry
                        continue
                    else:
                        break  # try next model
                elif "404" in err_str or "not found" in err_str.lower():
                    break  # model doesn't exist, try next
                else:
                    logger.error(f"Gemini error ({model_name}): {e}")
                    break

    return None


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")

@app.route("/health")
def health():
    """Health check endpoint for Cloud Run liveness probes."""
    return jsonify({
        "status": "ok",
        "service": "electraguide",
        "version": "4.0",
        "ai": "gemini" if gemini_client else "keyword-fallback",
    })

# ── API: Checklist ─────────────────────────────────────────────────────────────

@app.route("/api/checklist", methods=["GET"])
@rate_limit(max_requests=60, window=60)
def get_checklist():
    session_id = validate_session_id(request.args.get("session", "default"))
    checklist = sessions.get(session_id, {}).get("checklist", DEFAULT_CHECKLIST)
    return jsonify({"checklist": checklist})

@app.route("/api/checklist/toggle", methods=["POST"])
@rate_limit(max_requests=30, window=60)
def toggle_checklist():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    session_id = validate_session_id(data.get("session", "default"))
    item_id = data.get("id")

    # Validate item_id is an integer
    if not isinstance(item_id, int) or item_id < 0 or item_id > 100:
        return jsonify({"error": "Invalid item ID"}), 400

    if session_id not in sessions:
        sessions[session_id] = {"checklist": [dict(i) for i in DEFAULT_CHECKLIST]}

    for item in sessions[session_id]["checklist"]:
        if item["id"] == item_id and not item["done"]:
            item["done"] = True
            item["tag"] = "done"
            break

    checklist = sessions[session_id]["checklist"]
    done = sum(1 for i in checklist if i["done"])
    score = round((done / len(checklist)) * 100)
    return jsonify({"ok": True, "score": score, "done": done, "total": len(checklist)})

# ── API: Chat (Gemini-powered) ─────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
@rate_limit(max_requests=20, window=60)
def chat():
    data = request.get_json() or {}
    question = sanitize_input(data.get("question", ""), max_length=1000)
    history  = data.get("history", [])   # [{role, text}, …] last few turns

    if not question:
        return jsonify({"answer": "Please ask a question — I can help with voting, elections, or anything else!"})

    # Validate history format
    if not isinstance(history, list):
        history = []
    # Sanitize history entries
    clean_history = []
    for turn in history[-6:]:
        if isinstance(turn, dict) and "role" in turn and "text" in turn:
            role = turn["role"] if turn["role"] in ("user", "model") else None
            text = sanitize_input(str(turn.get("text", "")), max_length=1000)
            if role and text:
                clean_history.append({"role": role, "text": text})

    # ── Try Gemini first (with model fallback + retry) ─────────────────────────
    answer = call_gemini(question, clean_history)
    if answer:
        return jsonify({"answer": answer, "source": "gemini"})

    # ── Keyword fallback ───────────────────────────────────────────────────────
    answer = keyword_answer(question)
    if not answer:
        answer = (
            "I'm having trouble connecting to the AI service right now. "
            "For election-related questions, I can still help with:\n\n"
            "• Voter ID requirements\n"
            "• Finding your polling booth\n"
            "• NOTA explanation\n"
            "• Registration deadlines\n"
            "• Postal ballots\n"
            "• Aadhaar linking\n\n"
            "Try asking about one of these topics, or try again in a moment!"
        )
    return jsonify({"answer": answer, "source": "keyword"})

# ── API: Booth Finder ──────────────────────────────────────────────────────────

@app.route("/api/booth", methods=["POST"])
@rate_limit(max_requests=30, window=60)
def find_booth():
    data = request.get_json() or {}
    query = sanitize_input(data.get("query", ""), max_length=200).lower()

    if not query:
        return jsonify({"error": "Please provide a search query"}), 400

    result = None
    for city, info in BOOTHS.items():
        if city in query:
            result = info
            break

    if not result:
        result = {
            "name": "Government Primary School, Local Area",
            "address": "Based on your registered address — visit voters.eci.gov.in for exact booth",
            "ward": "Check via EPIC number at voterportal.eci.gov.in",
            "distance": "Usually within 2 km of your residence",
        }

    return jsonify({"booth": result})

# ── API: Glossary ──────────────────────────────────────────────────────────────

@app.route("/api/glossary", methods=["GET"])
@rate_limit(max_requests=60, window=60)
def glossary():
    q = sanitize_input(request.args.get("q", ""), max_length=100).lower()
    filtered = (
        [g for g in GLOSSARY if q in g["term"].lower() or q in g["def"].lower()]
        if q else GLOSSARY
    )
    return jsonify({"glossary": filtered})

# ── API: Tips ──────────────────────────────────────────────────────────────────

@app.route("/api/tip", methods=["GET"])
@rate_limit(max_requests=60, window=60)
def tip():
    return jsonify({"tip": random.choice(TIPS)})

# ── API: Election Statistics ───────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
@rate_limit(max_requests=60, window=60)
def election_stats():
    """Return key election statistics for the stats dashboard."""
    return jsonify({"stats": [
        {"label": "Registered Voters", "value": "968M+", "icon": "👥", "trend": "+3.2%"},
        {"label": "Polling Stations", "value": "1.05M", "icon": "🏫", "trend": "+5%"},
        {"label": "Avg. Turnout 2024", "value": "65.8%", "icon": "📊", "trend": "+1.1%"},
        {"label": "EVM Machines", "value": "5.5M", "icon": "🗳️", "trend": "Active"},
        {"label": "States & UTs", "value": "36", "icon": "🗺️", "trend": "All covered"},
        {"label": "Constituencies", "value": "543", "icon": "📍", "trend": "Lok Sabha"},
    ]})

# ── API: User Feedback ─────────────────────────────────────────────────────────

@app.route("/api/feedback", methods=["POST"])
@rate_limit(max_requests=5, window=300)
def submit_feedback():
    """Accept user feedback for continuous improvement."""
    data = request.get_json() or {}
    rating = data.get("rating", 0)
    comment = sanitize_input(data.get("comment", ""), max_length=500)
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be 1-5"}), 400
    logger.info(f"Feedback received: rating={rating}, comment={comment[:50]}")
    return jsonify({"ok": True, "message": "Thank you for your feedback!"})

# ── API: User session ──────────────────────────────────────────────────────────

@app.route("/api/session", methods=["POST"])
@rate_limit(max_requests=10, window=60)
def save_session():
    data = request.get_json() or {}
    session_id = validate_session_id(data.get("session"))
    user = data.get("user", {})

    # Sanitize user data
    if isinstance(user, dict):
        clean_user = {
            "name": sanitize_input(str(user.get("name", "Voter")), max_length=50),
            "state": sanitize_input(str(user.get("state", "")), max_length=50),
            "firstTime": bool(user.get("firstTime", False)),
        }
    else:
        clean_user = {"name": "Voter", "state": "", "firstTime": False}

    if session_id:
        if session_id not in sessions:
            sessions[session_id] = {}
        sessions[session_id]["user"] = clean_user
    return jsonify({"ok": True})

# ── Error Handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "Too many requests. Please slow down."}), 429

# ── ENTRY POINT ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"\n🚀 ElectraGuide v4.0 running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
