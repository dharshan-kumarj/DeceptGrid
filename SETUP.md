# DeceptGrid Backend Setup & Testing Guide

## Overview

DeceptGrid implements a **2-layer security authentication system** for smart grid protection:
- **Layer 1**: Mutual TLS (mTLS) Certificate Authentication
- **Layer 2**: One-Time Password (OTP) via Email Authentication

---

## Layer 1: Mutual TLS (mTLS) Certificate Authentication

### What It Does
Clients must present a valid SSL client certificate that:
1. Is signed by the custom CA
2. Has its fingerprint registered in the `authorized_certs` database
3. Is associated with an active user account

### Prerequisites

**1. Certificates** (already generated in `certs/` directory)
```
certs/
├── ca.crt           # Certificate Authority
├── ca.key           # CA Private Key
├── server.crt       # Server Certificate
├── server.key       # Server Private Key
├── client.crt       # Client Certificate (for testing)
├── client.key       # Client Private Key
└── attacker.crt     # Attacker Certificate (for testing attacks)
```

**2. Database Seeded**
```bash
cd backend
python setup_database.py
```

Expected output:
```
⏳ Creating tables in Render...
⏳ Seeding Sarah...
  (User sarah already exists)
  (Cert already exists)
✅ Database is ready!
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Client (curl with --cert/--key)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ TLS with client cert
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  mTLS Proxy (mtls_proxy.py) - Port 8443                     │
│  • Accepts mTLS connections                                 │
│  • Extracts client certificate                              │
│  • Forwards as X-Client-Cert header                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP with X-Client-Cert header
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI) - Port 8000                              │
│  • Validates cert against authorized_certs table           │
│  • Checks user is active                                    │
│  • Returns protected data                                   │
└─────────────────────────────────────────────────────────────┘
```

### How to Start Layer 1

**Terminal 1 - Start Backend (Port 8000)**
```bash
cd /home/dharshan/projects/DeceptGrid/backend
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 - Start mTLS Proxy (Port 8443)**
```bash
cd /home/dharshan/projects/DeceptGrid/backend
source .venv/bin/activate
python mtls_proxy.py
```

Expected output:
```
🚀 Starting simple mTLS proxy...
✅ mTLS Proxy listening on https://0.0.0.0:8443
   Backend: http://127.0.0.1:8000
   Certs: /home/dharshan/projects/DeceptGrid/certs
```

### How to Test Layer 1

**Test 1: Valid Client Certificate (Should Succeed ✅)**

```bash
cd /home/dharshan/projects/DeceptGrid
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

Expected output:
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

Server log output (in Terminal 1):
```
[ASGI] GET /api/meter/voltage
[AUTH] ✓ Found cert in X-Client-Cert header
[AUTH] ✓ Successfully converted DER → PEM from ssl_object
INFO:     127.0.0.1:XXXXX - "GET /api/meter/voltage HTTP/1.1" 200 OK
```

**Test 2: Invalid Client Certificate (Should Fail ❌)**

```bash
curl --cert certs/attacker.crt \
     --key certs/attacker.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

Expected output:
```json
{
  "detail": "Certificate not authorised"
}
```

**Test 3: No Client Certificate (Should Fail ❌)**

```bash
curl --cacert certs/ca.crt https://localhost:8443/api/meter/voltage
```

Expected output:
```
curl: (35) error:14094410:SSL routines:ssl3_read_bytes:sslv3 alert handshake failure
```

### Database Tables for Layer 1

```sql
-- Users Table
SELECT id, username, email, is_active FROM users;

-- Authorized Certificates
SELECT fingerprint_sha256, common_name, revoked FROM authorized_certs;

