"""
GridShield Engineer Dashboard — FastAPI Backend
Port: 8001
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="GridShield Engineer Dashboard API", version="1.0.0")

# CORS — allow all origins in dev mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "shared", "attack_logs.json"))

# ── Hardcoded credentials ─────────────────────────────────────────────
VALID_USERNAME = "engineer1"
VALID_PASSWORD = "grid@secure"

# ── Mock data fallback ─────────────────────────────────────────────────
MOCK_ENTRIES = [
    {"time": "10:34", "ip": "192.168.1.45", "type": "BruteForce", "severity": "HIGH", "target": "Honeypot_01"},
    {"time": "10:33", "ip": "10.0.0.12", "type": "LoginBlocked", "severity": "MEDIUM", "target": "Honeypot_02"},
    {"time": "10:32", "ip": "172.16.5.99", "type": "RateLimited", "severity": "LOW", "target": "Honeypot_01"},
    {"time": "10:31", "ip": "203.0.113.7", "type": "BruteForce", "severity": "HIGH", "target": "Honeypot_01"},
    {"time": "10:30", "ip": "198.51.100.22", "type": "LoginSuccess", "severity": "LOW", "target": "RealMeter_01"},
    {"time": "10:29", "ip": "192.168.1.100", "type": "BruteForce", "severity": "HIGH", "target": "Honeypot_02"},
    {"time": "10:28", "ip": "10.0.0.55", "type": "LoginBlocked", "severity": "MEDIUM", "target": "Honeypot_01"},
    {"time": "10:27", "ip": "172.16.5.3", "type": "RateLimited", "severity": "MEDIUM", "target": "Honeypot_01"},
    {"time": "10:26", "ip": "203.0.113.44", "type": "BruteForce", "severity": "HIGH", "target": "RealMeter_01"},
    {"time": "10:25", "ip": "198.51.100.8", "type": "LoginSuccess", "severity": "LOW", "target": "RealMeter_01"},
]


def read_log_entries() -> list[dict]:
    """Read log entries from the shared log file.
    Handles both JSON array and newline-delimited JSON formats.
    Falls back to mock data if the file is missing or empty."""
    if not os.path.exists(LOG_PATH):
        return list(MOCK_ENTRIES)

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return list(MOCK_ENTRIES)

        # Try JSON array first
        if content.startswith("["):
            entries = json.loads(content)
            if isinstance(entries, list):
                return entries

        # Try newline-delimited JSON (NDJSON)
        entries = []
        for line in content.split("\n"):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return entries if entries else list(MOCK_ENTRIES)

    except Exception:
        return list(MOCK_ENTRIES)


# ── Models ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str
    typing_speed_wpm: float = 0
    time_on_page_sec: float = 0
    mouse_event_count: int = 0


# ── Endpoints ──────────────────────────────────────────────────────────

@app.post("/login")
async def login(req: LoginRequest):
    # Validate credentials
    if req.username != VALID_USERNAME or req.password != VALID_PASSWORD:
        return {"success": False, "message": "Invalid credentials"}

    # Compute behaviour score
    score = 100
    if req.typing_speed_wpm > 120:
        score -= 40
    if req.time_on_page_sec < 3:
        score -= 30
    if req.mouse_event_count < 5:
        score -= 20
    score = max(score, 0)

    # Risk label
    if score >= 70:
        risk_label = "NORMAL"
    elif score >= 40:
        risk_label = "SUSPICIOUS"
    else:
        risk_label = "BOT"

    return {
        "success": True,
        "token": "mock-jwt-token",
        "behaviour_score": score,
        "risk_label": risk_label,
    }


@app.get("/logs/honeypot")
async def get_honeypot_logs(limit: int = Query(20, ge=1, le=200)):
    entries = read_log_entries()
    honeypot = [e for e in entries if e.get("target", "").startswith("Honeypot")]
    # Return last `limit` entries, newest first (assuming file is newest-first)
    return honeypot[:limit]


@app.get("/logs/meter-status")
async def get_meter_status():
    entries = read_log_entries()

    real_entries = [e for e in entries if e.get("target") == "RealMeter_01"]
    fake_entries = [e for e in entries if e.get("target", "").startswith("Honeypot")]

    # Determine if real meter is under attack (entries in last 5 minutes)
    now = datetime.now()
    real_under_attack = False
    for e in real_entries:
        try:
            t = datetime.strptime(e["time"], "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            if now - t < timedelta(minutes=5):
                real_under_attack = True
                break
        except (ValueError, KeyError):
            continue

    real_meter = {
        "status": "UNDER_ATTACK" if real_under_attack else "SECURE",
        "attack_count": len(real_entries),
        "last_ip": real_entries[0]["ip"] if real_entries else None,
        "last_time": real_entries[0]["time"] if real_entries else None,
    }

    fake_meter = {
        "status": "UNDER_ATTACK" if fake_entries else "IDLE",
        "attack_count": len(fake_entries),
        "last_ip": fake_entries[0]["ip"] if fake_entries else None,
        "last_type": fake_entries[0]["type"] if fake_entries else None,
        "last_time": fake_entries[0]["time"] if fake_entries else None,
    }

    return {"real_meter": real_meter, "fake_meter": fake_meter}


@app.get("/logs/auth")
async def get_auth_logs(limit: int = Query(30, ge=1, le=200)):
    entries = read_log_entries()

    auth_types = {"BruteForce", "LoginBlocked", "LoginSuccess", "RateLimited"}
    auth_entries = [e for e in entries if e.get("type") in auth_types][:limit]

    blocked_types = {"BruteForce", "LoginBlocked", "RateLimited"}
    blocked = [e for e in auth_entries if e.get("type") in blocked_types]
    allowed = [e for e in auth_entries if e.get("type") == "LoginSuccess"]

    return {"blocked": blocked, "allowed": allowed}


@app.get("/logs/stream")
async def stream_logs():
    """Server-Sent Events endpoint — streams new log lines every 2 seconds."""

    async def event_generator():
        last_count = 0
        while True:
            entries = read_log_entries()
            current_count = len(entries)

            if current_count > last_count:
                new_entries = entries[: current_count - last_count] if last_count > 0 else entries
                for entry in new_entries:
                    yield {"event": "log", "data": json.dumps(entry)}
                last_count = current_count

            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())


# ── Run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
