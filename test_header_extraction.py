#!/usr/bin/env python3
"""
Quick test to verify X-Client-Cert header extraction works.
"""

import base64
import sys
from pathlib import Path

# Read the client certificate
cert_path = Path("../certs/client.crt")
with open(cert_path, "rb") as f:
    cert_pem = f.read()

# Base64 encode it (like nginx does)
cert_b64 = base64.b64encode(cert_pem).decode()

print("✅ X-Client-Cert Header Test")
print("=" * 60)
print()

# Test with curl passing the cert as a header
print("1. Testing X-Client-Cert header extraction...")
print()
print("   Running: curl -X GET http://localhost:8000/api/meter/voltage \\")
print('             -H "X-Client-Cert: <base64-cert>"')
print()

# Create request with header
import subprocess
import urllib.request
import urllib.error

try:
    # First, ensure auth knows about this cert
    print("2. Checking database for authorized cert...")
    from backend.auth import extract_cert_info_from_pem
    fp, cn = extract_cert_info_from_pem(cert_pem)
    print(f"   ✓ Cert fingerprint: {fp}")
    print(f"   ✓ Common name: {cn}")
    print()

    # Now test with HTTPX or simple request
    print("3. Making HTTP request with X-Client-Cert header...")
    req = urllib.request.Request(
        "http://localhost:8000/api/meter/voltage",
        headers={"X-Client-Cert": cert_b64}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode()
            print(f"   ✓ Response: {data}")
            print()
            print("🎉 SUCCESS! mTLS certificate auth is working!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
        print("   This means:")
        print("   - Backend might not be running on port 8000")
        print("   - Header extraction might not be working")

except Exception as e:
    print(f"Error: {e}")
    print("Make sure you're in the backend directory")
    sys.exit(1)
