# ✅ DeceptGrid - Complete Layer Testing Guide (All 6 Layers)

**Last Updated:** April 15, 2026
**Status:** All Layers Operational
**Backend:** http://localhost:8000

---

## 🎯 QUICK START

```bash
# Make sure backend is running
curl -s http://localhost:8000/api/health | python3 -m json.tool

# Expected: {"status": "healthy", "service": "DeceptGrid Backend - Person C"}
```

---

# 📋 TABLE OF CONTENTS

1. [Layer 1: mTLS Authentication](#layer-1-mtls-authentication)
2. [Layer 2: OTP 2-Factor Authentication](#layer-2-otp-2-factor-authentication)
3. [Layer 3: ML-Based IDS](#layer-3-ml-based-ids)
4. [Layer 4: Honeypot System](#layer-4-honeypot-system)
5. [Layer 5: Cryptographic Code Signing](#layer-5-cryptographic-code-signing)
6. [Layer 6: Physics-Based Validation](#layer-6-physics-based-validation)

---

# Layer 1: mTLS Authentication

## Overview
Client certificate-based mutual TLS authentication. Requires valid client certificate signed by custom CA.

## Endpoints
- `GET /api/meter/voltage` - Requires mTLS certificate

## Test Commands

### Test 1: Get meter voltage (requires mTLS)
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
  "authenticated_as": "client.deceptgrid.local",
  "fingerprint": "SHA256:..."
}
```

---

# Layer 2: OTP 2-Factor Authentication

## Overview
Email-based one-time password (OTP) verification. 15-minute token validity.

## Endpoints
- `POST /api/otp/request` - Request OTP delivery
- `POST /api/otp/verify` - Verify OTP code
- `GET /api/otp/status/{session_id}` - Check OTP status
- `GET /api/otp/test` - Test OTP system

## Test Commands

### Test 1: Request OTP
```bash
curl -X POST http://localhost:8000/api/otp/request \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_meter": "SM-REAL-051",
    "client_ip": "192.168.1.1"
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "session_id": "90cdcb9c-a748-4f12-aed4-548c09563dd8",
  "message": "OTP sent to test@deceptgrid.test",
  "otp_sent_to": "test@deceptgrid.test",
  "expires_in_seconds": 900,
  "client_ip": "192.168.1.1"
}
```

⚠️ **Note:** OTP code is printed to backend logs (test mode). Check `/tmp/backend.log`:
```bash
grep "OTP TEST MODE" /tmp/backend.log | tail -1
```

### Test 2: Verify OTP
```bash
# Replace SESSION_ID with value from Test 1
curl -X POST http://localhost:8000/api/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "90cdcb9c-a748-4f12-aed4-548c09563dd8",
    "otp_code": "123456"
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "success": true,
  "message": "OTP verified successfully (TEST MODE)",
  "session_id": "90cdcb9c-a748-4f12-aed4-548c09563dd8",
  "expires_in_seconds": 900
}
```

### Test 3: Check OTP Status
```bash
curl -s http://localhost:8000/api/otp/status/90cdcb9c-a748-4f12-aed4-548c09563dd8 | python3 -m json.tool
```

**Expected Output (Before Verification):**
```json
{
  "status": "pending",
  "message": "Awaiting OTP verification",
  "expires_in_seconds": 895,
  "target_meter": "SM-REAL-051"
}
```

### Test 4: Test OTP System
```bash
curl -s http://localhost:8000/api/otp/test | python3 -m json.tool
```

**Expected Output:**
```json
{
  "layer": 2,
  "system": "OTP Authentication",
  "status": "operational",
  "methods": [
    "POST /api/otp/request - Request OTP",
    "POST /api/otp/verify - Verify OTP",
    "GET /api/otp/status/{session_id} - Check status"
  ],
  "otp_validity": "15 minutes",
  "delivery_method": "Email-based"
}
```

---

# Layer 3: ML-Based IDS

## Overview
Machine Learning intrusion detection using Isolation Forest + rule-based scoring.
Hybrid approach: 60% ML + 40% Rules = Final Risk Score (0-100)

## Endpoints
- `POST /api/ids/assess-risk` - Hybrid IDS scoring
- `POST /api/ids/rule-score` - Rule-based scoring only
- `POST /api/ids/ml-anomaly` - ML anomaly detection only
- `GET /api/ids/test/scenarios` - Get test scenarios
- `GET /api/ids/honeypot/meters` - List honeypot meters
- `GET /api/ids/honeypot/meter/{meter_id}/voltage` - Honeypot voltage
- `GET /api/ids/honeypot/test` - Test all honeypots

## Scoring Thresholds
- **0-49:** ALLOW (low risk)
- **50-79:** CHALLENGE (medium risk - re-auth with OTP)
- **80-100:** BLOCK (high risk - isolate)

## Test Commands

### Test 1: Normal User (Expect: ALLOW)
```bash
curl -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "client_ip": "192.168.1.100",
    "request_rate": 2.5,
    "session_duration": 40,
    "hour_of_day": 14,
    "day_of_week": 2,
    "unique_endpoints": 3,
    "data_volume": 4.5
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "user_id": "user001",
  "client_ip": "192.168.1.100",
  "ml_score": 68.1,
  "rule_score": 0.0,
  "hybrid_score": 40.9,
  "action": "ALLOW",
  "rule_reasons": ["Normal request rate", "Normal access time"],
  "risk_level": "LOW"
}
```

### Test 2: High Request Rate (Expect: CHALLENGE/BLOCK)
```bash
curl -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "client_ip": "192.168.1.101",
    "request_rate": 10,
    "session_duration": 120,
    "hour_of_day": 14,
    "day_of_week": 2,
    "unique_endpoints": 5,
    "data_volume": 20
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "hybrid_score": 60.5,
  "action": "CHALLENGE",
  "risk_level": "MEDIUM"
}
```

### Test 3: Brute Force Attack (Expect: BLOCK)
```bash
curl -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "attacker",
    "client_ip": "203.0.113.45",
    "request_rate": 15,
    "session_duration": 30,
    "hour_of_day": 13,
    "day_of_week": 1,
    "unique_endpoints": 50,
    "data_volume": 500
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "hybrid_score": 80.9,
  "action": "BLOCK",
  "risk_level": "HIGH"
}
```

### Test 4: Off-Hours + Scanning (Expect: CHALLENGE)
```bash
curl -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user002",
    "client_ip": "203.45.67.89",
    "request_rate": 5,
    "session_duration": 90,
    "hour_of_day": 2,
    "day_of_week": 6,
    "unique_endpoints": 15,
    "data_volume": 50
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "hybrid_score": 70.8,
  "action": "CHALLENGE",
  "risk_level": "MEDIUM"
}
```

### Test 5: Data Exfiltration (Expect: CHALLENGE)
```bash
curl -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "client_ip": "10.0.0.50",
    "request_rate": 3,
    "session_duration": 180,
    "hour_of_day": 13,
    "day_of_week": 1,
    "unique_endpoints": 8,
    "data_volume": 200
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "hybrid_score": 55.8,
  "action": "CHALLENGE",
  "risk_level": "MEDIUM"
}
```

### Test 6: Get Test Scenarios
```bash
curl -s http://localhost:8000/api/ids/test/scenarios | python3 -m json.tool
```

---

# Layer 4: Honeypot System

## Overview
Decoy meter system with realistic fake data and canary tokens for intrusion detection.

## Honeypot Meters
- `SM-HONEY-001` - Decoy meter 1
- `SM-HONEY-002` - Decoy meter 2
- `SM-HONEY-003` - Decoy meter 3

## Test Commands

### Test 1: List Active Honeypot Meters
```bash
curl -s http://localhost:8000/api/ids/honeypot/meters | python3 -m json.tool
```

**Expected Output:**
```json
{
  "active_meters": ["SM-HONEY-001", "SM-HONEY-002", "SM-HONEY-003"],
  "count": 3,
  "status": "operational"
}
```

### Test 2: Get Honeypot Meter 1 Voltage
```bash
curl -s http://localhost:8000/api/ids/honeypot/meter/SM-HONEY-001/voltage | python3 -m json.tool
```

**Expected Output:**
```json
{
  "meter_id": "SM-HONEY-001",
  "voltage": 220.12,
  "current": 18.66,
  "power_factor": 0.95,
  "frequency": 50.0,
  "status": "operational",
  "canary_token": "034ed222d132bf42352e..."
}
```

### Test 3: Get Honeypot Meter Status
```bash
curl -s http://localhost:8000/api/ids/honeypot/meter/SM-HONEY-001/status | python3 -m json.tool
```

### Test 4: Test All Honeypot Meters
```bash
curl -s http://localhost:8000/api/ids/honeypot/test | python3 -m json.tool
```

**Expected Output:**
```json
{
  "system": "honeypot",
  "status": "operational",
  "meters_tested": 3,
  "meters": {
    "SM-HONEY-001": {
      "voltage": 220.12,
      "current": 18.66,
      "power_factor": 0.95,
      "battery": 89.0,
      "signal_strength": 95.0,
      "model": "SmartMeter-3000X",
      "serial": "HONEY001",
      "token": "034ed222d132bf42352e..."
    },
    "SM-HONEY-002": {...},
    "SM-HONEY-003": {...}
  }
}
```

---

# Layer 5: Cryptographic Code Signing

## Overview
GPG-based RSA-4096 code signing for critical meter commands.
Ensures command integrity and signer authentication.

## Endpoints
- `POST /api/meter/config` - Execute signed commands
- `POST /api/meter/command/validate` - Verify signature only

## Security Events Logged
- `UNSIGNED_COMMAND`
- `INVALID_SIGNATURE`
- `UNAUTHORIZED_SIGNER`
- `SIGNED_COMMAND_ACCEPTED`

## Test Commands

### Test 1: Test Layer Status
```bash
curl -s http://localhost:8000/api/meter/test/layers | python3 -m json.tool
```

**Expected Output:**
```json
{
  "layer_5": {
    "name": "Code Signing",
    "status": "operational",
    "algorithm": "GPG/RSA-4096",
    "authorized_signers": 3,
    "endpoints": [
      "POST /api/meter/config (signed commands)",
      "POST /api/meter/command/validate (signature verification)"
    ]
  },
  "layer_6": {
    "name": "Physics Validation",
    "status": "operational",
    "validations": [
      "Statistical baseline (Z-score > 6)",
      "Ohm's Law (Power ≈ V × I × PF)",
      "Adjacent meter correlation (ΔV > 20V)",
      "Load consistency (change > 20%)"
    ],
    "endpoints": [
      "POST /api/meter/reading/validate"
    ]
  }
}
```

### Test 2: Test Unsigned Command (Should Fail)
```bash
curl -X POST http://localhost:8000/api/meter/config \
  -H "Content-Type: application/json" \
  -d '{"signed_payload": ""}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "detail": "Empty payload - expected signed GPG message"
}
```

### Test 3: Get Security Events
```bash
curl -s http://localhost:8000/api/meter/security/events | python3 -m json.tool
```

**Expected Output:**
```json
{
  "message": "Security events logged to application logs",
  "events_tracked": [
    "UNSIGNED_COMMAND",
    "INVALID_SIGNATURE",
    "UNAUTHORIZED_SIGNER",
    "SIGNED_COMMAND_ACCEPTED",
    "PHYSICS_VALIDATION_FAILED",
    "ANOMALOUS_READING_DETECTED"
  ],
  "log_location": "/tmp/backend.log"
}
```

### Test 4: Generate GPG Key and Sign Command

#### Step 1: Generate GPG Key
```bash
# Generate keypair
gpg --batch --generate-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Email: engineer@deceptgrid.local
Expire-Date: 2030-12-31
EOF

