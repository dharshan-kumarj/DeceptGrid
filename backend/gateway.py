"""
gateway.py – Layer 2 OTP Gateway

Standalone FastAPI application running on port 8001.
Simulates a network-isolated access gateway that sits between the engineering
VLAN (where clients connect) and the meter VLAN (isolated subnet).

Security flow:
  1. Client POSTs username + target_meter to /gateway/request-access.
     → Gateway checks IP not isolated, generates cryptographically-random OTP,
       stores its SHA-256 hash in otp_challenges, emails the OTP.
  2. Client POSTs session_id + otp_code to /gateway/verify-otp.
     → Gateway constant-time-compares hash, marks session used, returns JWT.
     → On failure: increments failed_attempts; ≥ ISOLATION_THRESHOLD → isolates IP.

Rate limiting is applied per-IP on both endpoints via slowapi.
"""

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from email_service import send_otp_email
from models.security import (
    EventType,
    FailedAttempt,
    IsolatedHost,
    OtpChallenge,
    SecurityLog,
    Severity,
    User,
)

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OTP_EXPIRY_SECONDS: int = int(os.environ.get("OTP_EXPIRY_SECONDS", "300"))   # 5 min
ISOLATION_THRESHOLD: int = int(os.environ.get("ISOLATION_THRESHOLD", "3"))

# ---------------------------------------------------------------------------
# Rate limiter setup
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
gateway = FastAPI(
    title="DeceptGrid OTP Gateway",
    description="Layer 2 – OTP-based access gateway for smart grid meters",
    version="1.0.0",
)
gateway.state.limiter = limiter
gateway.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

gateway.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AccessRequest(BaseModel):
    username: str
    target_meter: str


class AccessResponse(BaseModel):
    session_id: str
    message: str


class VerifyRequest(BaseModel):
    session_id: str
    otp_code: str


class VerifyResponse(BaseModel):
    access: str      # "granted"
    target_meter: str
    username: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_otp(otp_plaintext: str) -> str:
    """SHA-256 hex digest of the plaintext OTP."""
    return hashlib.sha256(otp_plaintext.encode()).hexdigest()


def _generate_otp() -> str:
    """
    Generate a cryptographically-random 6-digit numeric OTP.
    secrets.randbelow is used instead of random to ensure uniform distribution
    without modulo bias.
    """
    return str(secrets.randbelow(1_000_000)).zfill(6)


