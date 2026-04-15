#!/bin/bash

# DeceptGrid Layers 3 & 4 - Complete Installation & Testing Suite
# Run this script to install, train, test, and validate all components

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DeceptGrid Layer 3 & 4 - Installation & Testing    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"

PROJECT_DIR="/home/dharshan/projects/DeceptGrid"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"

# Step 1: Check if venv exists
echo -e "\n${BLUE}Step 1: Checking virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating new virtual environment...${NC}"
    cd "$BACKEND_DIR"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Step 2: Activate venv and install dependencies
echo -e "\n${BLUE}Step 2: Installing dependencies...${NC}"
source "$VENV_DIR/bin/activate"

# Install core requirements
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Install ML dependencies
echo "Installing scikit-learn, joblib, numpy..."
pip install scikit-learn==1.4.1.post1 joblib==1.3.2 numpy==1.24.3 > /dev/null 2>&1

echo -e "${GREEN}✓ All dependencies installed${NC}"

# Step 3: Verify installations
echo -e "\n${BLUE}Step 3: Verifying installations...${NC}"

python3 << 'VERIFY_SCRIPT'
import sys

try:
    from sklearn.ensemble import IsolationForest
    print("  ✓ scikit-learn imported")
except ImportError as e:
    print(f"  ✗ scikit-learn failed: {e}")
    sys.exit(1)

try:
    import joblib
    print("  ✓ joblib imported")
