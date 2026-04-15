"""
auth.py – mTLS Certificate Authentication Layer

Responsibilities:
  1. Extract the client certificate from the ASGI request scope (set by uvicorn SSL).
  2. Parse the PEM cert using the `cryptography` library.
  3. Compute the SHA-256 fingerprint and extract the Common Name (CN).
  4. Verify the fingerprint against the `authorized_certs` table.
  5. Reject revoked, missing, or unrecognised certs with a 403.
  6. Write a SecurityLog row for every auth attempt (success + failure).

The FastAPI dependency `require_mtls_cert` is what route handlers use:

  @router.get("/api/meter/voltage")
  async def voltage(
      cert_info: CertInfo = Depends(require_mtls_cert),
      db: AsyncSession = Depends(get_db),
  ):
      ...
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.security import AuthorizedCert, EventType, SecurityLog, Severity, User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data transfer object returned to route handlers after successful auth
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CertInfo:
    fingerprint: str        # 64-char hex SHA-256, no colons
    common_name: str
    user: User              # fully-loaded ORM row


# ---------------------------------------------------------------------------
# Certificate parsing helpers
# ---------------------------------------------------------------------------

def _parse_pem_cert(pem_bytes: bytes) -> x509.Certificate:
    """
    Parse a PEM-encoded certificate.
    Raises ValueError if the bytes are not a valid PEM certificate.
    """
    try:
        return x509.load_pem_x509_certificate(pem_bytes)
    except Exception as exc:
        raise ValueError(f"Failed to parse client certificate: {exc}") from exc


def _fingerprint_sha256(cert: x509.Certificate) -> str:
    """
    Return the SHA-256 fingerprint of `cert` as a lowercase hex string
    WITHOUT colons, matching the format stored in `authorized_certs`.
    """
    raw = cert.fingerprint(hashes.SHA256())
    return raw.hex()


def _common_name(cert: x509.Certificate) -> Optional[str]:
    """Extract the CN attribute from the certificate Subject, or None."""
    try:
        return cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except (IndexError, Exception):
        return None


def extract_cert_info_from_pem(pem_bytes: bytes) -> tuple[str, Optional[str]]:
    """
    Parse a PEM cert and return (fingerprint_hex, common_name).
    Public helper used in tests without a live Request.
    """
    cert = _parse_pem_cert(pem_bytes)
    return _fingerprint_sha256(cert), _common_name(cert)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

async def _get_authorized_cert(
    fingerprint: str, db: AsyncSession
) -> Optional[AuthorizedCert]:
    """Query the active (non-revoked) cert row matching `fingerprint`."""
    stmt = (
        select(AuthorizedCert)
        .where(
            AuthorizedCert.fingerprint_sha256 == fingerprint,
            AuthorizedCert.revoked == False,  # noqa: E712
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_user(user_id, db: AsyncSession) -> Optional[User]:
    stmt = select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _log_event(
    db: AsyncSession,
    event_type: str,
    severity: str,
    client_ip: Optional[str],
    user_id=None,
    session_id=None,
    details: Optional[dict] = None,
) -> None:
    """Insert one row into security_logs. Never raises – failures are swallowed."""
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
        # Caller commits via get_db context; we don't flush here.
    except Exception:
        logger.exception("Failed to write security log row — non-fatal")


# ---------------------------------------------------------------------------
# FastAPI dependency: require_mtls_cert
# ---------------------------------------------------------------------------

async def require_mtls_cert(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CertInfo:
    """
    FastAPI dependency.  Validates the mTLS client certificate and returns
    a CertInfo object if authentication succeeds.  Raises HTTP 403 otherwise.

    How the cert reaches here:
      - Uvicorn is started with --ssl-certfile, --ssl-keyfile, --ssl-ca-certs,
        and ssl.CERT_REQUIRED enforced.
      - The negotiated peer certificate is available in the ASGI scope under
        the key "ssl_object" (transport's SSL object), accessible via
        request.scope["ssl_object"].getpeercert(binary_form=True) / DER form,
        OR as the raw PEM string in the X-Client-Cert header when nginx
        terminates TLS and forwards the cert as a header.
      - For direct uvicorn TLS: we read the DER bytes from the transport's
        SSL object and convert to PEM for parsing.
      - For nginx passthrough (SSL_CLIENT_CERT header): we read the header.
    """
    client_ip: Optional[str] = _get_client_ip(request)

    # ---------- Step 1: extract raw certificate bytes ----------
    pem_bytes = await _extract_raw_cert(request)

    if pem_bytes is None:
        await _log_event(
            db,
            EventType.CERT_AUTH_FAILED,
            Severity.WARN,
            client_ip,
            details={"reason": "No client certificate presented"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client certificate required",
        )

    # ---------- Step 2: parse & extract fingerprint / CN ----------
    try:
        fingerprint, cn = extract_cert_info_from_pem(pem_bytes)
    except ValueError as exc:
        await _log_event(
            db,
            EventType.CERT_AUTH_FAILED,
            Severity.WARN,
            client_ip,
            details={"reason": "Certificate parse error", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid client certificate format",
        )

    # ---------- Step 3: look up fingerprint in DB ----------
    cert_row = await _get_authorized_cert(fingerprint, db)

    if cert_row is None:
        await _log_event(
            db,
            EventType.CERT_AUTH_FAILED,
            Severity.WARN,
            client_ip,
            details={
                "reason": "Fingerprint not in authorized_certs or cert revoked",
                "fingerprint": fingerprint,
                "cn": cn,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Certificate not authorised",
        )

    # ---------- Step 4: load and validate the user ----------
    user = await _get_user(cert_row.user_id, db)

    if user is None:
        await _log_event(
            db,
            EventType.CERT_AUTH_FAILED,
            Severity.CRIT,
            client_ip,
            details={
                "reason": "Cert references inactive or deleted user",
                "fingerprint": fingerprint,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Associated user account is disabled",
        )

    # ---------- Step 5: success ----------
    await _log_event(
        db,
        EventType.CERT_AUTH_SUCCESS,
        Severity.INFO,
        client_ip,
        user_id=user.id,
        details={"fingerprint": fingerprint, "cn": cn},
    )

    return CertInfo(fingerprint=fingerprint, common_name=cn or "", user=user)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> Optional[str]:
    """
    Best-effort client IP extraction.
    Respects X-Forwarded-For if set by a trusted proxy (nginx/traefik).
    """
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def _extract_raw_cert_via_socket():
    """Last resort: try to extract cert from current asyncio connection."""
    try:
        import asyncio
        task = asyncio.current_task()
        if task:
            print(f"[AUTH-SOCKET] Current task: {task.get_name()}")
            # Try to access the transport through asyncio context
            # This is hacky but might work
    except Exception as e:
        print(f"[AUTH-SOCKET] Error: {e}")
    return None


async def _extract_raw_cert(request: Request) -> Optional[bytes]:
    """
    Try to extract the client certificate PEM from the request.

    Strategy (in order of preference):
      1. X-Client-Cert header (set by nginx `ssl_client_cert` directive).
      2. The ASGI SSL transport object (direct uvicorn TLS).
    Returns PEM bytes or None.
    """
    # 1. Header-based (nginx forward)
    header_cert = request.headers.get("X-Client-Cert")
    if header_cert:
        print("[AUTH] ✓ Found cert in X-Client-Cert header")
        # nginx URL-encodes the PEM; decode it back.
        from urllib.parse import unquote
        decoded = unquote(header_cert)
        return decoded.encode("ascii")
    else:
        print("[AUTH] No X-Client-Cert header found")

    print(f"[AUTH] DEBUG: scope keys: {list(request.scope.keys())}")
    client = request.scope.get("client")
    print(f"[AUTH] DEBUG: client: {client}")
    # 2. Direct ASGI SSL transport
    ssl_obj = request.scope.get("ssl_object")
    print(f"[AUTH] ✓ ssl_object in scope: {ssl_obj is not None}")
    if ssl_obj is not None:
        try:
            der = ssl_obj.getpeercert(binary_form=True)
            print(f"[AUTH] ✓ peercert (binary) length: {len(der) if der else 0}")
            if der:
                # Convert DER → PEM
                from cryptography.hazmat.primitives.serialization import Encoding as Enc
                cert = x509.load_der_x509_certificate(der)
                print("[AUTH] ✓ Successfully converted DER → PEM from ssl_object")
                return cert.public_bytes(Enc.PEM)
        except Exception as e:
            print(f"[AUTH] ✗ Error getting peercert: {e}")

    # 3. Check transport extra info (fallback)
    print("[AUTH] Checking transport fallback...")
    transport = request.scope.get("transport")
    if transport:
        print(f"[AUTH] Transport exists")
        try:
            ssl_obj = transport.get_extra_info("ssl_object")
            print(f"[AUTH] ssl_object from transport.get_extra_info: {ssl_obj is not None}")
            if ssl_obj is not None:
                der = ssl_obj.getpeercert(binary_form=True)
                if der:
                    from cryptography.hazmat.primitives.serialization import Encoding as Enc
                    cert = x509.load_der_x509_certificate(der)
                    print("[AUTH] ✓ Successfully extracted from transport fallback")
                    return cert.public_bytes(Enc.PEM)
        except Exception as e:
            print(f"[AUTH] ✗ Transport error: {e}")
    else:
        print("[AUTH] No transport in scope")

    print("[AUTH] ✗ No certificate extraction method worked")
    return None