-- Security Logs (all auth attempts)
SELECT event_type, severity, client_ip, user_id, created_at FROM security_logs;
```

---

## Layer 2: One-Time Password (OTP) Email Authentication

### What It Does
After passing Layer 1 (mTLS), clients need to:
1. Request an OTP be sent to their email
2. Receive 6-digit OTP with 5-minute expiry
3. Submit OTP to re-authenticate and access resources
4. Attempts are rate-limited per IP

### Prerequisites

**1. Email Configuration** (in `.env`)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=deceptgrid@yourdomain.com
OTP_EXPIRY_SECONDS=300
ISOLATION_THRESHOLD=3
```

**2. Test Email Account**
- Use Gmail with [App Password](https://support.google.com/accounts/answer/185833)
- Or use your company mail server

### Architecture

```
┌─────────────────────────────────────────────────┐
│  Client (authenticated with mTLS cert)          │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │  POST /api/meter/otp     │
        │  (Request OTP)           │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │  Generate 6-digit OTP    │
        │  Store hash in DB        │
        │  Send email              │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │ POST /api/meter/otp/verify
        │ (Submit OTP)             │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │ Hash provided OTP        │
        │ Compare with DB hash     │
        │ Return session token     │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │ Protected Resource       │
        │ /api/meter/current       │
        └──────────────────────────┘
```

### Database Tables for Layer 2

```sql
-- OTP Challenges (temp records)
SELECT session_id, user_id, target_meter, expires_at, used FROM otp_challenges;

-- Failed Attempts (rate limiting)
SELECT client_ip, attempt_count, last_attempt FROM failed_attempts;

-- Isolated Hosts (blocked IPs)
SELECT client_ip, reason, isolated_at, lifted_at FROM isolated_hosts;
```

### How to Test Layer 2

**Assuming Layer 1 succeeded with valid cert...**

**Step 1: Request OTP Email**

```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"target_meter": "SM-REAL-051"}' \
     https://localhost:8443/api/meter/otp
```

Expected output:
```json
{
  "status": "pending",
  "message": "OTP sent to sarah@gridco.local",
  "expires_in_seconds": 300
}
```

Email received at `sarah@gridco.local`:
```
Subject: DeceptGrid Security - One-Time Password

Your OTP is: 123456

This code expires in 5 minutes (300 seconds).
Do not share this code with anyone.

---
DeceptGrid Security System
```

**Step 2: Verify OTP**

```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"otp": "123456"}' \
     https://localhost:8443/api/meter/otp/verify
```

Expected output (success):
```json
{
  "status": "verified",
  "message": "Authentication successful",
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-04-15T07:30:00Z"
}
```

Expected output (failed - invalid OTP):
```json
{
  "status": "failed",
  "message": "Invalid OTP",
  "attempts_remaining": 2
}
```

**Step 3: Access Protected Resource with Session Token**

```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     https://localhost:8443/api/meter/current
```

Expected output:
```json
{
  "meter_id": "SM-REAL-051",
  "voltage": 220.5,
  "current": 45.3,
  "power_factor": 0.98,
  "timestamp": "2026-04-15T07:15:00Z"
}
```

---

## Attack Simulation

### Attack 1: Unauthorized Access (Wrong Certificate)

```bash
curl --cert certs/attacker.crt \
     --key certs/attacker.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

Result: `403 Forbidden` - Certificate not authorized

### Attack 2: Brute Force OTP (Rate Limiting)

```bash
# Try invalid OTP 4 times
for i in {1..4}; do
  curl --cert certs/client.crt \
       --key certs/client.key \
       --cacert certs/ca.crt \
       -H "Content-Type: application/json" \
       -d '{"otp": "000000"}' \
       https://localhost:8443/api/meter/otp/verify
done
```

After 3 failed attempts:
```json
{
  "detail": "Too many failed attempts. IP isolated."
}
```

IP is added to `isolated_hosts` table with 24-hour temporary block.

### Attack 3: Replay Attack (Expired OTP)

```bash
# Request OTP, wait 6+ minutes
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/otp

# ... wait 6 minutes ...

# Try to use expired OTP
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"otp": "123456"}' \
     https://localhost:8443/api/meter/otp/verify
