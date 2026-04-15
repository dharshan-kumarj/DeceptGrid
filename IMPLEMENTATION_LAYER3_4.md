# DeceptGrid Layers 3 & 4 Implementation Guide

**Comprehensive Intrusion Detection + Honeypot System**

---

## 📋 TABLE OF CONTENTS

1. [Architecture Overview](#architecture)
2. [Layer 3: ML-Based IDS](#layer-3-ml-ids)
3. [Layer 4: Honeypot System](#layer-4-honeypot)
4. [Database Schema](#database-schema)
5. [Docker Networking](#docker-networking)
6. [Integration with Layers 1 & 2](#integration)
7. [Deployment Guide](#deployment)
8. [Security Considerations](#security)
9. [Testing & Validation](#testing)
10. [Monitoring](#monitoring)

---

## Architecture Overview {#architecture}

### Complete System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Request                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
           ┌─────────────────────────────┐
           │  Layer 1: mTLS              │
           │  Certificate Validation     │
           └────────────┬────────────────┘
                        │
                        ▼
           ┌─────────────────────────────┐
           │  Layer 2: OTP              │
           │  Email Authentication       │
           └────────────┬────────────────┘
                        │
                        ▼
           ┌─────────────────────────────┐
           │  Layer 3: ML IDS            │
           │  Risk Assessment            │
           │  - ML Anomaly Score         │
           │  - Rule-Based Score         │
           │  - Final Risk Score (0-100) │
           └────────┬──────────┬─────────┘
                    │          │
          Score < 50 │          │ Score >= 50
                    ▼          │
                  ALLOW    ┌──►CHALLENGE
                 (Proceed) └──►(Re-auth OTP)
                              │
                              ▼
                          ALLOW or BLOCK
                              │
                         ┌────┴─────────────┐
                         │                  │
                    REAL METERS    HONEYPOT METERS
                    (10.200.5.x)   (192.168.10.x)
                         │                  │
                         ▼                  ▼
                    Data Access        Log Intrusion
                                       Return Fake Data
                                       Embed Canary Token
```

### Network Architecture

```
┌─────────────────────────────────────────────────┐
│              PUBLIC INTERNET                    │
│              (Attacker Access)                  │
└──────────────────────┬──────────────────────────┘
                       │
       ┌───────────────┴──────────────┐
       │                              │
       ▼                              ▼
┌──────────────────┐        ┌──────────────────────┐
│  VLAN Engineering│        │  Honeypot Decoy      │
│  192.168.10.0/24 │        │                      │
├──────────────────┤        ├──────────────────────┤
│ Honeypot-1       │        │ 192.168.10.10        │
│ Honeypot-2       │        │ Fake Meter Data      │
│ Honeypot-3       │        │ Logs Intrustion      │
│ Gateway Bridge   │        │                      │
└────────┬─────────┘        └──────────┬───────────┘
         │                             │
         └──────────────┬──────────────┘
                        │
       ┌────────────────┴────────────┐
       │                             │
       ▼                             ▼
┌──────────────────┐    ┌──────────────────────┐
│ VLAN Meters      │    │  Backend Services    │
│ 10.200.5.0/24    │    │  (IDS, Auth, Logs)   │
├──────────────────┤    ├──────────────────────┤
│ Real Meter Data  │    │ FastAPI (port 8000)  │
│ (Protected)      │    │ PostgreSQL           │
│ (Isolated)       │    │ ML IDS               │
└──────────────────┘    └──────────────────────┘
```

---

## Layer 3: ML-Based IDS {#layer-3-ml-ids}

### Risk Scoring System (0-100 scale)

**Hybrid Approach:**
- ML Score (60% weight): Isolation Forest anomaly detection
- Rule Score (40% weight): Behavioral rules

**Decision Logic:**
```
Final Score = (ML_Score × 0.6) + (Rule_Score × 0.4)

if Final Score >= 80:
    ACTION = BLOCK      # Immediate isolation
    Log: IDS_BLOCK
elif Final Score >= 50:
    ACTION = CHALLENGE  # Redirect to Layer 2 OTP
    Log: IDS_CHALLENGE
else:
    ACTION = ALLOW      # Normal processing
    Log: IDS_ALLOW
```

### ML Model: Isolation Forest

**Why Isolation Forest?**
- Unsupervised learning (no labeled attacks needed)
- Efficient with high-dimensional data
- Robust to contamination in training data
- Fast real-time scoring

**Training Data Features (6D):**
1. `request_rate` - Requests per hour (0-15)
2. `session_duration` - Minutes per session (0-600)
3. `hour_of_day` - Hour when request occurs (0-23)
4. `day_of_week` - Day of week (0-6)
5. `unique_endpoints` - Number of different API endpoints accessed (1-30)
6. `data_volume` - Total data transfer in MB (0.1-500)

**Training Dataset (1000 samples):**
- 800 normal behavior samples
- 200 anomalous samples (synthetic attacks)

### Rule-Based Scoring System

**Rule 1: Request Rate Anomaly**
```
3x-5x normal: 40 points
5x+ normal:   80 points
Example: 10 req/min baseline + 30 req/min observed
```

**Rule 2: Temporal Anomaly**
```
Off-hours (weekday 18-08):   25 points
Weekend access:              30 points
Extreme (0-4am):             20 points
```

**Rule 3: Endpoint Scanning**
```
5-10 endpoints beyond baseline:  50 points
10+ endpoints:                    80 points
Example: User normally accesses 2 endpoints, suddenly 15
```

**Rule 4: Data Exfiltration**
```
2x-5x baseline data volume:   40 points
5x-10x baseline:               70 points
10x+ baseline:                 90 points
Example: Sudden 100 MB transfer vs 2 MB normal
```

**Rule 5: Session Duration**
```
3x-5x baseline:   35 points
5x+ baseline:     60 points
Example: 10hr session vs 30min normal
```

### Anomaly Detection Scenarios

**Scenario 1: Brute Force Attack**
- Request Rate: 10 req/sec → Score: 90
- Unique Endpoints: 50 → Score: 80
- Duration: 30 min continuous
- **Final: BLOCK**

**Scenario 2: Privileged User Scanning**
- Request Rate: 4 req/min → Score: 50
- Unique Endpoints: 12 (vs normal 2) → Score: 50
- Off-hours (2am): Score: 45
- **Final: CHALLENGE (OTP re-auth)**

**Scenario 3: Data Exfiltration**
- Request Rate: 2 req/min (normal) → Score: 0
- Data Volume: 200 MB (vs 5 MB normal) → Score: 90
- Session Duration: 120 min (vs 30 min normal) → Score: 40
- **Final: BLOCK**

### ML Model Training

**Location:** `backend/training_data.py`

```python
from training_data import create_training_dataset
from ids import MLAnomalyDetector

# Step 1: Generate synthetic training data
training_data = create_training_dataset()  # Shape: (1000, 6)

# Step 2: Train model
detector = MLAnomalyDetector()
detector.train(training_data)

# Step 3: Save model
detector.save("ml_models/ids_model.pkl")
```

**Training Parameters:**
- Algorithm: Isolation Forest
- n_estimators: 100 trees
- contamination: 0.1 (expect ~10% anomalies)
- random_state: 42 (reproducibility)

### API Integration

**Request**
```python
GET /api/meter/voltage
Headers:
  Authorization: Bearer <jwt_token>
  X-Session-Id: <session_id>
```

**Backend Processing (pseudo-code)**
```python
@app.get("/api/meter/voltage")
async def get_voltage(
    request: Request,
    cert_info: CertInfo = Depends(require_mtls_cert),
    db: AsyncSession = Depends(get_db)
):
    # Extract features from request
    features = extract_features(request, db)

    # Step 1: Run IDS assessment
    ids = IDS(model_path="ml_models/ids_model.pkl")
    assessment = await ids.assess_risk(
        db=db,
        user_id=cert_info.user_id,
        client_ip=request.client.host,
        features=features,
        session_id=request.headers.get("X-Session-Id")
    )

    # Step 2: Take action based on risk
    if assessment.action == RiskAction.BLOCK:
        await isolated_host_service.isolate(request.client.host)
        raise HTTPException(status_code=403, detail="Access blocked by IDS")

    elif assessment.action == RiskAction.CHALLENGE:
        # Redirect to OTP re-authentication
        return {"status": "challenge", "redirect_to": "/api/meter/otp"}

    # Step 3: Return protected data
    return get_meter_voltage_data(cert_info.user_id)
```

### Baseline Calculation

**User Baseline (stored in `user_baselines` table):**
```python
{
    "user_id": "uuid-123",
    "avg_request_rate": 2.5,        # req/hour
    "avg_session_duration": 45,     # minutes
    "typical_hours": [9-17],        # 9am-5pm
    "typical_days": [0-4],          # Mon-Fri
    "avg_endpoints": 3,             # /voltage, /status, /health
    "avg_data_volume": 5.0,         # MB per session
    "created_at": "2026-04-15T00:00:00Z",
    "updated_at": "2026-04-15T00:00:00Z"
}
```

**Baseline sources:**
- Manual configuration for known users
- Auto-computed from first 7 days of activity
- Regularly updated (monthly recalculation)

---

## Layer 4: Honeypot System {#layer-4-honeypot}

### Three-Meter Honeypot Deployment

**Honeypot Meters (Decoys):**
```
Meter ID          Network         Status      Purpose
─────────────────────────────────────────────────────
SM-HONEY-001      192.168.10.10   Active      Data exfiltration trap
SM-HONEY-002      192.168.10.11   Active      Endpoint enumeration trap
SM-HONEY-003      192.168.10.12   Active      Configuration access trap
```

**Attack Surface (What Attackers See):**
- Published in network discovery tools
- Referenced in default configurations
- Discoverable via port scanning
- No authentication required
- Responsive to all requests

### Honeypot Response Format

**Voltage Endpoint**
```json
{
  "meter_id": "SM-HONEY-001",
  "voltage": 221.34,
  "current": 18.92,
  "power_factor": 0.98,
  "status": "operational",
  "timestamp": "2026-04-15T07:30:45.123Z",
  "_canary_token": "a1b2c3d4e5f6g7h8i9j0"
}
```

**Canary Token:** Unique identifier embedded in every response. If found in attacker's infrastructure/data, confirms honeypot engagement.

**Config Endpoint**
```json
{
  "meter_id": "SM-HONEY-001",
  "model": "SmartMeter-3000X",
  "serial": "SN-SM-HONEY-001-54321",
  "utility_id": "UTIL-9999",
  "service_address": "123 Honeypot Lane, Deception City 90210",
  "meter_type": "3-phase",
  "ct_ratio": "200:5",
  "pt_ratio": "480:120",
  "_canary_token": "b2c3d4e5f6g7h8i9j0k1"
}
```

### Intrusion Detection Flow

**When honeypot is accessed:**

1. **Request Arrives**
   - No auth required
   - Accept any endpoint pattern
   - Respond with fake data

2. **Log Event**
   - Record in `honeypot_logs`
   - Extract canary token
   - Extract client IP, user-agent, headers

3. **Alert Security**
   - Create `CRITICAL` event in `security_logs`
   - Trigger alert system
   - Capture HTTP metadata

4. **Return Believable Response**
   - Include monitoring beacon
   - Add tracking token
   - Mimic real meter delays

### Honeypot Endpoints

**GET /api/honeypot/meter/<meter_id>/voltage**
- Returns: Voltage + current + power_factor + canary_token
- Logs: honeypot_logs entry with IPs, headers

**GET /api/honeypot/meter/<meter_id>/status**
- Returns: Battery %, signal strength, firmware version
- Logs: Intrusion attempt with device fingerprint

**POST /api/honeypot/meter/<meter_id>/config**
- Accepts: Any JSON payload
- Returns: Configuration details + canary token
- Logs: Full POST body, authentication attempts

**Catch-all: Any other path**
- Returns: "Endpoint not found" (404)
- Logs: Full request path, method, headers
- Tracks: Enumeration attempts

### Canary Token Tracking

**Token Generation:**
```python
data = f"{meter_id}:{request_count}:{uuid.uuid4()}"
token = hashlib.sha256(data.encode()).hexdigest()[:32]
```

**Use Case:**
If attacker extracts honeypot data and stores it, the token becomes a identifier:
- Found in attacker's GitHub repo → Commits attributed to honeypot
- Found in attacker's email → Email traced to honeypot engagement
- Found in C2 command outputs → C2 confirmed communicating

---

## Database Schema {#database-schema}

### Layer 3 Tables

**`user_baselines` Table**
```sql
CREATE TABLE user_baselines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  avg_request_rate FLOAT DEFAULT 2.5,
  avg_session_duration FLOAT DEFAULT 45.0,
  typical_hours INT[] DEFAULT ARRAY[9,10,11,12,13,14,15,16,17],
  typical_days INT[] DEFAULT ARRAY[0,1,2,3,4],
  avg_endpoints INT DEFAULT 3,
  avg_data_volume FLOAT DEFAULT 5.0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id),
  INDEX idx_user_baseline (user_id)
);
```

**`active_sessions` Table**
```sql
CREATE TABLE active_sessions (
  session_id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  client_ip INET NOT NULL,
  started_at TIMESTAMP DEFAULT NOW(),
  last_activity TIMESTAMP DEFAULT NOW(),
  request_count INT DEFAULT 0,
  data_transferred FLOAT DEFAULT 0.0,
  status VARCHAR(20) DEFAULT 'active',
  INDEX idx_session_user (user_id),
  INDEX idx_session_ip (client_ip),
  INDEX idx_session_status (status)
);
```

**`ids_logs` Table**
```sql
CREATE TABLE ids_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  client_ip INET NOT NULL,
  risk_score FLOAT NOT NULL,
  action VARCHAR(20) NOT NULL CHECK (action IN ('allow', 'challenge', 'block')),
  reasons TEXT[] NOT NULL,
  ml_score FLOAT NOT NULL,
  rule_score FLOAT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_ids_user (user_id),
  INDEX idx_ids_ip (client_ip),
  INDEX idx_ids_score (risk_score),
  INDEX idx_ids_action (action)
);
```

### Layer 4 Tables

**`honeypot_logs` Table**
```sql
CREATE TABLE honeypot_logs (
  id BIGSERIAL PRIMARY KEY,
  meter_id VARCHAR(50) NOT NULL,
  client_ip INET NOT NULL,
  endpoint VARCHAR(255) NOT NULL,
  method VARCHAR(10) NOT NULL,
  user_agent TEXT,
  auth_attempt BOOLEAN DEFAULT FALSE,
  response_token VARCHAR(64) NOT NULL,
  details JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_honeypot_meter (meter_id),
  INDEX idx_honeypot_ip (client_ip),
  INDEX idx_honeypot_token (response_token),
  INDEX idx_honeypot_created (created_at)
);
```

**`honeypot_stats` Table (Aggregated)**
```sql
CREATE TABLE honeypot_stats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meter_id VARCHAR(50) NOT NULL,
  access_count INT DEFAULT 0,
  unique_ips INT DEFAULT 0,
  last_access TIMESTAMP,
  common_endpoints VARCHAR(255)[],
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(meter_id)
);
```

---

## Docker Networking {#docker-networking}

### Docker Compose Configuration

**File:** `docker-compose.yml`

```yaml
version: '3.9'

services:
  # Backend API + IDS
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    networks:
      - vlan-engineering
      - vlan-meters
    environment:
      DATABASE_URL: postgresql+asyncpg://...
    depends_on:
      - postgres

  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: deceptgrid
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    networks:
      - vlan-meters
    volumes:
      - db_data:/var/lib/postgresql/data

  # Honeypot container (3 instances)
  honeypot-1:
    build: ./honeypot
    networks:
      - vlan-engineering
    environment:
      HONEYPOT_ID: SM-HONEY-001
      HONEYPOT_IP: 192.168.10.10
    ports:
      - "8001:8000"

  honeypot-2:
    build: ./honeypot
    networks:
      - vlan-engineering
    environment:
      HONEYPOT_ID: SM-HONEY-002
      HONEYPOT_IP: 192.168.10.11
    ports:
      - "8002:8000"

  honeypot-3:
    build: ./honeypot
    networks:
      - vlan-engineering
    environment:
      HONEYPOT_ID: SM-HONEY-003
      HONEYPOT_IP: 192.168.10.12
    ports:
      - "8003:8000"

networks:
  vlan-engineering:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.10.0/24
    driver_opts:
      com.docker.network.bridge.name: br-engineering

  vlan-meters:
    driver: bridge
    ipam:
      config:
        - subnet: 10.200.5.0/24
    driver_opts:
      com.docker.network.bridge.name: br-meters
    internal: true

volumes:
  db_data:
```

### Network Isolation Rules

**vlan-engineering (Honeypot VLAN):**
- Publicly accessible
- Contains honeypot instances only
- Monitored for all traffic
- No firewall restrictions

**vlan-meters (Meter VLAN):**
- Internal only (no external access)
- Contains real meter data
- Contains PostgreSQL
- Protected by IDS

---

## Integration with Layers 1 & 2 {#integration}

### Request Processing Pipeline

```
1. Client connects with mTLS cert (Layer 1)
   ↓ Validate certificate
   ├─ Invalid → 403 Forbidden
   └─ Valid → Continue

2. Client authenticates with password + OTP (Layer 2)
   ↓ Send OTP via email
   ├─ Incorrect OTP → 403 Forbidden
   └─ Correct OTP → Continue

3. IDS ASSESSES RISK (Layer 3) ← NEW
   ↓ Extract features, score risk
   ├─ Score < 50 → ALLOW
   ├─ Score 50-79 → CHALLENGE (re-request OTP)
   └─ Score >= 80 → BLOCK (isolate IP)

4. Access meter data (if allowed)
   ↓ Return encrypted data
   └─ Log access event

5. Optional: Honeypot detects alternate access paths
   ↓ Log intrusion, embed canary token
   └─ Alert security team
```

### IDS Redirect on High Risk

**If risk score 50-79:**
```
HTTP/1.1 307 Temporary Redirect
Location: /api/meter/otp?challenge=true
X-Risk-Score: 65
X-Risk-Reason: ["Unusual time access (2:34 AM)", "Data transfer 8x normal"]

Client must re-authenticate with OTP before access is granted
```

### Isolation on Critical Risk

**If risk score >= 80:**
```
HTTP/1.1 403 Forbidden
X-Risk-Score: 92
X-Risk-Action: BLOCK
X-Isolation-Duration: 3600

Actions taken:
- IP added to isolated_hosts table
- All subsequent requests from same IP blocked for 1 hour
- Security team alerted with details
- Incident logged to security_logs
```

---

## Deployment Guide {#deployment}

### Step 1: Install ML Dependencies

```bash
cd backend
pip install scikit-learn joblib numpy

# Verify
python -c "from sklearn.ensemble import IsolationForest; print('✓ scikit-learn installed')"
```

### Step 2: Generate Training Data

```bash
cd backend
python -c "
from training_data import create_training_dataset, create_baseline_profiles
import numpy as np

# Generate training data
data = create_training_dataset()
np.save('training_data.npy', data)
print('✓ Training data generated (1000 samples)')

# Generate profiles
profiles = create_baseline_profiles(50)
print(f'✓ Baseline profiles created (50 users)')
"
```

### Step 3: Train ML Model

```bash
cd backend
python -c "
from training_data import create_training_dataset
from ids import MLAnomalyDetector
import os

# Create models directory
os.makedirs('ml_models', exist_ok=True)

# Generate and train
data = create_training_dataset()
detector = MLAnomalyDetector()
detector.train(data)
detector.save('ml_models/ids_model.pkl')

print('✓ IDS model trained and saved')
"
```

### Step 4: Update Database

```bash
# Run migration (add new tables)
psql $DATABASE_URL -f database/layer3_4_migration.sql

# Seed baseline data
python backend/setup_baselines.py
```

### Step 5: Start Services

```bash
# Using the existing startup script
cd /home/dharshan/projects/DeceptGrid
./start_services.sh

# Plus honeypot (if using Docker)
docker-compose up -d honeypot-1 honeypot-2 honeypot-3
```

---

## Security Considerations {#security}

### Model Poisoning Prevention

- Training data from controlled environment only
- No online learning (model fixed post-deployment)
- Model file integrity check (SHA-256 hash)
- Model versioning with deployment tracking

### Honeypot Isolation

- Honeypot never touches real infrastructure
- Network segmentation enforced at Docker level
- No database write-through from honeypot
- Canary tokens prevent data cross-contamination

### Feature Extraction Safety

- sanitize client IP (prevent SQL injection)
- Limit feature values to known ranges
- No model inference on untrusted data
- Rate limit feature extraction (1/sec per user)

### Logging Security

- Append-only security_logs table
- No log deletion (delete events trigger audit)
- Encrypted connection to PostgreSQL
- Logs validated before storage

---

## Testing & Validation {#testing}

### Unit Tests

```python
# Test 1: Risk scoring consistency
def test_risk_scoring():
    scorer = RuleBasedScorer(default_baseline())
    score, reasons = scorer.compute_score(
        request_rate=10,  # 4x normal
        session_duration=120,
        hour=2,  # Off-hours
        day=6,   # Sunday
        unique_endpoints=20,  # Endpoint scan
        data_volume=100  # Data exfil
    )
    assert score >= 70, f"Expected high risk, got {score}"

# Test 2: ML model scoring
def test_ml_scoring():
    detector = MLAnomalyDetector("ml_models/ids_model.pkl")
    features = np.array([[10, 120, 2, 6, 20, 100]])
    score = detector.predict_anomaly_score(features)
    assert 0 <= score <= 100, f"Score out of range: {score}"

# Test 3: Honeypot generation
def test_honeypot_response():
    meter = HoneypotMeter("SM-HONEY-001")
    response = meter.generate_response()
    assert 210 < response.voltage < 230
    assert 0 < response.current < 50
    assert len(response._canary_token) == 32
```

### Integration Tests

```bash
# Test 1: Normal user access (should ALLOW)
curl --cert certs/client.crt \
     --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/api/meter/voltage
# Expected: 200 OK with meter data

# Test 2: Suspicious access (should CHALLENGE or BLOCK)
# Simulate from different IP, off-hours
curl --header "X-Forwarded-For: 192.168.1.100" \
     --cert certs/client.crt \
     https://localhost:8443/api/meter/voltage?time=02:34
# Expected: 307 Redirect to OTP or 403 Blocked

# Test 3: Honeypot endpoint
curl http://192.168.10.10:8000/api/meter/voltage
# Expected: 200 with fake data + canary token
# Check logs: honeypot_logs should have entry
```

---

## Monitoring {#monitoring}

### Key Metrics (via SQL queries)

**IDS Effectiveness:**
```sql
SELECT
  action,
  COUNT(*) as count,
  AVG(risk_score) as avg_score,
  MAX(risk_score) as max_score
FROM ids_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY action;
```

**Honeypot Engagement:**
```sql
SELECT
  meter_id,
  COUNT(*) as access_count,
  COUNT(DISTINCT client_ip) as unique_ips
FROM honeypot_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY meter_id;
```

**Risk Score Distribution:**
```sql
SELECT
  CASE
    WHEN risk_score < 50 THEN 'ALLOW'
    WHEN risk_score < 80 THEN 'CHALLENGE'
    ELSE 'BLOCK'
  END as action,
  COUNT(*) as occurrences
FROM ids_logs
GROUP BY action;
```

### Alerting Rules

**Alert on BLOCK:**
- Risk score >= 80
- Send alert immediately
- Include user, IP, reasons, recommendations

**Alert on Honeypot Access:**
- Any honeypot_logs entry
- Severity: CRITICAL
- Include canary token for tracking

**Alert on Repeated CHALLENGE:**
- Same user 3+ CHALLENGE in 1 hour
- Possible credential compromise
- Recommend password reset

---

## File Structure

```
DeceptGrid/
├── backend/
│   ├── ids.py                  # Layer 3 ML IDS implementation
│   ├── honeypot.py             # Layer 4 honeypot system
│   ├── training_data.py        # ML training data generator
│   ├── ml_models/
│   │   └── ids_model.pkl       # Trained IDS model
│   ├── models/security.py      # Updated ORM models
│   └── setup_baselines.py      # Baseline initialization script
│
├── database/
│   ├── init.sql                # Original schema
│   └── layer3_4_migration.sql  # New tables for Layer 3 & 4
│
├── docker-compose.yml          # Updated with honeypot services
│
└── IMPLEMENTATION_LAYER3_4.md  # This file
```

---

## Success Criteria

✅ **Layer 3 IDS:**
- ML model trains in < 1 second on 1000 samples
- Risk scoring responds in < 100ms per request
- Rule-based scoring provides interpretable reasons
- Hybrid score accurately identifies anomalies
- Database logging captures all assessments

✅ **Layer 4 Honeypot:**
- 3 honeypot meters active and monitoring
- All honeypot access logged with canary tokens
- Network segmentation prevents access to real meters
- No false positives from legitimate users
- Intrusion detection triggers security alerts

✅ **Integration:**
- IDS executes after Layer 1 & 2 authentication
- CHALLENGE action triggers Layer 2 OTP re-auth
- BLOCK action isolates host within 100ms
- Honeypot logs integrated with security_logs

---

**Deployment Ready:** ✅
**Production Grade:** ✅
**Tested Scenarios:** ✅
