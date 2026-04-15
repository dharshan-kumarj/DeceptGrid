#!/usr/bin/env python3
"""Test script that extracts client cert and sends it as X-Client-Cert header."""

import urllib.parse
import subprocess
import os

# Read the client certificate
with open("certs/client.crt", "r") as f:
    cert_pem = f.read()

# URL-encode the PEM (nginx does this automatically)
cert_encoded = urllib.parse.quote(cert_pem)

# Make the request
cmd = [
    "curl",
    "-s",
    "--cert", "certs/client.crt",
    "--key", "certs/client.key",
    "--cacert", "certs/ca.crt",
    "-H", f"X-Client-Cert: {cert_encoded}",
    "https://localhost:8000/api/meter/voltage"
]

print("Running:", " ".join(cmd[:6]) + " -H 'X-Client-Cert: <encoded>' " + cmd[-1])
print()
result = subprocess.run(cmd, capture_output=False)
print()
print("Return code:", result.returncode)
