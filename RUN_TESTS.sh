#!/bin/bash

# DeceptGrid Layers 3 & 4 - Quick Copy-Paste Commands

echo '
╔════════════════════════════════════════════════════════════════════╗
║     DeceptGrid Layer 3 & 4 - Copy-Paste Command Reference         ║
╚════════════════════════════════════════════════════════════════════╝

🚀 OPTION 1: Run Complete Automated Test (RECOMMENDED)
───────────────────────────────────────────────────────

cd /home/dharshan/projects/DeceptGrid
bash test_layers_3_4.sh

# This runs ALL tests automatically and shows results


🚀 OPTION 2: Run Tests Manually Step-by-Step
───────────────────────────────────────────────────

# Step 1: Setup
cd /home/dharshan/projects/DeceptGrid/backend
source .venv/bin/activate

# Step 2: Install ML dependencies
pip install scikit-learn==1.4.1.post1 joblib==1.3.2 numpy==1.24.3

# Step 3: Generate training data
python3 << '"'"'EOF'"'"'
from training_data import create_training_dataset
import os
os.makedirs("ml_models", exist_ok=True)
data = create_training_dataset()
print(f"✓ Generated {data.shape[0]} training samples")
EOF

# Step 4: Train ML model
python3 << '"'"'EOF'"'"'
from training_data import create_training_dataset
from ids import MLAnomalyDetector
detector = MLAnomalyDetector()
detector.train(create_training_dataset())
detector.save("ml_models/ids_model.pkl")
print("✓ Model trained and saved")
EOF

# Step 5: Test scoring
python3 << '"'"'EOF'"'"'
from ids import RuleBasedScorer, UserBaseline
baseline = UserBaseline(
    user_id="test",
    avg_request_rate=2.5,
    avg_session_duration=45,
    typical_hours=list(range(9, 18)),
    typical_days=list(range(0, 5)),
    avg_endpoints=3,
    avg_data_volume=5.0
)
scorer = RuleBasedScorer(baseline)
score, _ = scorer.compute_score(
    request_rate=10,
    session_duration=120,
    hour=2,
    day=6,
    unique_endpoints=20,
    data_volume=100
)
print(f"Risk Score: {score:.1f} → {'ALLOW' if score < 50 else 'CHALLENGE' if score < 80 else 'BLOCK'}")
EOF

# Step 6: Test honeypot
python3 << '"'"'EOF'"'"'
from honeypot import HoneypotSystem
honeypot = HoneypotSystem()
for meter_id, meter in honeypot.meters.items():
    response = meter.generate_response()
    print(f"{meter_id}: {response.voltage}V, Token: {response._canary_token[:16]}...")
EOF

# Step 7: Test hybrid ID
python3 << '"'"'EOF'"'"'
import numpy as np
from ids import MLAnomalyDetector, RuleBasedScorer, UserBaseline
detector = MLAnomalyDetector("ml_models/ids_model.pkl")
baseline = UserBaseline(user_id="test", avg_request_rate=2.5, avg_session_duration=45,
    typical_hours=list(range(9, 18)), typical_days=list(range(0, 5)), avg_endpoints=3, avg_data_volume=5.0)
scorer = RuleBasedScorer(baseline)
ml_score = detector.predict_anomaly_score(np.array([[10, 120, 2, 6, 20, 100]]))
rule_score, _ = scorer.compute_score(10, 120, 2, 6, 20, 100)
hybrid = (ml_score * 0.6) + (rule_score * 0.4)
print(f"ML: {ml_score:.1f} | Rule: {rule_score:.1f} | Hybrid: {hybrid:.1f} → {'BLOCK' if hybrid >= 80 else 'CHALLENGE' if hybrid >= 50 else 'ALLOW'}")
EOF


🎯 VERIFICATION COMMANDS
───────────────────────────────────────────────────

# Check model file exists
ls -la ml_models/ids_model.pkl

# Verify imports work
python3 -c "from ids import IDS; from honeypot import HoneypotSystem; print(\"✓ All imports OK\")"

# Check file structure
cd /home/dharshan/projects/DeceptGrid/backend
ls -la ids.py honeypot.py training_data.py


📋 VIEW DOCUMENTATION
───────────────────────────────────────────────────

# Full implementation guide
less IMPLEMENTATION_LAYER3_4.md

# Test command reference
less TEST_COMMANDS.md


🔍 QUICK VALIDATION (Run after install)
───────────────────────────────────────────────────

python3 << '"'"'QUICK_VALIDATE'"'"'
print(\"Running quick validation...\")

# Test 1: Imports
try:
    from sklearn.ensemble import IsolationForest
    from ids import IDS
    from honeypot import HoneypotSystem
    print(\"✓ All imports successful\")
except ImportError as e:
    print(f\"✗ Import failed: {e}\")
    exit(1)

# Test 2: Model
try:
    import os
    if os.path.exists(\"ml_models/ids_model.pkl\"):
        from ids import MLAnomalyDetector
        detector = MLAnomalyDetector(\"ml_models/ids_model.pkl\")
        print(\"✓ Model loaded successfully\")
    else:
        print(\"! Model not trained yet (run training steps first)\")
except Exception as e:
    print(f\"✗ Model error: {e}\")
    exit(1)

# Test 3: Honeypot
try:
    honeypot = HoneypotSystem()
    print(f\"✓ Honeypot active: {list(honeypot.meters.keys())}\")
except Exception as e:
    print(f\"✗ Honeypot error: {e}\")
    exit(1)

print(\"\\n✓ Validation complete!\")
QUICK_VALIDATE


🚀 INTEGRATE WITH DECEPTGRID
───────────────────────────────────────────────────

# After all tests pass, start the full system
cd /home/dharshan/projects/DeceptGrid
./start_services.sh

# Test from another terminal (Layer 1 + 2 + 3 integration)
curl --cert certs/client.crt \\
     --key certs/client.key \\
     --cacert certs/ca.crt \\
     https://localhost:8443/api/meter/voltage


📊 CHECK LOGS (After integration)
───────────────────────────────────────────────────

# Backend logs
tail -50 /tmp/backend.log | grep -i ids

# View IDS decisions
psql $DATABASE_URL -c "SELECT user_id, risk_score, action FROM ids_logs ORDER BY created_at DESC LIMIT 10;"

# View honeypot access
psql $DATABASE_URL -c "SELECT meter_id, client_ip, endpoint FROM honeypot_logs ORDER BY created_at DESC LIMIT 10;"


═════════════════════════════════════════════════════════════════════

✨ ALL COMMANDS READY TO COPY-PASTE ✨

Start with: cd /home/dharshan/projects/DeceptGrid && bash test_layers_3_4.sh
'
