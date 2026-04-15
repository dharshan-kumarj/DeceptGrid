"""
models.py – SQLAlchemy 2.0 ORM models for all DeceptGrid security tables.

Each class maps 1:1 to a table in database/init.sql.
Use `from backend.models import <Model>` in route handlers.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    certs: Mapped[list["AuthorizedCert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    otp_challenges: Mapped[list["OtpChallenge"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    security_logs: Mapped[list["SecurityLog"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User username={self.username!r}>"


# ---------------------------------------------------------------------------
# authorized_certs
# ---------------------------------------------------------------------------
class AuthorizedCert(Base):
    __tablename__ = "authorized_certs"
    __table_args__ = (
        Index(
            "idx_authorized_certs_fingerprint",
            "fingerprint_sha256",
            postgresql_where="revoked = FALSE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 64-char hex-encoded SHA-256, no colons
    fingerprint_sha256: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    common_name: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(128))
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="certs")

    def __repr__(self) -> str:
        return f"<AuthorizedCert cn={self.common_name!r} revoked={self.revoked}>"


# ---------------------------------------------------------------------------
# otp_challenges
# ---------------------------------------------------------------------------
class OtpChallenge(Base):
    __tablename__ = "otp_challenges"
    __table_args__ = (
        Index(
            "idx_otp_challenges_session",
            "session_id",
            postgresql_where="used = FALSE",
        ),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_meter: Mapped[str] = mapped_column(String(64), nullable=False)
    # SHA-256 hex of the raw 6-digit OTP; never store plaintext
    otp_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    client_ip: Mapped[str] = mapped_column(INET, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="otp_challenges")

    def __repr__(self) -> str:
        return f"<OtpChallenge session_id={self.session_id} used={self.used}>"


# ---------------------------------------------------------------------------
# failed_attempts
# ---------------------------------------------------------------------------
class FailedAttempt(Base):
    __tablename__ = "failed_attempts"
    __table_args__ = (
        Index("idx_failed_attempts_ip", "client_ip"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # INET is stored as a Python str (IPv4 or IPv6 text)
    client_ip: Mapped[str] = mapped_column(INET, unique=True, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<FailedAttempt ip={self.client_ip!r} count={self.attempt_count}>"
        )


# ---------------------------------------------------------------------------
# isolated_hosts
# ---------------------------------------------------------------------------
class IsolatedHost(Base):
    __tablename__ = "isolated_hosts"
    __table_args__ = (
        Index(
            "idx_isolated_hosts_ip",
            "client_ip",
            postgresql_where="lifted_at IS NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_ip: Mapped[str] = mapped_column(INET, unique=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    isolated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    lifted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    lifted_by: Mapped[Optional[str]] = mapped_column(String(64))

    def __repr__(self) -> str:
        return (
            f"<IsolatedHost ip={self.client_ip!r} active={self.lifted_at is None}>"
        )


# ---------------------------------------------------------------------------
# security_logs  (append-only)
# ---------------------------------------------------------------------------

# Allowed event type constants – import these everywhere instead of
# using raw strings to prevent typos.
class EventType:
    CERT_AUTH_SUCCESS = "CERT_AUTH_SUCCESS"
    CERT_AUTH_FAILED  = "CERT_AUTH_FAILED"
    OTP_REQUESTED     = "OTP_REQUESTED"
    OTP_FAILED        = "OTP_FAILED"
    OTP_SUCCESS       = "OTP_SUCCESS"
    HOST_ISOLATED     = "HOST_ISOLATED"


class Severity:
    INFO = "INFO"
    WARN = "WARN"
    CRIT = "CRIT"


class SecurityLog(Base):
    __tablename__ = "security_logs"
    __table_args__ = (
        Index("idx_security_logs_event_type", "event_type", "created_at"),
        Index("idx_security_logs_ip", "client_ip", "created_at"),
        Index("idx_security_logs_user", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    client_ip: Mapped[Optional[str]] = mapped_column(INET)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # Arbitrary structured context (cert fingerprint, error messages, etc.)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    severity: Mapped[str] = mapped_column(
        String(8), nullable=False, default=Severity.INFO
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="security_logs")

    def __repr__(self) -> str:
        return f"<SecurityLog event={self.event_type!r} ip={self.client_ip!r}>"
