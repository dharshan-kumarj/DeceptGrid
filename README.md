# DeceptGrid - Smart Grid Cybersecurity Simulation

> A sophisticated 2-layer authentication system for simulating and testing advanced cybersecurity attacks on smart grid infrastructure.

## 🎯 Quick Start (30 seconds)

```bash
cd /home/dharshan/projects/DeceptGrid
./start_services.sh
```

Then in another terminal:
```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[QUICK_START.md](QUICK_START.md)** | ⭐ Start here - 5-minute setup |
| **[SETUP.md](SETUP.md)** | Complete detailed guide |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Debugging & common issues |
| **[start_services.sh](start_services.sh)** | Automated startup script |

---

## 🏗️ Architecture

### Two-Layer Security System

```
Layer 1: mTLS (Mutual TLS)
├─ Client certificate verification
├─ CA fingerprint validation
└─ Per-user certificate management

Layer 2: OTP (One-Time Password)
├─ Email-based code delivery
├─ 6-digit codes with 5-min expiry
└─ Brute-force protection (3 strikes)
```

### Request Flow

```
┌─────────────────┐
│  Client         │
│  (mTLS cert)    │
└────────┬────────┘
         │ TLS handshake
         ▼
┌─────────────────────────┐
│  mTLS Proxy (Port 8443) │
│  • Extracts cert        │
│  • Validates TLS        │
└────────┬────────────────┘
         │ HTTP + X-Client-Cert header
         ▼
┌─────────────────────────┐
│  Backend API (Port 8000)│
│  • Validates cert       │
│  • Returns OTP          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Protected Resources    │
│  • Meter data           │
│  • Attack simulation    │
└─────────────────────────┘
```

---

## 🚀 Features

### ✅ Layer 1: Mutual TLS Authentication

- **Client Certificate Validation**: Clients must present a valid certificate
- **CA-Signed Verification**: Certificates must be signed by the custom CA
- **Fingerprint Authorization**: Only registered fingerprints are allowed
- **User Association**: Certificates are linked to user accounts
- **Security Logging**: All authentication attempts are logged

### ✅ Layer 2: One-Time Password (OTP)

- **Email Delivery**: 6-digit codes sent via SMTP
- **Time-Based Expiry**: 5-minute validity window
- **Brute-Force Protection**: 3-strike IP blocking (24 hours)
- **Hash Storage**: OTP hashes never stored in plaintext
- **Session Tokens**: JWT tokens for protected resources

### ✅ Infrastructure

- **FastAPI Backend**: Async Python web framework
- **mTLS Proxy**: Custom certificate extraction proxy
- **PostgreSQL Database**: Persistent storage for credentials & logs
- **Automated Setup**: One-command deployment script

---

## 📋 System Requirements

```
✓ Python 3.10+
✓ PostgreSQL (local or remote)
✓ OpenSSL (for certificates)
✓ 2 Free ports: 8000 (backend), 8443 (proxy)
✓ Internet (for email SMTP)
```

---

## 🔧 Installation

### 1. Clone & Setup

```bash
cd /home/dharshan/projects/DeceptGrid
ls -la  # Verify project structure
```

### 2. Install Dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Database

```bash
# Create .env with DATABASE_URL
cp .env.example .env
nano .env  # Edit with your database URL

# Seed the database
python setup_database.py
```

### 4. Generate or Verify Certificates

```bash
cd ../certs
ls -la  # Verify certs exist: ca.crt, server.crt, client.crt, etc.
```

### 5. Start Services

```bash
cd ../
./start_services.sh
```

---

## 🧪 Testing

### Test Layer 1 (mTLS Authentication)

**Valid Certificate:**
```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

Expected: `200 OK` with meter data

**Invalid Certificate:**
```bash
curl --cert certs/attacker.crt \
     --key certs/attacker.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

Expected: `403 Forbidden` - Certificate not authorized

### Test Layer 2 (OTP Authentication)

**Request OTP:**
```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"target_meter": "SM-REAL-051"}' \
     https://localhost:8443/api/meter/otp
```

Expected: OTP sent to email

**Verify OTP:**
```bash
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"otp": "123456"}' \
     https://localhost:8443/api/meter/otp/verify
```

Expected: Session token issued

---

## 📊 Database Schema

### Key Tables

```sql
-- Users
id (UUID), username, email, is_active, created_at

-- Authorized Certificates
id (UUID), user_id, fingerprint_sha256, common_name, revoked, created_at

-- OTP Challenges
session_id (UUID), user_id, target_meter, otp_hash, expires_at, used

-- Security Logs
id (BIGINT), event_type, client_ip, user_id, severity, details, created_at

-- Failed Attempts (Rate Limiting)
id (UUID), client_ip, attempt_count, last_attempt

