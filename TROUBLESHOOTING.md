# DeceptGrid Troubleshooting Guide

## Layer 1: mTLS Certificate Issues

### Problem: "Certificate not authorised"

**Error:**
```json
{"detail":"Certificate not authorised"}
```

**Cause:** Certificate fingerprint not in database

**Solution:**
```bash
# 1. Get your certificate's fingerprint
openssl x509 -in certs/client.crt -noout -fingerprint -sha256

# Output: sha256 Fingerprint=A1:C1:36:12:FF:34:8A:A5:...

# 2. Check what's in the database
psql $DATABASE_URL -c "SELECT fingerprint_sha256, common_name, revoked FROM authorized_certs;"

# 3. If missing, add it (contact admin or update database)
psql $DATABASE_URL -c "
INSERT INTO authorized_certs (user_id, fingerprint_sha256, common_name)
SELECT id, 'a1c13612ff348aa51e6410bfd791de93669c73efa90414199b1bd9bb399e9306', 'sarah@gridco.local'
FROM users WHERE username = 'sarah';
"

# 4. Verify it was added
psql $DATABASE_URL -c "SELECT * FROM authorized_certs;"
```

---

### Problem: "Client certificate required"

**Error:**
```json
{"detail":"Client certificate required"}
```

**Cause:** Curl not sending client certificate OR proxy not running

**Solution:**

**Option 1: Verify client certificate files exist**
```bash
ls -la certs/
# Should show:
# client.crt  (contains public cert)
# client.key  (contains private key)
```

**Option 2: Check proxy is running**
```bash
ps aux | grep mtls_proxy
# Should output: python mtls_proxy.py

# If not running, start it:
cd backend && source .venv/bin/activate && python mtls_proxy.py
```

**Option 3: Verify curl syntax**
```bash
# ❌ WRONG - missing key
curl --cert certs/client.crt --cacert certs/ca.crt https://localhost:8443/api/meter/voltage

# ✅ CORRECT - has both cert and key
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

**Option 4: Check certificate is valid**
```bash
# Verify cert wasn't revoked
openssl x509 -in certs/client.crt -noout -dates
# notBefore=... notAfter=...

# Verify cert is signed by CA
openssl verify -CAfile certs/ca.crt certs/client.crt
# Should output: certs/client.crt: OK
```

---

### Problem: "SSL: CERTIFICATE_VERIFY_FAILED"

**Error:**
```
curl: (60) SSL certificate problem: self signed certificate
```

**Cause:** curl doesn't trust the CA certificate

**Solution:**
```bash
# Make sure you're using --cacert with the CA, not the server cert
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
```

---

### Problem: "Port 8443 already in use"

**Error:**
```
OSError: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8443)
```

**Cause:** Another process already using port 8443

**Solution:**
```bash
# Find and kill the process
lsof -ti:8443 | xargs kill -9

# Or use a different port
python mtls_proxy.py --port 8444

# Update curl to use new port
curl ... https://localhost:8444/api/meter/voltage
```

---

## Layer 2: OTP Email Issues

### Problem: "OTP not sent / Email not received"

**Symptoms:**
- Request to `/api/meter/otp` succeeds
- But no email arrives
- Check logs show no errors

**Solution:**

**1. Verify SMTP Configuration**
```bash
# Check .env has correct email config
grep -E "SMTP|EMAIL" ~/.env

# Should show:
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASS=your-app-password
# SMTP_FROM=deceptgrid@yourdomain.com
```

**2. Verify Backend Logs**
```bash
# Check for email sending errors
tail -100 /tmp/backend.log | grep -E "email|mail|smtp|Email|Mail|SMTP"

# Common errors:
# - "SMTPAuthenticationError" → wrong password
# - "SMTPNotSupportedError" → wrong port
# - "Connection refused" → wrong host
```

**3. Test SMTP Connection Manually**
```python
# backend/test_smtp.py
import asyncio
import aiosmtplib
from email.mime.text import MIMEText

async def test():
    async with aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587) as smtp:
        await smtp.login("your-email@gmail.com", "your-app-password")
        message = MIMEText("Test OTP: 123456")
        message["Subject"] = "DeceptGrid Test"
        message["From"] = "deceptgrid@yourdomain.com"
        message["To"] = "your-email@gmail.com"
        await smtp.send_message(message)
        print("✅ Email sent successfully!")

asyncio.run(test())
```

**4. For Gmail Users**
- Use an [App Password](https://support.google.com/accounts/answer/185833), NOT your regular password
- Enable [Less Secure App Access](https://myaccount.google.com/lesssecureapps) if available
- Check 2-Factor Authentication is enabled

**5. Check Recipient Email**
```bash
# Verify recipient is correct
psql $DATABASE_URL -c "SELECT email FROM users WHERE username='sarah';"

# Also check if there's an OTP record in DB
psql $DATABASE_URL -c "SELECT session_id, user_id, expires_at FROM otp_challenges ORDER BY created_at DESC LIMIT 5;"
```

---

### Problem: "Invalid OTP" / "OTP verification failed"

**Error:**
```json
{"detail":"Invalid OTP"}
```

**Cause:** OTP doesn't match or is expired

**Solution:**

**1. Check OTP has not expired**
```bash
# OTPs expire after 300 seconds (5 minutes)
# Request a new one:
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     -H "Content-Type: application/json" \
     -d '{"target_meter": "SM-REAL-051"}' \
     https://localhost:8443/api/meter/otp
```

**2. Verify OTP format**
```bash
# OTP must be exactly 6 digits
# ❌ WRONG:
curl ... -d '{"otp": "12345"}'      # Only 5 digits
curl ... -d '{"otp": "1234567"}'    # 7 digits
curl ... -d '{"otp": "123456abcd"}' # Contains letters

