-- DeceptGrid Security System - PostgreSQL Schema
-- Initialises all tables required for mTLS auth + OTP gateway

-- Enable pgcrypto for uuid generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- TABLE: users
-- Registered grid engineers who may authenticate to the system
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(64)  UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    full_name     VARCHAR(255) NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: authorized_certs
-- Maps a certificate SHA-256 fingerprint to a user.
-- Only certs present here (and signed by CA) are accepted.
-- ============================================================
CREATE TABLE IF NOT EXISTS authorized_certs (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fingerprint_sha256 CHAR(64)   UNIQUE NOT NULL,  -- hex-encoded SHA-256, no colons
    common_name      VARCHAR(255) NOT NULL,
    serial_number    VARCHAR(128),
    issued_at        TIMESTAMPTZ,
    expires_at       TIMESTAMPTZ,
    revoked          BOOLEAN      NOT NULL DEFAULT FALSE,
    revoked_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_authorized_certs_fingerprint
    ON authorized_certs (fingerprint_sha256)
    WHERE revoked = FALSE;

-- ============================================================
-- TABLE: otp_challenges
-- One row per active OTP session.
-- otp_hash stores bcrypt/sha256 hash of the 6-digit code.
-- ============================================================
CREATE TABLE IF NOT EXISTS otp_challenges (
    session_id     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_meter   VARCHAR(64)  NOT NULL,
    otp_hash       VARCHAR(256) NOT NULL,   -- SHA-256 hex of the raw OTP
    client_ip      INET         NOT NULL,
    expires_at     TIMESTAMPTZ  NOT NULL,
    used           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_otp_challenges_session
    ON otp_challenges (session_id)
    WHERE used = FALSE;

-- Auto-cleanup: sessions older than 1 hour are irrelevant; handled by app logic.

-- ============================================================
-- TABLE: failed_attempts
-- Tracks consecutive OTP failures per client IP.
-- Reset to 0 on any successful OTP verify.
-- ============================================================
CREATE TABLE IF NOT EXISTS failed_attempts (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_ip      INET        UNIQUE NOT NULL,
    attempt_count  INTEGER     NOT NULL DEFAULT 0,
    last_attempt   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_failed_attempts_ip
    ON failed_attempts (client_ip);

-- ============================================================
-- TABLE: isolated_hosts
-- IPs permanently blocked after exceeding failure threshold.
-- Only a manual admin action (or TTL in app logic) lifts isolation.
-- ============================================================
CREATE TABLE IF NOT EXISTS isolated_hosts (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_ip      INET        UNIQUE NOT NULL,
    reason         TEXT        NOT NULL,
    isolated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    lifted_at      TIMESTAMPTZ,           -- NULL = still isolated
    lifted_by      VARCHAR(64)            -- admin who lifted isolation
);

CREATE INDEX IF NOT EXISTS idx_isolated_hosts_ip
    ON isolated_hosts (client_ip)
    WHERE lifted_at IS NULL;   -- partial index: only active isolations

-- ============================================================
-- TABLE: security_logs
-- Append-only audit trail for all security events.
-- Never UPDATE or DELETE rows here.
-- ============================================================
CREATE TABLE IF NOT EXISTS security_logs (
    id             BIGSERIAL    PRIMARY KEY,
    event_type     VARCHAR(32)  NOT NULL,   -- CERT_AUTH_SUCCESS | CERT_AUTH_FAILED |
                                            -- OTP_REQUESTED | OTP_FAILED |
                                            -- OTP_SUCCESS | HOST_ISOLATED
    client_ip      INET,
    user_id        UUID         REFERENCES users(id) ON DELETE SET NULL,
    session_id     UUID,
    details        JSONB        NOT NULL DEFAULT '{}',
    severity       VARCHAR(8)   NOT NULL DEFAULT 'INFO',  -- INFO | WARN | CRIT
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_logs_event_type
    ON security_logs (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_logs_ip
    ON security_logs (client_ip, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_logs_user
    ON security_logs (user_id, created_at DESC);

-- ============================================================
-- TRIGGER: keep updated_at current on mutable tables
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER trg_failed_attempts_updated_at
    BEFORE UPDATE ON failed_attempts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- SEED: demo infrastructure
-- ============================================================
INSERT INTO users (username, email, full_name)
VALUES ('sarah', 'dharshankumarj.dev@gmail.com', 'Sarah Engineer')
ON CONFLICT (username) DO NOTHING;

-- Seed Sarah's cert in authorized_certs table
-- Fingerprint generated by certs/generate_certs.sh
INSERT INTO authorized_certs (user_id, fingerprint_sha256, common_name)
SELECT id, 'a1c13612ff348aa51e6410bfd791de93669c73efa90414199b1bd9bb399e9306', 'sarah@gridco.local'
FROM users WHERE username = 'sarah'
ON CONFLICT (fingerprint_sha256) DO NOTHING;
