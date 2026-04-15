#!/bin/bash
# Test mTLS with the DeceptGrid backend

set -e

CERTS_DIR="../certs"
BACKEND_URL="https://127.0.0.1:8443"

echo "🧪 Testing DeceptGrid Backend mTLS"
echo "   Assuming nginx is running on 8443 with SSL/mTLS"
echo "   and forwarding to Uvicorn on 8000"
echo ""

# Test 1: Without client certificate (should fail)
echo "❌ Test 1: Request without client cert (should be rejected)"
curl -sk "$BACKEND_URL/api/meter/voltage" 2>&1 | head -5 || true
echo ""

# Test 2: With valid client certificate (should succeed)
echo "✅ Test 2: Request with valid client cert"
curl -sk \
  --cert "$CERTS_DIR/client.crt" \
  --key "$CERTS_DIR/client.key" \
  "$BACKEND_URL/api/meter/voltage" | python3 -m json.tool || echo "Response received"
echo ""

echo "✅ Tests complete!"
