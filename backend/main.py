from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pathlib import Path

# Create FastAPI application
app = FastAPI(
    title="DeceptGrid Backend API",
    description="Smart grid cybersecurity simulation backend - Person C",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize required directories and files on startup."""
    # Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("routes", exist_ok=True)
    os.makedirs("utils", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # Initialize attack_logs.json if it doesn't exist
    attack_logs_path = Path("data/attack_logs.json")
    if not attack_logs_path.exists():
        with open(attack_logs_path, "w") as f:
            json.dump([], f, indent=2)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "DeceptGrid Backend API is running", "status": "active"}

@app.get("/api/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "service": "DeceptGrid Backend - Person C"}

# Import and register routers
from routes.steg import router as steg_router
from routes.attack_extra import router as attack_router

app.include_router(steg_router, prefix="/api/steg", tags=["steganography"])
app.include_router(attack_router, prefix="/api/attacks", tags=["attacks"])
