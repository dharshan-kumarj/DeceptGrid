#!/bin/bash
echo "============================================"
echo "  Testing Layer 3 & 4 - All Scenarios"
echo "============================================"

echo ""
echo "1️⃣  Testing Normal User - EXPECT: ALLOW"
curl -s -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user001","client_ip":"192.168.1.100","request_rate":2.5,"session_duration":40,"hour_of_day":14,"day_of_week":2,"unique_endpoints":3,"data_volume":4.5}' | grep -o '"action":"[^"]*"'

echo ""
echo "2️⃣  Testing Brute Force - EXPECT: BLOCK"
curl -s -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{"user_id":"attacker","client_ip":"203.0.113.45","request_rate":15,"session_duration":30,"hour_of_day":13,"day_of_week":1,"unique_endpoints":50,"data_volume":500}' | grep -o '"action":"[^"]*"'

echo ""
echo "3️⃣  Testing Data Exfiltration - EXPECT: BLOCK"
curl -s -X POST http://localhost:8000/api/ids/assess-risk \
  -H "Content-Type: application/json" \
  -d '{"user_id":"admin","client_ip":"10.0.0.50","request_rate":3,"session_duration":180,"hour_of_day":13,"day_of_week":1,"unique_endpoints":8,"data_volume":200}' | grep -o '"action":"[^"]*"'

echo ""
echo "4️⃣  Testing Honeypot System"
curl -s http://localhost:8000/api/ids/honeypot/test | grep -o '"meters_tested":[0-9]*'

echo ""
echo "✅ All tests completed!"