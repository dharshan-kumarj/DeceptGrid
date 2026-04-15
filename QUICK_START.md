# DeceptGrid - Quick Start Guide

## 🚀 One-Command Startup

```bash
cd /home/dharshan/projects/DeceptGrid
./start_services.sh
```

This will:
- Start Backend API on http://127.0.0.1:8000
- Start mTLS Proxy on https://0.0.0.0:8443
- Show live logs and test commands

---

## ⚡ Quick Tests

### Layer 1: mTLS Certificate Authentication

**✅ Valid Certificate (Should succeed)**
```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

**Expected Output:**
```json
{
  "meter_id": "SM-REAL-051",
  "voltage": 220.5,
  "frequency": 50.0,
  "status": "operational",
  "authenticated_as": "sarah@gridco.local",
  "fingerprint": "a1c13612ff348aa51e6410bfd791de93669c73efa90414199b1bd9bb399e9306"
}
```

---

### Layer 2: OTP Email Authentication

**Step 1: Request OTP**
```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"target_meter": "SM-REAL-051"}' \
     https://localhost:8443/api/meter/otp
```

**Expected Output:**
```json
{
  "status": "pending",
  "message": "OTP sent to sarah@gridco.local",
  "expires_in_seconds": 300
}
```

**Step 2: Check Email**
- Look for OTP code sent to `sarah@gridco.local`
- Code format: `123456` (6 digits)
- Expires in: 5 minutes

**Step 3: Verify OTP**
```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"otp": "123456"}' \
     https://localhost:8443/api/meter/otp/verify
```

**Expected Output:**
```json
{
  "status": "verified",
  "message": "Authentication successful",
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-04-15T07:30:00Z"
}
```

---

## 📋 Architecture Overview

```
Client (with mTLS cert)
    ↓
mTLS Proxy (Port 8443) - Extracts cert
    ↓
Backend API (Port 8000) - Validates auth
    ↓
Database - Checks authorized_certs & users
    ↓
Protected Resources
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `start_services.sh` | One-command startup |
| `backend/main.py` | FastAPI application |
| `backend/mtls_proxy.py` | mTLS terminating proxy |
| `backend/auth.py` | Certificate validation |
| `backend/models/security.py` | Database models |
| `backend/setup_database.py` | Database seeding |
| `SETUP.md` | Detailed documentation |

---

## 🔍 Monitoring & Debugging

### Live Logs
```bash
# Backend logs
tail -f /tmp/backend.log

# Proxy logs (in another terminal)
tail -f /tmp/proxy.log
```

### Database Queries
```bash
# All authentication attempts
psql $DATABASE_URL -c "SELECT event_type, severity, client_ip, created_at FROM security_logs LIMIT 10;"

# Authorized certificates
psql $DATABASE_URL -c "SELECT fingerprint_sha256, common_name FROM authorized_certs;"

# OTP challenges
psql $DATABASE_URL -c "SELECT session_id, user_id, used, expires_at FROM otp_challenges;"
```

### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/health

# Root endpoint
curl http://localhost:8000/
```

---

## ❌ Troubleshooting

### "Port already in use"
```bash
lsof -ti:8000,8443 | xargs kill -9
./start_services.sh
```

### "Certificate not authorised"
Check database has your cert:
```bash
openssl x509 -in certs/client.crt -noout -fingerprint -sha256
psql $DATABASE_URL -c "SELECT fingerprint_sha256 FROM authorized_certs;"
```

### "OTP not sent/received"
Check email config in `.env`:
```bash
grep SMTP .env
grep DATABASE_URL .env
```

### "Database connection refused"
```bash
# Verify connection string
cat .env | grep DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

---

## 🎯 Testing Scenarios

### Attack Scenario 1: Wrong Certificate
```bash
curl --cert certs/attacker.crt \
     --key certs/attacker.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
# Expected: 403 Forbidden
```

### Attack Scenario 2: Brute Force OTP
```bash
for i in {1..5}; do
  curl --cert certs/client.crt \
       --key certs/client.key \
       --cacert certs/ca.crt \
       -H "Content-Type: application/json" \
       -d '{"otp": "000000"}' \
       https://localhost:8443/api/meter/otp/verify
  sleep 1
done
# After 3 attempts: IP is isolated
```

### Attack Scenario 3: Expired OTP
```bash
# Request OTP
curl ... https://localhost:8443/api/meter/otp

# Wait 6+ minutes

# Try expired OTP (should fail)
curl ... https://localhost:8443/api/meter/otp/verify -d '{"otp": "123456"}'
# Expected: 403 Forbidden (OTP expired)
```

---

## 📞 API Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/` | None | Health check |
| GET | `/api/health` | None | API health |
| GET | `/api/meter/voltage` | mTLS | Get meter voltage |
| POST | `/api/meter/otp` | mTLS | Request OTP |
| POST | `/api/meter/otp/verify` | mTLS | Verify OTP |

---

## 🔐 Security Features

✅ **Layer 1: mTLS**
- Client certificate validation
- CA-signed certificate verification
- Fingerprint-based authorization
- Per-user certificate management

✅ **Layer 2: OTP**
- 6-digit one-time passwords
- 5-minute expiry
- Email-based delivery
- Brute-force protection (3 attempts = IP block)

✅ **Logging**
- All auth attempts logged
- Success/failure tracking
- Attack detection
- IP-based rate limiting

---

## 📚 For More Details

See **SETUP.md** for comprehensive documentation including:
- Complete architecture diagrams
- Database schema explanations
- Advanced configuration
- Production deployment guide

---

**Last Updated**: 2026-04-15
**Status**: ✅ Layer 1 & 2 Operational
