"""
ElectraGuide v2.0 — Flask backend
Deployable on Google Cloud Run
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="public")
CORS(app)

# ── In-memory session store (use Redis/Firestore for production) ──────────────
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
]

CHAT_KB = {
    "id": "You need your Voter ID card (EPIC), or any ONE of: Aadhaar, PAN, Passport, Driving Licence, or MNREGA Job Card. Originals only — no photocopies.\n\n✅ Source: Election Commission of India",
    "nota": "NOTA = None Of The Above. Lets you register dissent without supporting any candidate. Your vote counts but goes to no party. Introduced in 2013 by the Supreme Court.\n\n✅ Source: ECI",
    "booth": "Visit voters.eci.gov.in → Search by EPIC number or mobile. Or SMS EPIC <voter-id> to 1950. Your booth is usually the nearest government school or community hall in your ward.\n\n📍 Source: ECI Portal",
    "register": "Registration closes 30 days before Election Day. Apply on nvsp.in or the Voter Helpline App. Call 1950 for state-specific dates.\n\n✅ Source: NVSP",
    "postal": "Apply for postal ballot if you're a service voter, senior citizen (80+), or person with disability. Form 12D must be submitted to your Returning Officer.\n\n✅ Source: ECI",
    "aadhaar": "Linking Aadhaar to your Voter ID is voluntary but recommended for de-duplication. Link via nvsp.in or the Voter Helpline App.\n\n✅ Source: ECI",
}

BOOTHS = {
    "delhi": {"name": "Govt. Boys Sr. Secondary School, Sector 14", "address": "Dwarka Sector 14, New Delhi — 110078", "ward": "Ward 142, Dwarka Sector-14", "distance": "0.8 km"},
    "mumbai": {"name": "Municipal School, Andheri West", "address": "Jai Hind Colony, Andheri West, Mumbai — 400058", "ward": "K/West Ward — Andheri", "distance": "1.2 km"},
    "bangalore": {"name": "Government Primary School, Koramangala", "address": "5th Block, Koramangala, Bengaluru — 560095", "ward": "Ward 151 — Koramangala", "distance": "0.6 km"},
}

DEFAULT_CHECKLIST = [
    {"id": 0, "title": "Register on Voter ID portal", "meta": "nvsp.in · Required", "tag": "done", "done": True},
    {"id": 1, "title": "Verify Aadhaar linkage", "meta": "voters.eci.gov.in · Required", "tag": "done", "done": True},
    {"id": 2, "title": "Find your polling booth", "meta": "Due 7 days before election · Urgent", "tag": "urgent", "done": False},
    {"id": 3, "title": "Download Voter ID slip (e-EPIC)", "meta": "voterportal.eci.gov.in", "tag": "pending", "done": False},
    {"id": 4, "title": "Set Election Day reminder", "meta": "Optional but recommended", "tag": "pending", "done": False},
]

TIPS = [
    "India has over 900 million registered voters — the world's largest democratic electorate.",
    "EVMs have been used in Indian elections since 1998.",
    "NOTA was introduced in 2013 following a Supreme Court ruling.",
    "Voting typically takes less than 5 minutes at the booth.",
    "Women account for nearly 49% of India's registered voters as of 2024.",
    "Mobile phones are NOT allowed inside polling booths during voting.",
    "The Election Commission of India was established in 1950.",
    "You can track your vote application status on nvsp.in anytime.",
]

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "electraguide", "version": "2.0"})

# ── API: Checklist ─────────────────────────────────────────────────────────────

@app.route("/api/checklist", methods=["GET"])
def get_checklist():
    session_id = request.args.get("session", "default")
    checklist = sessions.get(session_id, {}).get("checklist", DEFAULT_CHECKLIST)
    return jsonify({"checklist": checklist})

@app.route("/api/checklist/toggle", methods=["POST"])
def toggle_checklist():
    data = request.get_json()
    session_id = data.get("session", "default")
    item_id = data.get("id")

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

# ── API: Chat ──────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question", "").lower()

    answer = None
    for key, response in CHAT_KB.items():
        if key in question:
            answer = response
            break

    if not answer:
        if any(w in question for w in ["vote", "voting", "election", "ballot"]):
            answer = "For your specific query, I recommend:\n\n• voters.eci.gov.in — official ECI portal\n• Voter Helpline: 1950 (toll-free)\n• nvsp.in — National Voters' Service Portal\n\nI can answer questions about IDs, booths, NOTA, registration, postal ballots, and Aadhaar linking."
        else:
            answer = "I can only assist with voting and election-related questions. Try asking about voter ID requirements, finding your booth, NOTA, or registration deadlines!"

    return jsonify({"answer": answer})

# ── API: Booth Finder ──────────────────────────────────────────────────────────

@app.route("/api/booth", methods=["POST"])
def find_booth():
    data = request.get_json()
    query = data.get("query", "").lower()

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
            "distance": "Usually within 2 km of your residence"
        }

    return jsonify({"booth": result})

# ── API: Glossary ──────────────────────────────────────────────────────────────

@app.route("/api/glossary", methods=["GET"])
def glossary():
    q = request.args.get("q", "").lower()
    if q:
        filtered = [g for g in GLOSSARY if q in g["term"].lower() or q in g["def"].lower()]
    else:
        filtered = GLOSSARY
    return jsonify({"glossary": filtered})

# ── API: Tips ──────────────────────────────────────────────────────────────────

@app.route("/api/tip", methods=["GET"])
def tip():
    import random
    return jsonify({"tip": random.choice(TIPS)})

# ── API: User session ──────────────────────────────────────────────────────────

@app.route("/api/session", methods=["POST"])
def save_session():
    data = request.get_json()
    session_id = data.get("session")
    user = data.get("user", {})
    if session_id:
        if session_id not in sessions:
            sessions[session_id] = {}
        sessions[session_id]["user"] = user
    return jsonify({"ok": True})

# ── ENTRY POINT ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
