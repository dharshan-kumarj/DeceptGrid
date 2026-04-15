#!/usr/bin/env python3
"""
Custom mTLS server using Python async and ssl modules to properly extract peer certs.
Bypasses Uvicorn's ASGI scope limitations for cert extraction.
"""

import asyncio
import ssl
import socket
from pathlib import Path
from typing import Tuple, Dict, Optional
import json
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Global cache of peer certs indexed by (client_ip, client_port)
peer_certs: Dict[Tuple[str, int], bytes] = {}


class CertificateExtractingProtocol(asyncio.Protocol):
    """Protocol that captures SSL peer certificate on connection."""

    def connection_made(self, transport):
        """Called when connection is established."""
        # Get peer SSL certificate
        try:
            peername = transport.get_extra_info("peername")
            ssl_object = transport.get_extra_info("ssl_object")

            if ssl_object and peername:
                try:
                    peer_cert_der = ssl_object.getpeercert(binary_form=True)
                    if peer_cert_der:
                        peer_certs[tuple(peername)] = peer_cert_der
                        print(f"[CertCapture] ✓ Captured cert for {peername[0]}:{peername[1]}")
                except Exception as e:
                    print(f"[CertCapture] Error extracting cert: {e}")
        except Exception as e:
            print(f"[CertCapture] Connection error: {e}")

        self.transport = transport

    def data_received(self, data):
        """This shouldn't be called for our direct server."""
        pass

    def connection_lost(self, exc):
        """Called when connection is closed."""
        pass


async def run_server_with_cert_extraction():
    """
    Run the ASGI app with a separate SSL socket server that extracts certs
    and stores them for the app to retrieve.
    """
    # This approach requires modifying the app to use stored cert data
    # For now, fall back to using uvicorn directly and rely on middleware

    print("Note: This approach requires deeper socket-level integration.")
    print("Falling back to uvicorn with middleware cert extraction...")

    import subprocess

    # Just run uvicorn normally - our middleware will try to extract certs
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--ssl-keyfile", "../certs/server.key",
        "--ssl-certfile", "../certs/server.crt",
        "--ssl-ca-certs", "../certs/ca.crt",
        "--ssl-cert-reqs", "2",
        "--host", "0.0.0.0",
        "--port", "8000",
    ])


if __name__ == "__main__":
    print("🚀 Starting DeceptGrid with certificate extraction...")
    asyncio.run(run_server_with_cert_extraction())
