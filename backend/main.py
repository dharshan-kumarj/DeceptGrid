from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

# New imports for Layer 1 & 2
from database import get_db
from auth import require_mtls_cert, CertInfo
from ssl_middleware import TransportCertificateMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for startup/shutdown."""
    print("[STARTUP] ✓ ClientCertificateMiddleware configured")
    yield


# Create FastAPI application
app = FastAPI(
    title="DeceptGrid Backend API",
    description="Smart grid cybersecurity simulation backend - Person C",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev servers
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


@app.get("/debug/scope")
async def debug_scope(request):
    """Debug endpoint to inspect what's available in request."""
    import json

    # Try to extract all available info
    result = {
        "client": request.client,
        "url": str(request.url),
        "headers_count": len(request.headers),
        "scope_type": request.scope.get("type"),
        "scheme": request.scope.get("scheme"),
    }

    # Check for SSL/cert info
    if "ssl_object" in request.scope:
        result["ssl_object_found"] = True

    # List all scope keys
    result["scope_keys"] = list(request.scope.keys())

    # Check extensions
    extensions = request.scope.get("extensions", {})
    result["extensions"] = list(extensions.keys()) if extensions else []

    return result

# Layer 1: mTLS Authenticated Endpoint
@app.get("/api/meter/voltage")
async def get_meter_voltage(
    cert_info: CertInfo = Depends(require_mtls_cert),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns meter voltage data.
    Requires a valid mTLS certificate signed by the custom CA and registered in authorized_certs.
    """
    return {
        "meter_id": "SM-REAL-051",
        "voltage": 220.5,
        "frequency": 50.0,
        "status": "operational",
        "authenticated_as": cert_info.common_name,
        "fingerprint": cert_info.fingerprint
    }

# Import and register routers
from routes.steg import router as steg_router
from routes.attack_extra import router as attack_router
from routes.ids import router as ids_router
from routes.otp import router as otp_router

app.include_router(steg_router, prefix="/api/steg", tags=["steganography"])
app.include_router(attack_router, prefix="/api/attacks", tags=["attacks"])
app.include_router(otp_router, prefix="/api/otp", tags=["layer2-otp"])
app.include_router(ids_router, prefix="/api/ids", tags=["layer3-ids", "layer4-honeypot"])

# Wrap the entire FastAPI app with the transport middleware at the very end
# This gives us access to the raw ASGI transport object
app = TransportCertificateMiddleware(app)