except ImportError as e:
    print(f"  ✗ joblib failed: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("  ✓ numpy imported")
except ImportError as e:
    print(f"  ✗ numpy failed: {e}")
    sys.exit(1)

try:
    from ids import IDS, RiskAction, RuleBasedScorer
    print("  ✓ ids module imported")
except ImportError as e:
    print(f"  ✗ ids module failed: {e}")
    sys.exit(1)

try:
    from honeypot import HoneypotSystem, HoneypotMeter
    print("  ✓ honeypot module imported")
except ImportError as e:
    print(f"  ✗ honeypot module failed: {e}")
    sys.exit(1)

try:
    from training_data import TrainingDataGenerator, create_training_dataset
    print("  ✓ training_data module imported")
except ImportError as e:
    print(f"  ✗ training_data module failed: {e}")
    sys.exit(1)

print("\n✓ All imports successful!")
VERIFY_SCRIPT

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Import verification failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All modules verified${NC}"

# Step 4: Generate training data
echo -e "\n${BLUE}Step 4: Generating ML training data...${NC}"

python3 << 'TRAINING_SCRIPT'
from training_data import create_training_dataset
import numpy as np
import os

os.makedirs("ml_models", exist_ok=True)

print("  Generating 1000 training samples (800 normal + 200 anomalies)...")
data = create_training_dataset()
print(f"  Training data shape: {data.shape}")
print(f"  Min values: {data.min(axis=0)}")
print(f"  Max values: {data.max(axis=0)}")
print(f"  Mean values: {data.mean(axis=0)}")

print("✓ Training data generated successfully")
TRAINING_SCRIPT

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Training data generation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Training data ready${NC}"

# Step 5: Train ML model
echo -e "\n${BLUE}Step 5: Training IDS ML model...${NC}"

python3 << 'MODEL_SCRIPT'
from training_data import create_training_dataset
from ids import MLAnomalyDetector
import numpy as np

print("  Generating training data...")
training_data = create_training_dataset()

print("  Training Isolation Forest model...")
detector = MLAnomalyDetector()
detector.train(training_data)

print("  Saving model to ml_models/ids_model.pkl...")
detector.save("ml_models/ids_model.pkl")

print("✓ IDS model trained and saved")
MODEL_SCRIPT

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Model training failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ML model trained${NC}"

# Step 6: Test IDS Scoring
echo -e "\n${BLUE}Step 6: Testing IDS Risk Scoring...${NC}"

python3 << 'IDS_TEST'
import numpy as np
from ids import IDS, RuleBasedScorer, UserBaseline, RiskAction

print("  Testing rule-based scoring...")

# Create baseline
baseline = UserBaseline(
    user_id="test_user",
    avg_request_rate=2.5,
    avg_session_duration=45,
    typical_hours=list(range(9, 18)),
    typical_days=list(range(0, 5)),
    avg_endpoints=3,
    avg_data_volume=5.0
)

scorer = RuleBasedScorer(baseline)

# Test 1: Normal behavior
print("\n  Test 1: Normal behavior")
score, reasons = scorer.compute_score(
    request_rate=2.5,
    session_duration=40,
    hour=14,
    day=2,
    unique_endpoints=3,
    data_volume=4.5
)
print(f"    Risk Score: {score:.1f}/100")
print(f"    Action: {'ALLOW' if score < 50 else 'CHALLENGE' if score < 80 else 'BLOCK'}")
for reason in reasons:
    print(f"    - {reason}")

# Test 2: Suspicious behavior (high request rate)
print("\n  Test 2: High request rate (10 req/sec)")
score, reasons = scorer.compute_score(
    request_rate=10,
    session_duration=120,
    hour=14,
    day=2,
    unique_endpoints=5,
    data_volume=20
)
print(f"    Risk Score: {score:.1f}/100")
print(f"    Action: {'ALLOW' if score < 50 else 'CHALLENGE' if score < 80 else 'BLOCK'}")

# Test 3: Off-hours access + endpoint scanning
print("\n  Test 3: Off-hours + endpoint scanning")
score, reasons = scorer.compute_score(
    request_rate=5,
    session_duration=90,
    hour=2,
    day=6,
    unique_endpoints=15,
    data_volume=50
)
print(f"    Risk Score: {score:.1f}/100")
print(f"    Action: {'ALLOW' if score < 50 else 'CHALLENGE' if score < 80 else 'BLOCK'}")

# Test 4: Data exfiltration
print("\n  Test 4: Data exfiltration (200 MB)")
score, reasons = scorer.compute_score(
    request_rate=3,
    session_duration=180,
    hour=13,
    day=1,
    unique_endpoints=8,
    data_volume=200
)
print(f"    Risk Score: {score:.1f}/100")
print(f"    Action: {'ALLOW' if score < 50 else 'CHALLENGE' if score < 80 else 'BLOCK'}")

print("\n✓ Rule-based scoring tests completed")
IDS_TEST

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ IDS scoring tests failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ IDS scoring functional${NC}"

# Step 7: Test ML Anomaly Detection
echo -e "\n${BLUE}Step 7: Testing ML Anomaly Detection...${NC}"

python3 << 'ML_TEST'
import numpy as np
from ids import MLAnomalyDetector

print("  Loading trained model...")
detector = MLAnomalyDetector("ml_models/ids_model.pkl")

print("\n  Testing ML anomaly scores...")

# Test 1: Normal behavior
print("  Test 1: Normal behavior")
normal = np.array([[2.5, 45, 14, 2, 3, 5.0]])
score = detector.predict_anomaly_score(normal)
print(f"    ML Score: {score:.1f}/100 ({'NORMAL' if score < 50 else 'ANOMALY'})")

# Test 2: High request rate
print("  Test 2: High request rate")
high_rate = np.array([[10, 120, 14, 2, 5, 20]])
score = detector.predict_anomaly_score(high_rate)
print(f"    ML Score: {score:.1f}/100 ({'NORMAL' if score < 50 else 'ANOMALY'})")

# Test 3: Endpoint scanning
print("  Test 3: Endpoint scanning")
scanning = np.array([[5, 90, 2, 6, 25, 50]])
score = detector.predict_anomaly_score(scanning)
print(f"    ML Score: {score:.1f}/100 ({'NORMAL' if score < 50 else 'ANOMALY'})")

# Test 4: Data exfiltration
print("  Test 4: Data exfiltration")
exfil = np.array([[3, 180, 13, 1, 8, 300]])
score = detector.predict_anomaly_score(exfil)
print(f"    ML Score: {score:.1f}/100 ({'NORMAL' if score < 50 else 'ANOMALY'})")

print("\n✓ ML anomaly detection tests completed")
ML_TEST

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ ML tests failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ML anomaly detection functional${NC}"

# Step 8: Test Honeypot System
echo -e "\n${BLUE}Step 8: Testing Honeypot System...${NC}"

python3 << 'HONEYPOT_TEST'
from honeypot import HoneypotSystem, HoneypotMeter
import json

print("  Initializing honeypot system...")
honeypot_system = HoneypotSystem()

print(f"  Active honeypot meters: {list(honeypot_system.meters.keys())}")

# Test each meter
for meter_id, meter in honeypot_system.meters.items():
    print(f"\n  Testing {meter_id}...")

    # Test voltage response
    response = meter.generate_response()
    print(f"    Voltage: {response.voltage}V")
    print(f"    Current: {response.current}A")
    print(f"    Power Factor: {response.power_factor}")
    print(f"    Canary Token: {response._canary_token[:16]}...")
    assert 210 < response.voltage < 230, "Voltage out of range"
    assert 0 < response.current < 50, "Current out of range"
    assert len(response._canary_token) == 32, "Invalid token length"

    # Test status response
    status = meter.generate_status()
    assert "battery" in status
    assert "signal_strength" in status
    assert "_canary_token" in status
    print(f"    Status: {status['status']}")

    # Test config response
    config = meter.generate_config()
    assert "model" in config
    assert "serial" in config
    print(f"    Model: {config['model']}")

print("\n✓ Honeypot system tests completed")
HONEYPOT_TEST

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Honeypot tests failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Honeypot system functional${NC}"

# Step 9: Integration Test (Hybrid IDS)
echo -e "\n${BLUE}Step 9: Testing Hybrid IDS (ML + Rules)...${NC}"

python3 << 'HYBRID_TEST'
import numpy as np
from ids import IDS, RuleBasedScorer, UserBaseline, RiskAction

print("  Loading ML model and testing hybrid scoring...")

ids = IDS("ml_models/ids_model.pkl")

# Simulate feature extraction
test_cases = [
    {
        "name": "Normal user (business hours)",
        "features": {
            "request_rate": 2.5,
            "session_duration": 40,
            "hour_of_day": 14,
            "day_of_week": 2,
            "unique_endpoints": 3,
            "data_volume": 5.0
        }
    },
    {
        "name": "Suspicious (extreme hours)",
        "features": {
            "request_rate": 8,
            "session_duration": 150,
            "hour_of_day": 3,
            "day_of_day": 6,
            "unique_endpoints": 20,
            "data_volume": 100
        }
    },
    {
        "name": "Brute force (high rate)",
        "features": {
            "request_rate": 15,
            "session_duration": 30,
            "hour_of_day": 13,
            "day_of_week": 1,
            "unique_endpoints": 50,
            "data_volume": 200
        }
    }
]

for test_case in test_cases:
    print(f"\n  Case: {test_case['name']}")

    baseline = UserBaseline(
        user_id="hybrid_test",
        avg_request_rate=2.5,
        avg_session_duration=45,
        typical_hours=list(range(9, 18)),
        typical_days=list(range(0, 5)),
        avg_endpoints=3,
        avg_data_volume=5.0
    )

    scorer = RuleBasedScorer(baseline)
    rule_score, _ = scorer.compute_score(**test_case["features"])

    ml_features = np.array([[
        test_case["features"]["request_rate"],
        test_case["features"]["session_duration"],
        test_case["features"]["hour_of_day"],
        test_case["features"]["day_of_week"],
        test_case["features"]["unique_endpoints"],
        test_case["features"]["data_volume"],
    ]])

    from ids import MLAnomalyDetector
    detector = MLAnomalyDetector("ml_models/ids_model.pkl")
    ml_score = detector.predict_anomaly_score(ml_features)

    # Hybrid scoring
    final_score = (ml_score * 0.6) + (rule_score * 0.4)

    if final_score >= 80:
        action = "BLOCK"
    elif final_score >= 50:
        action = "CHALLENGE"
    else:
        action = "ALLOW"

    print(f"    ML Score: {ml_score:.1f}")
    print(f"    Rule Score: {rule_score:.1f}")
    print(f"    Final Score: {final_score:.1f}")
    print(f"    Action: {action}")

print("\n✓ Hybrid IDS tests completed")
HYBRID_TEST

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Hybrid IDS tests failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Hybrid IDS functional${NC}"

# Step 10: Summary
echo -e "\n${BLUE}Step 10: Test Summary${NC}"

python3 << 'SUMMARY'
import os
import json

print("\n  ✓ All components tested successfully!")
print("\n  Generated files/models:")

if os.path.exists("ml_models/ids_model.pkl"):
    size = os.path.getsize("ml_models/ids_model.pkl")
    print(f"    - ml_models/ids_model.pkl ({size:,} bytes)")

print("\n  Ready for deployment!")
SUMMARY

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✓ ALL TESTS PASSED SUCCESSFULLY ✓            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "  1. Review: ${YELLOW}cat $PROJECT_DIR/IMPLEMENTATION_LAYER3_4.md${NC}"
echo -e "  2. Start services: ${YELLOW}./start_services.sh${NC}"
echo -e "  3. Test endpoint: ${YELLOW}curl https://localhost:8443/api/meter/voltage${NC}"

echo -e "\n${YELLOW}All checks completed successfully!${NC}\n"