def _get_client_ip(request: Request) -> str:
    """Best-effort IP extraction, respecting X-Forwarded-For."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _is_isolated(ip: str, db: AsyncSession) -> bool:
    """Return True if the IP is in isolated_hosts with no lifted_at."""
    stmt = (
        select(IsolatedHost)
        .where(IsolatedHost.client_ip == ip, IsolatedHost.lifted_at.is_(None))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _get_user_by_username(username: str, db: AsyncSession) -> Optional[User]:
    stmt = select(User).where(User.username == username, User.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _log_event(
    db: AsyncSession,
    event_type: str,
    severity: str,
    client_ip: Optional[str] = None,
    user_id=None,
    session_id=None,
    details: Optional[dict] = None,
) -> None:
    """Insert one row into security_logs.  Errors are logged, never raised."""
    try:
        log = SecurityLog(
            event_type=event_type,
            severity=severity,
            client_ip=client_ip,
            user_id=user_id,
            session_id=session_id,
            details=details or {},
        )
        db.add(log)
    except Exception:
        logger.exception("Non-fatal: failed to write security_log row")


async def _increment_failed_attempts(ip: str, db: AsyncSession) -> int:
    """
    Upsert a row in failed_attempts for `ip` and increment attempt_count.
    Returns the NEW count after incrementing.
    Uses PostgreSQL INSERT ... ON CONFLICT ... DO UPDATE for atomicity.
    """
    stmt = (
        pg_insert(FailedAttempt)
        .values(client_ip=ip, attempt_count=1, last_attempt=datetime.now(timezone.utc))
        .on_conflict_do_update(
            index_elements=["client_ip"],
            set_={
                "attempt_count": FailedAttempt.attempt_count + 1,
                "last_attempt": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        .returning(FailedAttempt.attempt_count)
    )
    result = await db.execute(stmt)
    row = result.fetchone()
    return row[0] if row else 1


async def _reset_failed_attempts(ip: str, db: AsyncSession) -> None:
    """Reset the attempt counter for `ip` after a successful OTP."""
    stmt = (
        update(FailedAttempt)
        .where(FailedAttempt.client_ip == ip)
        .values(attempt_count=0, updated_at=datetime.now(timezone.utc))
    )
    await db.execute(stmt)


async def _isolate_host(ip: str, reason: str, db: AsyncSession) -> None:
    """Insert into isolated_hosts (ignore conflict if already isolated)."""
    stmt = (
        pg_insert(IsolatedHost)
        .values(client_ip=ip, reason=reason)
        .on_conflict_do_nothing(index_elements=["client_ip"])
    )
    await db.execute(stmt)


# ---------------------------------------------------------------------------
# Startup hook: ensure DB tables exist (schema managed by init.sql in Docker,
# this is a safety check for non-Docker local runs).
# ---------------------------------------------------------------------------

@gateway.on_event("startup")
async def startup() -> None:
    logger.info("OTP Gateway starting — Layer 2 initialised")


# ---------------------------------------------------------------------------
# Middleware: block isolated IPs on every endpoint
# ---------------------------------------------------------------------------

@gateway.middleware("http")
async def block_isolated_ips(request: Request, call_next):
    """
    Reject any request from an IP currently in isolated_hosts.
    Runs before rate limiting and route handling.
    """
    # We need a DB session outside a route dependency.
    from database import AsyncSessionLocal
    client_ip = _get_client_ip(request)

    async with AsyncSessionLocal() as db:
        if await _is_isolated(client_ip, db):
            await _log_event(
                db,
                EventType.HOST_ISOLATED,
                Severity.CRIT,
                client_ip=client_ip,
                details={"reason": "Request blocked — IP is isolated"},
            )
            await db.commit()
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied: host isolated due to repeated failures"},
            )

    return await call_next(request)


# ---------------------------------------------------------------------------
# POST /gateway/request-access
# ---------------------------------------------------------------------------

@gateway.post(
    "/gateway/request-access",
    response_model=AccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP for meter access",
)
@limiter.limit("5/minute")
async def request_access(
    request: Request,
    body: AccessRequest,
    db: AsyncSession = Depends(get_db),
) -> AccessResponse:
    """
    Validates the requesting user, generates a 6-digit OTP, persists its
    SHA-256 hash in otp_challenges, and dispatches an email.
    Returns a session_id the client must present with the OTP.
    """
    client_ip = _get_client_ip(request)

    # --- Validate user ---
    user = await _get_user_by_username(body.username, db)
    if user is None:
        # Do NOT reveal whether username exists – same response either way.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or account inactive",
        )

    # --- Generate OTP ---
    otp_plaintext = _generate_otp()
    otp_hash = _hash_otp(otp_plaintext)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=OTP_EXPIRY_SECONDS)

    # --- Persist challenge ---
    challenge = OtpChallenge(
        user_id=user.id,
        target_meter=body.target_meter,
        otp_hash=otp_hash,
        client_ip=client_ip,
        expires_at=expires_at,
    )
    db.add(challenge)
    await db.flush()   # assigns session_id (UUID) before commit
    session_id = str(challenge.session_id)

    # --- Log event ---
    await _log_event(
        db,
        EventType.OTP_REQUESTED,
        Severity.INFO,
        client_ip=client_ip,
        user_id=user.id,
        session_id=challenge.session_id,
        details={"target_meter": body.target_meter},
    )

    # --- Send email (do this AFTER DB flush so session_id exists) ---
    try:
        await send_otp_email(
            to_address=user.email,
            otp_code=otp_plaintext,
            session_id=session_id,
            target_meter=body.target_meter,
        )
    except Exception as exc:
        # Email failure → rollback the challenge so the user can retry.
        logger.error("Failed to send OTP email to %r: %s", user.email, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to dispatch OTP email. Please retry.",
        )

    return AccessResponse(
        session_id=session_id,
        message="OTP dispatched to registered email. Valid for 5 minutes.",
    )


# ---------------------------------------------------------------------------
# POST /gateway/verify-otp
# ---------------------------------------------------------------------------

@gateway.post(
    "/gateway/verify-otp",
    response_model=VerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and obtain access token",
)
@limiter.limit("10/minute")
async def verify_otp(
    request: Request,
    body: VerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyResponse:
    """
    Validates the OTP submitted against the stored hash.
    - On success: marks session used, resets failure counter, returns confirmation.
    - On failure: increments counter; ≥ ISOLATION_THRESHOLD → isolates IP.
    """
    client_ip = _get_client_ip(request)

    # --- Load session ---
    try:
        import uuid
        session_uuid = uuid.UUID(body.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format",
        )

    stmt = (
        select(OtpChallenge)
        .where(
            OtpChallenge.session_id == session_uuid,
            OtpChallenge.used == False,  # noqa: E712
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    challenge: Optional[OtpChallenge] = result.scalar_one_or_none()

    if challenge is None:
        await _log_event(
            db,
            EventType.OTP_FAILED,
            Severity.WARN,
            client_ip=client_ip,
            session_id=session_uuid,
            details={"reason": "Session not found or already used"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired session",
        )

    now = datetime.now(timezone.utc)

    # --- Check expiry ---
    if now > challenge.expires_at.replace(tzinfo=timezone.utc):
        challenge.used = True   # prevent replay of expired sessions
        await _log_event(
            db,
            EventType.OTP_FAILED,
            Severity.WARN,
            client_ip=client_ip,
            user_id=challenge.user_id,
            session_id=challenge.session_id,
            details={"reason": "OTP session expired"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP has expired. Request a new one.",
        )

    # --- Constant-time comparison to prevent timing attacks ---
    submitted_hash = _hash_otp(body.otp_code)
    otp_valid = hmac.compare_digest(submitted_hash, challenge.otp_hash)

    if not otp_valid:
        # Increment failure counter
        new_count = await _increment_failed_attempts(client_ip, db)

        await _log_event(
            db,
            EventType.OTP_FAILED,
            Severity.WARN,
            client_ip=client_ip,
            user_id=challenge.user_id,
            session_id=challenge.session_id,
            details={
                "reason": "Incorrect OTP",
                "attempt_number": new_count,
                "isolation_threshold": ISOLATION_THRESHOLD,
            },
        )

        if new_count >= ISOLATION_THRESHOLD:
            await _isolate_host(
                client_ip,
                reason=f"Exceeded {ISOLATION_THRESHOLD} failed OTP attempts",
                db=db,
            )
            await _log_event(
                db,
                EventType.HOST_ISOLATED,
                Severity.CRIT,
                client_ip=client_ip,
                user_id=challenge.user_id,
                session_id=challenge.session_id,
                details={
                    "reason": "Auto-isolated after repeated OTP failures",
                    "failed_attempts": new_count,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Host isolated due to repeated authentication failures",
            )

        remaining = ISOLATION_THRESHOLD - new_count
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Incorrect OTP. {remaining} attempt(s) remaining before isolation.",
        )

    # --- OTP valid ---
    challenge.used = True   # mark single-use
    await _reset_failed_attempts(client_ip, db)

    # Load user for response
    user = await db.get(User, challenge.user_id)

    await _log_event(
        db,
        EventType.OTP_SUCCESS,
        Severity.INFO,
        client_ip=client_ip,
        user_id=challenge.user_id,
        session_id=challenge.session_id,
        details={"target_meter": challenge.target_meter},
    )

    return VerifyResponse(
        access="granted",
        target_meter=challenge.target_meter,
        username=user.username if user else "unknown",
    )
