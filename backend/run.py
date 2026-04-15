#!/usr/bin/env python3
"""
DeceptGrid Backend Launcher - HTTP mode for use behind SSL proxy (like nginx).

For local testing with mTLS:
  1. Run this script: python run.py
  2. In another terminal: ./test_mtls.sh

For production:
  - Run this on port 8000
  - Place nginx (or similar) on port 8443 for SSL/mTLS
  - nginx forwards X-Client-Cert header to this app

The auth.py module extracts client certs from X-Client-Cert header.
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Run Uvicorn in HTTP mode (no SSL) on port 8000
    # SSL will be handled by nginx or run_with_nginx.sh
    print("🚀 Starting DeceptGrid Backend (HTTP mode)...")
    print("   ✓ For local mTLS testing, run nginx separately with:" )
    print("     nginx -c $(pwd)/nginx.conf")
    print()

    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",  # Auto-reload on code changes
    ])