# ✅ CORRECT:
curl ... -d '{"otp": "123456"}' # Exactly 6 digits
```

**3. Copy OTP Carefully**
- Check email for OTP code
- Copy exactly (no spaces, exact digits)
- Paste immediately (don't wait 5+ minutes)

**4. Database Verification**
```bash
# Check if OTP exists and hasn't been used
psql $DATABASE_URL -c "SELECT session_id, user_id, used, expires_at FROM otp_challenges ORDER BY created_at DESC LIMIT 1;"

# If used=true, request a new OTP
```

---

### Problem: "Too many failed attempts. IP isolated."

**Error:**
```json
{"detail":"Too many failed attempts. IP isolated."}
```

**Cause:** 3+ failed OTP attempts from same IP

**Details:**
- Failed attempt counter: 3 attempts max
- Isolation period: 24 hours
- Affects: Current IP address

**Solution:**

**Option 1: Wait 24 hours** (automatic unblock)

**Option 2: Admin unblock**
```bash
# Check isolated IPs
psql $DATABASE_URL -c "SELECT client_ip, reason, isolated_at, lifted_at FROM isolated_hosts WHERE lifted_at IS NULL;"

# Unblock IP
psql $DATABASE_URL -c "UPDATE isolated_hosts SET lifted_at=NOW() WHERE client_ip='127.0.0.1';"
```

**Option 3: Use different IP** (for testing)
```bash
# Test from different machine/VPN if available
ssh user@other-machine "curl ... https://localhost:8443/api/meter/otp"
```

---

### Problem: "Associated user account is disabled"

**Error:**
```json
{"detail":"Associated user account is disabled"}
```

**Cause:** User's `is_active` flag is false in database

**Solution:**
```bash
# Check user status
psql $DATABASE_URL -c "SELECT username, email, is_active FROM users WHERE username='sarah';"

# Re-enable user
psql $DATABASE_URL -c "UPDATE users SET is_active=true WHERE username='sarah';"

# Verify
psql $DATABASE_URL -c "SELECT * FROM users WHERE username='sarah';"
```

---

## Network & Connection Issues

### Problem: "Connection refused" / "Port 8000 not responding"

**Error:**
```
curl: (7) Failed to connect to localhost port 8000
```

**Solution:**
```bash
# Check backend is running
ps aux | grep uvicorn | grep main:app

# If not running, start it:
cd backend && source .venv/bin/activate && uvicorn main:app --host 127.0.0.1 --port 8000

# Verify it responds
curl http://localhost:8000/api/health

# Check logs
tail -50 /tmp/backend.log
```

---

### Problem: "Connection reset by peer"

**Error:**
```
curl: (56) Failure in receiving network data
```

**Cause:** Backend crashed or connection dropped

**Solution:**
```bash
# Check if backend is still running
ps aux | grep uvicorn

# If dead, check error logs
tail -100 /tmp/backend.log

# Look for Python errors

# Restart if needed
pkill -f "uvicorn main:app"
sleep 2
cd backend && source .venv/bin/activate && uvicorn main:app --host 127.0.0.1 --port 8000
```

---

## Database Issues

### Problem: "Database connection refused"

**Error:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server:
Connection refused
```

**Solution:**
```bash
# 1. Verify DATABASE_URL is set
cat .env | grep DATABASE_URL

# 2. Test connection
psql $DATABASE_URL -c "SELECT 1;"

# 3. If fails, check:
# - Hostname is correct
# - Port is correct (default 5432)
# - Username/password correct
# - Database exists
# - Network can reach server (ping hostname)

# 4. For Render PostgreSQL:
# Get connection string from Render dashboard
# Update .env
export DATABASE_URL="postgresql+asyncpg://..."
```

---

### Problem: "Table does not exist"

**Error:**
```
ProgrammingError: (psycopg2.errors.UndefinedTable) relation "users" does not exist
```

**Solution:**
```bash
# Run database setup
cd backend
python setup_database.py

# Or manually:
psql $DATABASE_URL -c "
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username TEXT UNIQUE,
  email TEXT UNIQUE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);
"

# Run full migration
python setup_database.py
```

---

## Performance Issues

### Slow Response Times

**Check:**
```bash
# 1. Database response time
time psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"

# 2. Network latency
ping $(hostname -I | awk '{print $1}')

# 3. CPU/Memory usage
top -b -n 1 | head -20
```

**Solutions:**
- Add database indexes (indexes already in models)
- Reduce log verbosity
- Check for slow queries in logs

---

## Verification Checklist

Before reporting issues, verify:

- [ ] `start_services.sh` completed without errors
- [ ] Backend shows "Application startup complete"
- [ ] Proxy shows "Proxy listening on https://0.0.0.0:8443"
- [ ] `curl http://localhost:8000/api/health` returns 200
- [ ] `.env` file exists with DATABASE_URL
- [ ] Certificate files exist in `certs/`
- [ ] `psql $DATABASE_URL -c "SELECT 1;" ` returns success
- [ ] No other process on ports 8000 or 8443
- [ ] Sufficient disk space
- [ ] Network connectivity

---

## Getting Help

If issue persists:

1. **Collect logs:**
   ```bash
   tail -200 /tmp/backend.log > /tmp/debug_backend.log
   tail -200 /tmp/proxy.log > /tmp/debug_proxy.log
   ```

2. **Collect system info:**
   ```bash
   uname -a > /tmp/debug_system.log
   python3 --version >> /tmp/debug_system.log
   pip list >> /tmp/debug_system.log
   ```

3. **Share:**
   - All debug logs
   - Your `.env` file (with sensitive values removed)
   - Full error message
   - Steps to reproduce

---

**Last Updated**: 2026-04-15
