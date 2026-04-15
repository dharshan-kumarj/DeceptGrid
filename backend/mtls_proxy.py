#!/usr/bin/env python3
"""
Simple mTLS-terminating proxy using only asyncio and ssl.
Extracts client certificates and forwards them as X-Client-Cert headers.
"""

import asyncio
import ssl
from pathlib import Path
from urllib.parse import quote
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MTLSProxy:
    """mTLS proxy that terminates SSL and forwards requests to backend."""

    def __init__(self, backend_host="127.0.0.1", backend_port=8000, listen_port=8443):
        self.backend_host = backend_host
        self.backend_port = backend_port
        self.listen_port = listen_port
        self.certs_dir = Path(__file__).parent.parent / "certs"

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming mTLS connection."""
        try:
            peername = writer.get_extra_info("peername")
            ssl_object = writer.get_extra_info("ssl_object")

            cert_header = None
            if ssl_object:
                try:
                    peer_cert_der = ssl_object.getpeercert(binary_form=True)
                    if peer_cert_der:
                        from cryptography.hazmat.primitives import serialization
                        from cryptography import x509
                        cert = x509.load_der_x509_certificate(peer_cert_der)
                        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
                        print(f"[MTLSProxy] ✓ Extracted cert for {peername}")
                        cert_header = quote(cert_pem)
                except Exception as e:
                    logger.error(f"Error extracting cert: {e}")

            # Read the HTTP request from client
            request_data = await reader.read(4096)
            if not request_data:
                writer.close()
                return

            # Parse request to get HTTP method, path, and headers
            request_str = request_data.decode('utf-8', errors='ignore')
            request_lines = request_str.split('\r\n')
            if not request_lines:
                writer.close()
                return

            # Extract request line
            request_line = request_lines[0]  # GET /path HTTP/1.1
            print(f"[MTLSProxy] Request: {request_line}")

            # Extract headers and inject X-Client-Cert
            headers = []
            for line in request_lines[1:]:
                if line == '':
                    break
                headers.append(line)

            # Inject the certificate header
            if cert_header:
                headers.insert(0, f"X-Client-Cert: {cert_header}")
                print(f"[MTLSProxy] Injected X-Client-Cert header")

            # Forward to backend
            backend_reader, backend_writer = await asyncio.open_connection(
                self.backend_host, self.backend_port
            )

            # Reconstruct and send request to backend
            forwarded_request = request_line + '\r\n'
            for header in headers:
                if header.strip():
                    forwarded_request += header + '\r\n'
            forwarded_request += '\r\n'

            backend_writer.write(forwarded_request.encode())
            # Read any body data if present
            # For GET requests, there usually isn't one
            await backend_writer.drain()

            # Read response from backend
            response_data = await backend_reader.read(4096)
            backend_writer.close()

            # Send response back to client
            writer.write(response_data)
            await writer.drain()
            writer.close()

        except Exception as e:
            logger.error(f"Connection error: {e}")
            writer.close()

    async def start(self):
        """Start the mTLS proxy server."""
        # Create SSL context for incoming connections (mTLS server)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(
            certfile=str(self.certs_dir / "server.crt"),
            keyfile=str(self.certs_dir / "server.key"),
        )
        ssl_context.load_verify_locations(str(self.certs_dir / "ca.crt"))
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = False

        server = await asyncio.start_server(
            self.handle_connection,
            "0.0.0.0",
            self.listen_port,
            ssl=ssl_context
        )

        print(f"✅ mTLS Proxy listening on https://0.0.0.0:{self.listen_port}")
        print(f"   Backend: http://{self.backend_host}:{self.backend_port}")
        print(f"   Certs: {self.certs_dir}")

        async with server:
            await server.serve_forever()


async def main():
    proxy = MTLSProxy()
    await proxy.start()


if __name__ == "__main__":
    print("🚀 Starting simple mTLS proxy...")
    asyncio.run(main())