```

Result: `403 Forbidden` - OTP expired

---

## Monitoring & Debugging

### View Security Logs

```bash
# All authentication attempts
psql $DATABASE_URL -c "SELECT event_type, severity, client_ip, user_id, created_at FROM security_logs ORDER BY created_at DESC LIMIT 20;"

# Failed attempts only
psql $DATABASE_URL -c "SELECT * FROM security_logs WHERE event_type = 'CERT_AUTH_FAILED' ORDER BY created_at DESC;"

# Rate limiting data
psql $DATABASE_URL -c "SELECT * FROM failed_attempts;"

# Isolated hosts
psql $DATABASE_URL -c "SELECT * FROM isolated_hosts WHERE lifted_at IS NULL;"
```

### Debug Endpoints

```bash
# Inspect request scope (development only)
curl https://localhost:8443/debug/scope

# Health check
curl http://localhost:8000/api/health

# Root endpoint
curl http://localhost:8000/
```

---

## Common Issues & Solutions

### Issue: "Port 8443 already in use"

```bash
# Kill existing proxy/server
lsof -ti:8443 | xargs kill -9

# Or use different port
python mtls_proxy.py --port 8444
```

### Issue: "Certificate not authorised"

Check if certificate fingerprint is in database:
```bash
openssl x509 -in certs/client.crt -noout -fingerprint -sha256

psql $DATABASE_URL -c "SELECT fingerprint_sha256 FROM authorized_certs;"
```

The fingerprints must match (after removing colons).

### Issue: "OTP not received"

1. Check `.env` has correct SMTP credentials
2. Verify email isn't in spam folder
3. Check backend logs:
   ```bash
   tail -100 /tmp/backend.log | grep -i email
   ```

### Issue: "Database connection refused"

```bash
# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

---

## Complete Startup Script

**Create `start_all.sh`:**

```bash
#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd /home/dharshan/projects/DeceptGrid

echo -e "${BLUE}🚀 Starting DeceptGrid Stack...${NC}\n"

# Start Backend
echo -e "${BLUE}1️⃣  Starting Backend API (Port 8000)...${NC}"
(cd backend && source .venv/bin/activate && uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1) &
BACKEND_PID=$!
sleep 2

# Start mTLS Proxy
echo -e "${BLUE}2️⃣  Starting mTLS Proxy (Port 8443)...${NC}"
(cd backend && source .venv/bin/activate && python mtls_proxy.py > /tmp/proxy.log 2>&1) &
PROXY_PID=$!
sleep 2

# Verify services
echo -e "\n${GREEN}✅ Service Status:${NC}"
curl -s http://localhost:8000/api/health | grep -q "healthy" && echo "   Backend: ✅ Running" || echo "   Backend: ❌ Failed"
sleep 1 && echo "   Proxy: ✅ Running (listening on 8443)"

echo -e "\n${GREEN}📝 Test Commands:${NC}"
echo "   Layer 1 (mTLS):"
echo "   curl --cert certs/client.crt --key certs/client.key --cacert certs/ca.crt https://localhost:8443/api/meter/voltage"
echo ""
echo "   Cleanup:"
echo "   kill $BACKEND_PID $PROXY_PID"
```

**Make it executable:**
```bash
chmod +x start_all.sh
./start_all.sh
```

---

## Next Steps

1. ✅ Layer 1 (mTLS) - Complete
2. ✅ Layer 2 (OTP Email) - Ready to test
3. **Layer 3** (Advanced): Steganography attacks
4. **Layer 4** (Advanced): Attack logging & response

---

## Additional Resources

- **mTLS Proxy**: `backend/mtls_proxy.py`
- **Authentication**: `backend/auth.py`
- **Database Models**: `backend/models/security.py`
- **Email Service**: `backend/email_service.py`
- **Setup Script**: `backend/setup_database.py`

---

**Last Updated**: 2026-04-15
**DeceptGrid Version**: 1.0.0