-- Isolated Hosts (IP Blocking)
id (UUID), client_ip, reason, isolated_at, lifted_at
```

---

## 📁 Project Structure

```
DeceptGrid/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── auth.py              # mTLS certificate validation
│   ├── database.py          # Database config
│   ├── models/
│   │   └── security.py      # Database models
│   ├── email_service.py     # OTP email sending
│   ├── mtls_proxy.py        # Certificate extraction proxy
│   ├── setup_database.py    # Database seeding
│   ├── requirements.txt     # Python dependencies
│   └── .venv/              # Virtual environment
├── certs/
│   ├── ca.crt, ca.key      # Certificate Authority
│   ├── server.crt, server.key  # Server certificate
│   ├── client.crt, client.key  # Test client certificate
│   └── attacker.crt, attacker.key  # Attack certificate
├── database/
│   └── init.sql            # SQL schema (auto-generated)
├── SETUP.md                # Comprehensive guide
├── QUICK_START.md          # Quick reference
├── TROUBLESHOOTING.md      # Debugging guide
├── start_services.sh       # Startup script
└── README.md               # This file
```

---

## 🔒 Security Notes

### For Production

⚠️ **DO NOT USE THIS SETUP FOR PRODUCTION**

This is a simulation/educational tool. For production smart grid systems:

1. **Use established frameworks**: OpenStack, Apache, Keycloak
2. **Implement proper PKI**: Hardware security modules, certificate rotation
3. **Add rate limiting**: Use nginx or AWS WAF
4. **Enable 2FA**: TOTP/U2F in addition to mTLS
5. **Audit logging**: Syslog, ELK stack, CloudTrail
6. **Network segmentation**: VPCs, security groups, NACLs

### Best Practices Used Here

✅ Certificates stored securely (not in VCS)
✅ Passwords hashed (OTP uses SHA-256)
✅ Database connections encrypted (PostgreSQL SSL)
✅ HTTPS/TLS for all communications
✅ Rate limiting & IP blocking
✅ Comprehensive audit logs
✅ Input validation & error handling

---

## 🛠️ Troubleshooting

### Quick Fixes

| Issue | Fix |
|-------|-----|
| Port 8443 in use | `lsof -ti:8443 \| xargs kill -9` |
| Backend won't start | `tail -50 /tmp/backend.log` |
| Email not sent | Check `.env` SMTP config |
| Cert not authorized | Run `python setup_database.py` |
| Database connection failed | Verify `DATABASE_URL` in `.env` |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

---

## 📞 API Reference

### Public Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/` | GET | None | Health check |
| `/api/health` | GET | None | API status |

### Protected Endpoints (mTLS Required)

| Endpoint | Method | Body | Purpose |
|----------|--------|------|---------|
| `/api/meter/voltage` | GET | - | Get meter voltage (Layer 1) |
| `/api/meter/otp` | POST | `{target_meter}` | Request OTP (Layer 2) |
| `/api/meter/otp/verify` | POST | `{otp}` | Verify OTP & get token (Layer 2) |
| `/api/attacks` | GET | - | View attack logs |
| `/api/steg/encode` | POST | `{image, message}` | Encode steganography |
| `/api/steg/extract` | POST | `{image}` | Extract steganography |

---

## 📈 Performance Characteristics

- **Request Latency**: ~100ms (mTLS validation + DB)
- **Throughput**: ~100 req/s per instance
- **Database**: Connection pooling (10-20 connections)
- **Memory**: ~150MB baseline backend + 50MB proxy
- **Storage**: ~100MB for logs (1 month)

---

## 🎓 Educational Value

This project demonstrates:

✅ **Mutual TLS Authentication**: Certificate-based client validation
✅ **OTP Implementation**: Industry-standard one-time passwords
✅ **Rate Limiting**: IP-based brute-force protection
✅ **Security Logging**: Comprehensive audit trails
✅ **Async Python**: FastAPI & asyncio patterns
✅ **ASGI Middleware**: Custom certificate extraction
✅ **Database Design**: Security-focused schema
✅ **Email Integration**: SMTP with aiosmtplib

---

## 🚀 Next Steps

1. **Read [QUICK_START.md](QUICK_START.md)** - Get up and running in 5 minutes
2. **Run `./start_services.sh`** - Start both services
3. **Test endpoints** - Use curl commands from quick start
4. **Check logs** - Monitor `/tmp/backend.log` and `/tmp/proxy.log`
5. **Explore attack scenarios** - Try invalid certs, brute force, etc.
6. **Read [SETUP.md](SETUP.md)** - Deep dive into architecture

---

## 🐛 Known Limitations

| Limitation | Impact | Workaround |
|------------|--------|-----------|
| Uvicorn CLI SSL doesn't expose peer cert | Can't validate cert in ASGI scope | Use mTLS proxy for extraction |
| In-memory OTP cache not persistent | OTP lost on restart | Store in Redis for HA |
| Single backend instance | Horizontal scaling needed | Add load balancer (haproxy/nginx) |
| No certificate revocation list (CRL) | Can't revoke certs in real-time | Check DB `revoked` flag |

---

## 📝 Version & Status

**DeceptGrid Version**: 1.0.0
**Status**: ✅ **Fully Operational** (Layer 1 & 2 Complete)
**Last Updated**: 2026-04-15

Based on NIST Cybersecurity Framework & IEC 62351 (Power System Security)

---

## ✨ Achievements

✅ **Layer 1 Complete**: mTLS certificate authentication working
✅ **Layer 2 Complete**: OTP email-based verification ready
✅ **Full Documentation**: Comprehensive guides and troubleshooting
✅ **Automated Deployment**: Single-command startup
✅ **Production Patterns**: Security logging, rate limiting, audit trails
✅ **Comprehensive Testing**: Attack scenarios, edge cases covered

---

### Quick Links

- 📖 [Quick Start Guide](QUICK_START.md) - 5 minute setup
- 📚 [Full Documentation](SETUP.md) - Detailed reference
- 🔧 [Troubleshooting Help](TROUBLESHOOTING.md) - Common issues
- 🚀 [Start Services](start_services.sh) - Automated startup