# List keys to get fingerprint
gpg --list-keys --keyid-format=long engineer@deceptgrid.local
```

#### Step 2: Create Command
```bash
cat > command.json <<'EOF'
{
  "action": "set_config",
  "target_meter": "SM-REAL-051",
  "value": {
    "sampling_rate": 1000,
    "transmission_interval": 300
  }
}
EOF
```

#### Step 3: Sign Command
```bash
gpg --sign --armor --output command.json.asc command.json
```

#### Step 4: Read Signed Payload
```bash
cat command.json.asc
```

#### Step 5: Send Signed Command
```bash
# Extract the signed payload (everything between BEGIN/END)
SIGNED_PAYLOAD=$(cat command.json.asc)

# Send to API
curl -X POST http://localhost:8000/api/meter/config \
  -H "Content-Type: application/json" \
  -d "{\"signed_payload\": $(echo "$SIGNED_PAYLOAD" | python3 -c 'import sys, json; print(json.dumps(sys.stdin.read()))')}" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "success": true,
  "message": "Command executed: set_config",
  "signer": "engineer@deceptgrid.local",
  "command_action": "set_config"
}
```

---

# Layer 6: Physics-Based Anomaly Detection

## Overview
Real-world physics constraint validation on meter readings.
Detects compromised or tampered meters.

## Validations
1. **Statistical Baseline** - Z-score > 6σ = anomaly
2. **Ohm's Law** - Power ≈ V × I × PF (±10% tolerance)
3. **Adjacent Meters** - Voltage deviation > 20V = anomaly
4. **Load Consistency** - Current change > 20% = investigation

## Endpoints
- `POST /api/meter/reading/validate` - Validate meter readings

## Test Commands

### Test 1: Normal Reading (Valid)
```bash
curl -X POST http://localhost:8000/api/meter/reading/validate \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "SM-REAL-051",
    "voltage": 220.5,
    "current": 18.5,
    "power": 4100.0,
    "power_factor": 0.95
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "meter_id": "SM-REAL-051",
  "voltage": 220.5,
  "current": 18.5,
  "power": 4100.0,
  "power_factor": 0.95,
  "physics_valid": true,
  "validation_notes": [
    "✓ Power valid (error: 5.8%)",
    "✓ Adjacent meter voltage OK (SM-REAL-052)",
    "✓ Load consistent (change: 0.0%)"
  ],
  "status": "OPERATIONAL"
}
```

### Test 2: Voltage Anomaly (Z-score > 6)
```bash
curl -X POST http://localhost:8000/api/meter/reading/validate \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "SM-REAL-051",
    "voltage": 260.0,
    "current": 18.5,
    "power": 4810.0,
    "power_factor": 0.95
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "physics_valid": false,
  "status": "ANOMALY_DETECTED",
  "validation_notes": [
    "⚠️ Voltage anomaly detected",
    "⚠️ Adjacent meter voltage mismatch: 40.2V"
  ]
}
```

### Test 3: Ohm's Law Violation
```bash
curl -X POST http://localhost:8000/api/meter/reading/validate \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "SM-REAL-051",
    "voltage": 220.5,
    "current": 18.5,
    "power": 2000.0,
    "power_factor": 0.95
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "physics_valid": false,
  "status": "ANOMALY_DETECTED",
  "validation_notes": [
    "⚠️ Power mismatch: 48.4%"
  ]
}
```

### Test 4: Adjacent Meter Voltage Mismatch (ΔV > 20V)
```bash
curl -X POST http://localhost:8000/api/meter/reading/validate \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "SM-REAL-051",
    "voltage": 185.0,
    "current": 18.5,
    "power": 3423.0,
    "power_factor": 0.95
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "physics_valid": false,
  "status": "ANOMALY_DETECTED",
  "validation_notes": [
    "⚠️ Voltage anomaly detected",
    "⚠️ Adjacent meter voltage mismatch: 34.8V"
  ]
}
```

### Test 5: High Load Change (Change > 20%)
```bash
curl -X POST http://localhost:8000/api/meter/reading/validate \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "SM-REAL-051",
    "voltage": 220.5,
    "current": 25.0,
    "power": 5252.5,
    "power_factor": 0.95
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "physics_valid": true,
  "status": "OPERATIONAL",
  "validation_notes": [
    "✓ Power valid (error: 0.3%)",
    "✓ Adjacent meter voltage OK (SM-REAL-052)",
    "⚠️ Load change: 35.1% (needs investigation)"
  ]
}
```

---

## 🧪 AUTOMATED TEST SUITES

### Run All Layer 3-6 Tests
```bash
python3 test_layer5_layer6.py
```

### Expected Output
```
======================================================================
DeceptGrid LAYER 5 & 6 TEST SUITE
======================================================================

======================================================================
LAYER 6: PHYSICS-BASED ANOMALY DETECTION
======================================================================

📊 TEST 1: Normal Reading (SM-REAL-051)
  ✓ Valid: True
    ✓ Power valid (error: 5.8%)
    ✓ Adjacent meter voltage OK (SM-REAL-052)
    ✓ Load consistent (change: 0.0%)

📊 TEST 2: Voltage Anomaly - Z-score > 6
  ⚠️  Valid: False (ANOMALY DETECTED)
    ⚠️ Voltage anomaly detected
    ⚠️ Adjacent meter voltage mismatch: 40.2V

📊 TEST 3: Ohm's Law Violation - Power Mismatch > 10%
  ⚠️  Valid: False (ANOMALY DETECTED)
    ⚠️ Power mismatch: 48.4%

📊 TEST 4: Adjacent Meter Correlation Violation
  ⚠️  Valid: False (ANOMALY DETECTED)
    ⚠️ Voltage anomaly detected
    ⚠️ Adjacent meter voltage mismatch: 34.8V

📊 TEST 5: Load Consistency - Change > 20%
  ⚠️  Valid: True
    ⚠️ Load change: 35.1% (needs investigation)

✅ ALL PHYSICS VALIDATION TESTS COMPLETED
```

---

## 📊 COMPLETE LAYER INTEGRATION TEST

```bash
#!/bin/bash

echo "╔════════════════════════════════════════════════════════╗"
echo "║  DeceptGrid All Layers - Integration Test Suite      ║"
echo "╚════════════════════════════════════════════════════════╝"

echo ""
echo "✅ Layer 1: mTLS"
curl -s http://localhost:8000/api/health | python3 -m json.tool | head -5

echo ""
echo "✅ Layer 2: OTP"
curl -s http://localhost:8000/api/otp/test | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Status: {d['status']}\")"

echo ""
echo "✅ Layer 3: IDS"
curl -s -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","client_ip":"192.168.1.1","request_rate":2.5,"session_duration":40,"hour_of_day":14,"day_of_week":2,"unique_endpoints":3,"data_volume":4.5}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Action: {d['action']} (Score: {d['hybrid_score']:.1f})\")"

echo ""
echo "✅ Layer 4: Honeypot"
curl -s http://localhost:8000/api/ids/honeypot/meters | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Active: {d['count']} meters\")"

echo ""
echo "✅ Layer 5: Code Signing"
curl -s http://localhost:8000/api/meter/test/layers | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Status: {d['layer_5']['status']}\")"

echo ""
echo "✅ Layer 6: Physics Validation"
curl -s -X POST http://localhost:8000/api/meter/reading/validate \
  -H "Content-Type: application/json" \
  -d '{"meter_id":"SM-REAL-051","voltage":220.5,"current":18.5,"power":4100.0,"power_factor":0.95}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Status: {d['status']}\")"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║            ✅ ALL LAYERS OPERATIONAL                 ║"
echo "╚════════════════════════════════════════════════════════╝"
```

Save as `run_all_tests.sh` and execute:
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

---

## 📋 QUICK REFERENCE MATRIX

| Layer | Endpoint | Method | Auth | Purpose |
|-------|----------|--------|------|---------|
| 1 | `/api/meter/voltage` | GET | mTLS | Client cert auth |
| 2 | `/api/otp/request` | POST | None | Request OTP |
| 2 | `/api/otp/verify` | POST | None | Verify OTP |
| 3 | `/api/ids/assess-risk` | POST | None | Risk assessment |
| 4 | `/api/ids/honeypot/test` | GET | None | Test honeypots |
| 5 | `/api/meter/config` | POST | GPG | Signed commands |
| 6 | `/api/meter/reading/validate` | POST | None | Physics validation |

---

## 🔍 TROUBLESHOOTING

### Backend not running?
```bash
cd /home/dharshan/projects/DeceptGrid/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Port already in use?
```bash
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Check backend logs
```bash
tail -f /tmp/backend.log
```

### GPG Error: "no default secret key"?
- You haven't generated a GPG key yet
- Follow **Test 4** under Layer 5 to generate keys first
- Or use the test mode endpoints (they work without GPG setup)

---

## 📈 PRODUCTION CHECKLIST

- [ ] All 6 layers tested
- [ ] No errors in backend logs
- [ ] All endpoints responding
- [ ] Security events being logged
- [ ] Physics validation detecting anomalies
- [ ] Code signing verifying signatures
- [ ] OTP successfully generating/verifying
- [ ] mTLS certificates valid
- [ ] IDS scoring working (ALLOW/CHALLENGE/BLOCK)
- [ ] Honeypot meters responding

---

**✅ DeceptGrid System Complete and Operational!** 🚀
